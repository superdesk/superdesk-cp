
import re
import cp
import json
import superdesk

from typing import List
from flask import current_app as app
from superdesk.io.feed_parsers import APMediaFeedParser


AP_SOURCE = 'The Associated Press'
AP_SUBJECT_SCHEME = 'http://cv.ap.org/id/'

FR_CATEGORY_MAPPING = [
    ('Culture', 'a'),
    ('International', 'i', 'n'),
    ('Nouvelles Générales', 'g'),
    ('Sports', 's'),
]

EN_CATEGORY_MAPPING = [
    ('International', 'a', 'b', 'i', 'k', 'n', 'w'),
    ('Lifestyle', 'd', 'l'),
    ('Entertainment', 'e', 'c'),
    ('Business', 'f'),
    ('Politics', 'p'),
    ('Sports', 'q', 's', 'z'),
    ('Travel', 't'),
    ('Advisories', 'v'),
]

AP_SUBJECT_CODES = set([
    'c8e409f8858510048872ff2260dd383e',
    '5b4319707dd310048b23df092526b43e',
    '8783d248894710048286ba0a2b2ca13e',
    'f25af2d07e4e100484f5df092526b43e',
    '86aad5207dac100488ecba7fa5283c3e',
    'cc7a76087e4e10048482df092526b43e',
    '3e37e4b87df7100483d5df092526b43e',
    '44811870882f10048079ae2ac3a6923e',
    '4bf76cb87df7100483dbdf092526b43e',
    '75a42fd87df7100483eedf092526b43e',
    '54df6c687df7100483dedf092526b43e',
    '455ef2b87df7100483d8df092526b43e',
])


def _get_cv_items(_id: str) -> List:
    cv = superdesk.get_resource_service('vocabularies').find_one(req=None, _id=_id)
    return cv['items']


class CP_APMediaFeedParser(APMediaFeedParser):
    """
    Metadata: https://developer.ap.org/ap-media-api/agent/AP_Classification_Metadata.htm
    """

    PROFILE_ID = 'Story'
    RELATED_ID = 'media-gallery'

    # use preview for all now
    RENDITIONS_MAPPING = {
        'baseImage': 'preview',
        'viewImage': 'preview',
        'thumbnail': 'thumbnail',
    }

    def process_slugline(self, slugline):
        return re.sub(r'--+', '-', re.sub(r'[ !"#$%&()*+,./:;<=>?@[\]^_`{|}~\\]', '-', slugline))

    def process_headline(self, headline):
        return headline \
            .replace('APNewsBreak: ', '') \
            .replace('—', ' - ') \
            .replace('_', ' - ')

    def parse(self, data, provider=None):
        """
        Applying custom CP mapping based on _APWebFeed-1.0-JIMI-3.0.xsl
        """
        ap_item = data['data']['item']
        item = super().parse(data, provider=provider)
        item.setdefault('extra', {})

        if app.config.get('AP_INGEST_DEBUG'):
            transref = ap_item['altids']['itemid']
            with open('/tmp/ap/{}.json'.format(transref), 'w') as out:
                json.dump(data['data'], out, indent=2)

        item['guid'] = ap_item['altids']['etag']

        if item.get('slugline'):
            item['slugline'] = self.process_slugline(item['slugline'])

        if item.get('type') == 'text':
            item['profile'] = self.PROFILE_ID

        item['keywords'] = [
            subj['name']
            for subj in ap_item.get('subject', [])
            if subj.get('scheme') == AP_SUBJECT_SCHEME
        ]

        if ap_item.get('subject'):
            item['subject'] = self._parse_subject(ap_item['subject'])

        if item.get('headline'):
            item['headline'] = self.process_headline(item['headline'])
            item['extra'][cp.HEADLINE2] = item['headline']

        if item.get('byline'):
            item['byline'] = ','.join(filter(None, [
                capitalize(re.sub(
                    r' \([^)]+?\)',
                    '',
                    byline.replace('The Associated Press', '').replace('--Par', ''),
                )) for byline in item['byline'].split(',')
            ]))

        try:
            dateline = ap_item['datelinelocation']
        except KeyError:
            pass
        else:
            try:
                source = ap_item['infosource'][0]['name']
            except (KeyError, IndexError):
                source = item.get('source')
            item['dateline'] = {
                'text': ap_item.get('located', ''),
                'source': source,
                'located': {
                    'alt_name': '',
                    'city': dateline.get('city', ''),
                    'city_code': dateline.get('city', ''),
                    'state': dateline.get('countryareaname', ''),
                    'state_code': dateline.get('countryareacode', ''),
                    'country': dateline.get('countryname', ''),
                    'country_code': dateline.get('countrycode', ''),
                    'dateline': 'city',
                }
            }

            try:
                lon, lat = dateline['geometry_geojson']['coordinates']
                item['dateline']['located']['location'] = {'lat': lat, 'lon': lon}
            except KeyError:
                pass

        if ap_item.get('description_summary'):
            item['abstract'] = ap_item['description_summary']

        if ap_item.get('ednote'):
            ednote = self._parse_ednote(ap_item['ednote'])
            item['ednote'] = self._format_ednote(ednote)
            item['extra']['update'] = self._format_update(ednote)

        item['source'] = AP_SOURCE
        item['urgency'] = self._parse_ranking(data['data'], item)

        if item['type'] == 'text':
            self._parse_genre(data['data'], item)
            self._parse_category(data['data'], item)

        if ap_item.get('organisation'):
            item['extra']['stocks'] = self._parse_stocks(ap_item['organisation'])

        if ap_item.get('embargoed'):
            item['embargoed'] = self.datetime(ap_item['embargoed'])

        return item

    def _parse_stocks(self, organisations):
        return ','.join([
            org['symbols'][0]['instrument']
            for org in organisations
            if org.get('symbols')
        ])

    def _get_subject(self, data):
        return data['item'].get('subject', [])

    def get_anpa_categories(self, data):
        return [subj['code'] for subj in self._get_subject(data) if 'category' in subj.get('rels', [])]

    def get_ap_subjects(self, data):
        return [subj['code'] for subj in self._get_subject(data) if subj.get('scheme') == AP_SUBJECT_SCHEME]

    def get_products(self, data):
        try:
            return [product['id'] for product in data['meta']['products']]
        except KeyError:
            return []

    def _parse_ranking(self, data, item):
        slugline = item.get('slugline') or ''
        content_type = data['item']['profile'].lower() if data['item'].get('profile') else 'unknown'
        priority = data['item']['editorialpriority'].lower() if data['item'].get('editorialpriority') else ''

        if 'fr' in item['language']:
            if re.search(r'^(insolite)', slugline, re.IGNORECASE):
                return cp.NEWS_BUZZ
            elif priority in ['f', 'b']:
                return cp.NEWS_URGENT
            elif priority == 'u':
                return cp.NEWS_NEED_TO_KNOW
            elif priority == 'r':
                return cp.NEWS_GOOD_TO_KNOW
            else:
                return cp.NEWS_OPTIONAL

        products = self.get_products(data)
        categories = self.get_anpa_categories(data)
        ap_subject = self.get_ap_subjects(data)

        if 32607 in products and 's' in categories and re.search(
            r'(CYC|FIG|OLY|SKI|TEN)-',
            slugline,
            re.IGNORECASE,
        ):
            return cp.NEWS_GOOD_TO_KNOW

        if 30599 in products and 's' in categories and re.search(
            r'(CAR|BBA|BBN|BKN|FBN|GLF|HKN|LAC|OLY|RAC|MMA)-',
            slugline,
            re.IGNORECASE,
        ):
            return cp.NEWS_GOOD_TO_KNOW

        if 32607 in products and 's' in categories and re.search(
            r'(ARC|ATH|BAD|BIA|BOB|CAN|CRI|XXC|CUR|DIV|EQU|FEN|FHK|FRE|GYM|HNB|JUD|LUG|PEN|MOT|NOR|ROW|RGL|RGU|SAI|SHO|SKE|JUM|SBD|SOC|SOF|SPD|SQA|SUM|SWM|TTN|TAE|TRI|VOL|WPO|WEI|WRE)-',  # noqa
            slugline,
            re.IGNORECASE,
        ):
            return cp.NEWS_OPTIONAL

        if 30599 in products and 's' in categories and re.search(
            r'(BBC|BBH|BBI|BBM|BBW|BBY|BKC|BKH|BKO|BKW|BKL|BOX|FBC|FBH|FBO|HKC|HKO|HKW)-',
            slugline,
            re.IGNORECASE,
        ):
            return cp.NEWS_OPTIONAL

        if re.search(
            r'today-in-history',
            slugline,
            re.IGNORECASE,
        ):
            return cp.NEWS_ROUTINE

        if (re.search(r'(odd|people)', slugline, re.IGNORECASE) and 'spot' in content_type) or re.search(
            r'ap\s+impact',
            content_type,
            re.IGNORECASE,
        ):
            return cp.NEWS_BUZZ

        if 'spot' in content_type and 'r' == priority and '5b4319707dd310048b23df092526b43e' in ap_subject:
            return cp.NEWS_BUZZ

        if 'game' in content_type and '5b4319707dd310048b23df092526b43e' in ap_subject:
            return cp.NEWS_GOOD_TO_KNOW

        if 'obituary' in content_type and priority == 'u':
            return cp.NEWS_URGENT

        if re.search(r'(spot|game|topstory|headlinepackage)', content_type) and 'u' == priority:
            return cp.NEWS_NEED_TO_KNOW

        if re.search(r'(spot|obituary|game|topstory|headlinepackage)', content_type) and 'r' == priority:
            return cp.NEWS_GOOD_TO_KNOW

        if 'enterprise' in content_type and '54df6c687df7100483dedf092526b43e' in ap_subject:
            return cp.NEWS_FEATURE_PREMIUM

        if 'enterprise' in content_type:
            return cp.NEWS_FEATURE_REGULAR

        if 'review' in content_type and re.search(r'us-film-review', slugline, re.IGNORECASE):
            return cp.NEWS_FEATURE_REGULAR

        if re.search(r'(column|profile|review)', content_type):
            return cp.NEWS_FEATURE_PREMIUM

        if re.search(r'(Alaska-Digest-News|Washington-Digest|AP-Newsfeatures-Digest)', content_type, re.IGNORECASE):
            return cp.NEWS_ROUTINE

        if re.search(r'(advisory|daybook)', content_type, re.IGNORECASE):
            return cp.NEWS_ROUTINE

        return cp.NEWS_OPTIONAL

    def _parse_ednote(self, ednote):
        return re.sub(
            r'eds:\s*',
            '',
            ednote,
            flags=re.IGNORECASE,
        )

    def _format_ednote(self, ednote):
        matches = [
            re.search(r'APNewsNow[;.]?', ednote, re.IGNORECASE),
            re.search(r'Moving on.*\.', ednote),
        ]
        return ' '.join([m.group() for m in matches if m])

    def _format_update(self, ednote):
        return re.sub(
            r'NDLR\:',
            '',
            re.sub(r'\s*Moving on.*\.', '', ednote),
        )

    def _parse_subject(self, subject):
        CV_ID = 'subject_custom'
        parsed = []
        available = _get_cv_items(CV_ID)
        for subj in available:
            if subj.get('ap_subject'):
                codes = [code.strip() for code in subj['ap_subject'].split(',')]
                for ap_subj in subject:
                    if any([code for code in codes if ap_subj['code'].startswith(code)]):
                        parsed.append({
                            'name': subj['name'],
                            'qcode': subj['qcode'],
                            'scheme': CV_ID,
                            'translations': subj['translations'],
                        })
        return parsed

    def _map_category_codes(self, item):
        categories = _get_cv_items('categories')
        codes = [cat['qcode'] for cat in item['anpa_category']]
        item['anpa_category'] = [
            {
                'name': cat['name'],
                'qcode': cat['qcode'],
            } for cat in categories if cat.get('qcode') in codes
        ]

    def _parse_index_code(self, data, item):
        if not item.get('language') or not item.get('slugline'):
            return

        categories = self.get_anpa_categories(data)

        def get_index(mapping):
            for index, *cats in mapping:
                if any([c in categories for c in cats]):
                    return index

        if 'fr' in item['language']:
            index = get_index(FR_CATEGORY_MAPPING)
            if index:
                return index
            return 'Spare News'

        slugline = item['slugline']
        products = self.get_products(data)
        textformat = data['item'].get('textformat', '')

        if re.search(r'-MED-', slugline):
            return 'Lifestyle'

        if 't' in textformat or 31385 in products:
            return 'Agate'

        if re.search(r'''
            (ARC	(?# Match for Archery)
            |ATH	(?# Match for Athletics)
            |BAD	(?# Match for Badminton)
            |BBA	(?# Match for Baseball American League)
            |BBC	(?# Match for Baseball U.S. College)
            |BBH	(?# Match for Baseball High School)
            |BBI	(?# Match for Baseball International)
            |BBM	(?# Match for Baseball Minor Leagues)
            |BBN	(?# Match for Baseball National League)
            |BBO	(?# Match for Baseball Other)
            |BBW	(?# Match for Baseball Women)
            |BBY	(?# Match for Baseball Youth)
            |BIA	(?# Match for Biathalon)
            |BKC	(?# Match for Basketball U.S. College)
            |BKH	(?# Match for Basketball High School)
            |BKL	(?# Match for Basketball Womens Pro)
            |BKN	(?# Match for Basketball NBA)
            |BKO	(?# Match for Basketball Other)
            |BKW	(?# Match for Basketball Womens College)
            |BOB	(?# Match for Bobsled)
            |BOX	(?# Match for Boxing)
            |CAN	(?# Match for Canoeing)
            |CAR	(?# Match for Auto Racing)
            |COM	(?# Match for Commonwealth Games)
            |CRI	(?# Match for Cricket)
            |CUR	(?# Match for Curling)
            |CYC	(?# Match for Cycling)
            |DIV	(?# Match for Diving)
            |EQU	(?# Match for Equestrian)
            |FBC	(?# Match for Football U.S. College)
            |FBH	(?# Match for Football High School)
            |FBN	(?# Match for Football NFL)
            |FBO	(?# Match for Football Other)
            |FEN	(?# Match for Fencing)
            |FHK	(?# Match for Field Hockey)
            |FIG	(?# Match for Figure Skating)
            |FRE	(?# Match for Freestyle skiing)
            |GLF	(?# Match for Golf)
            |GYM	(?# Match for Gymnastics)
            |HKC	(?# Match for Hockey U.S. College)
            |HKN	(?# Match for Hockey NHL)
            |HKO	(?# Match for Hockey Other)
            |HKW	(?# Match for Hockey Women)
            |HNB	(?# Match for Handball)
            |JUD	(?# Match for Judo)
            |JUM	(?# Match for Ski jumping)
            |LUG	(?# Match for Luge)
            |MMA	(?# Match for Mixed martial arts)
            |MOT	(?# Match for Motorcycling)
            |NOR	(?# Match for Nordic Combined)
            |OLY	(?# Match for Olympics)
            |PEN	(?# Match for Modern Pentathlon)
            |RAC	(?# Match for Horseracing)
            |RGL	(?# Match for RugbyLeague)
            |RGU	(?# Match for RugbyUnion)
            |ROW	(?# Match for Rowing)
            |SAI	(?# Match for Sailing)
            |SBD	(?# Match for Snowboarding)
            |SHO	(?# Match for Short track)
            |SKE	(?# Match for Skeleton)
            |SKI	(?# Match for Skiing - Alpine)
            |SOC	(?# Match for Soccer)
            |SOF	(?# Match for Softball)
            |SPD	(?# Match for Speedskating long track)
            |SQA	(?# Match for Squash)
            |SUM	(?# Match for Sumo Wrestling)
            |SWM	(?# Match for Swimming)
            |TAE	(?# Match for Taekwondo)
            |TEN	(?# Match for Tennis)
            |TRI	(?# Match for Triathlon)
            |TTN	(?# Match for Table tennis)
            |VOL	(?# Match for Volleyball)
            |WEI	(?# Match for Weightlifting)
            |WPO	(?# Match for WaterPolo)
            |WRE	(?# Match for Wrestling)
            |XXC	(?# Match for Cross-country skiing)
            )
            .*
            (Box		(?# Match for Box)
            |Calendar	(?# Match for Calendar)
            |Comparison	(?# Match for Comparison)
            |Date		(?# Match for Date)
            |Digest		(?# Match for Digest)
            |Fared		(?# Match for Fared)
            |Glance		(?# Match for Glance)
            |Leaders	(?# Match for Leaders)
            |Poll		(?# Match for Poll)
            |Results?	(?# Match for Results)
            |Linescores	(?# Match for Linescores)
            |Schedule	(?# Match for Schedule)
            |Scores?	(?# Match for Score)
            |Scorers	(?# Match for Scorers)
            |Scoreboard	(?# Match for Scoreboard)
            |Standings	(?# Match for Standings)
            |Stax		(?# Match for Stax)
            |Streaks?    (?# Match for baseball streak files)
            |Sums?		(?# Match for Sum)
            |Summaries	(?# Match for Summaries)
            |Glantz-Culver-Line	(?# Match for Glantz-Culver-Line)
            )
        ''', slugline, re.IGNORECASE | re.VERBOSE):
            return 'Agate'

        index = get_index(EN_CATEGORY_MAPPING)
        if index:
            return index

        if re.search(r'Washington-Digest|AP-Newsfeatures-Digest', slugline):
            return 'Prairies/BC'

        if re.search(r'AP-Newsfeatures-Digest', slugline):
            return 'International'

        return 'Spare News'

    def _parse_genre(self, data, item):
        """VersionType in JIMI"""
        slugline = item.get('slugline') or ''
        if re.search(r'NewsAlert', slugline, re.IGNORECASE):
            genre = 'NewsAlert'
        elif re.search(r'Correction:', item['headline'], re.IGNORECASE):
            genre = 'Corrective'
        elif 'canceled' == data['item']['pubstatus']:
            genre = 'Kill'
        elif 'withheld' == data['item']['pubstatus']:
            genre = 'Withhold'
        elif 'embargoed' == data['item']['pubstatus']:
            genre = 'Embargoed'
        else:
            genre = data['item'].get('profile')

        if genre:
            item['genre'] = [{
                'name': genre,
                'qcode': genre,
            }]

    def _parse_category(self, data, item):
        """Index in JIMI"""
        index_names = set()
        index = self._parse_index_code(data, item)
        if index:
            index_names.add(index)

        for subj in self._get_subject(data):
            if subj.get('code') in AP_SUBJECT_CODES:
                index_names.add(subj['name'])

        if index_names:
            categories = _get_cv_items('categories')
            item['anpa_category'] = []
            for cat in categories:
                if cat.get('name') in index_names:
                    item['anpa_category'].append(
                        {'name': cat['name'], 'qcode': cat['qcode']},
                    )


def capitalize(name):
    return ' '.join([n.capitalize() for n in name.split(' ')])
