
from superdesk.metadata.item import SCHEDULE_SETTINGS
import cp
import arrow
import superdesk
import lxml.etree as etree
import cp.ingest.parser.globenewswire as globenewswire

from collections import OrderedDict
from superdesk.utc import utc_to_local
from superdesk.text_utils import get_text, get_word_count
from superdesk.publish.formatters import Formatter
from superdesk.media.renditions import get_rendition_file_name
from apps.publish.enqueue import get_enqueue_service

from cp.utils import format_maxlength


DEFAULT_DATETIME = '0001-01-01T00:00:00'

DATELINE_MAPPING = OrderedDict((
    ('city', 'City'),
    ('state', 'Province'),
    ('country', 'Country'),
))

OUTPUT_LENGTH_LIMIT = 128

PICTURE_TYPES = {
    'picture',
    'graphic',
}

PICTURE_CATEGORY_MAPPING = {
    cp.PHOTO_CATEGORIES: 'Category',
    cp.PHOTO_SUPPCATEGORIES: 'SupplementalCategories',
}


class JimiFormatter(Formatter):

    ENCODING = 'utf-8'

    def can_format(self, format_type, article):
        return format_type == 'jimi'

    def format(self, article, subscriber, codes=None):
        output = []
        services = [s.get('name') for s in article.get('subject') or [] if s.get('scheme') == cp.SERVICE]
        if not services:
            services.append(None)
        for service in services:
            pub_seq_num = superdesk.get_resource_service('subscribers').generate_sequence_number(subscriber)
            root = etree.Element('Publish')
            self._format_item(root, article, pub_seq_num, service, services)
            xml = etree.tostring(root, pretty_print=True, encoding=self.ENCODING, xml_declaration=True)
            output.append((pub_seq_num, xml.decode(self.ENCODING)))
        return output

    def _format_subject_code(self, root, item, elem, scheme):
        subject = item.get('subject') or []
        for subj in subject:
            if subj.get('scheme') == scheme and subj.get('qcode'):
                etree.SubElement(root, elem).text = subj['qcode']

    def _format_item(self, root, item, pub_seq_num, service, services):
        content = etree.SubElement(root, 'ContentItem')
        extra = item.get('extra') or {}

        # root system fields
        etree.SubElement(root, 'Reschedule').text = 'false'
        etree.SubElement(root, 'IsRegional').text = 'false'
        etree.SubElement(root, 'CanAutoRoute').text = 'true'
        etree.SubElement(root, 'PublishID').text = str(pub_seq_num)
        etree.SubElement(root, 'Username')
        etree.SubElement(root, 'UseLocalsOut').text = 'false'

        if item.get('type') in PICTURE_TYPES:
            etree.SubElement(root, 'Services').text = 'Pictures'
            self._format_subject_code(root, item, 'PscCodes', 'destinations')
            if root.find('PscCodes') is None:
                etree.SubElement(root, 'PscCodes').text = 'Online'
        elif service:
            etree.SubElement(root, 'Services').text = 'Print'
            etree.SubElement(root, 'PscCodes').text = service
        else:
            self._format_subject_code(root, item, 'Services', 'distribution')
            self._format_subject_code(root, item, 'PscCodes', 'destinations')

        # content system fields
        etree.SubElement(content, 'Name')
        etree.SubElement(content, 'Cachable').text = 'false'
        etree.SubElement(content, 'FileName').text = str(extra.get(cp.FILENAME) or item['guid'])
        etree.SubElement(content, 'NewsCompID').text = '{:08d}'.format(pub_seq_num % 100000000)
        etree.SubElement(content, 'SystemSlug').text = str(extra.get(cp.ORIG_ID) or item['guid'])

        if service:
            etree.SubElement(content, 'Note').text = ','.join(services)

        # timestamps
        firstpublished = item.get('firstpublished') or item['versioncreated']
        etree.SubElement(root, 'PublishDateTime').text = self._format_datetime(firstpublished)
        try:
            etree.SubElement(content, 'EmbargoTime').text = self._format_datetime(
                item[SCHEDULE_SETTINGS]['utc_embargo'],
                local=True,
            )
        except KeyError:
            etree.SubElement(content, 'EmbargoTime').text = self._format_datetime(item.get('embargoed'), local=True)
        etree.SubElement(content, 'CreatedDateTime').text = self._format_datetime(item['firstcreated'])
        etree.SubElement(content, 'UpdatedDateTime').text = self._format_datetime(item['versioncreated'], True)

        # obvious
        etree.SubElement(content, 'ContentType').text = 'Photo' if item['type'] in PICTURE_TYPES else \
            item['type'].capitalize()
        etree.SubElement(content, 'Headline').text = format_maxlength(item.get('headline'), OUTPUT_LENGTH_LIMIT)
        etree.SubElement(content, 'Headline2').text = format_maxlength(extra.get(cp.HEADLINE2) or item.get('headline'),
                                                                       OUTPUT_LENGTH_LIMIT)
        etree.SubElement(content, 'SlugProper').text = item.get('slugline')
        etree.SubElement(content, 'Credit').text = self._format_credit(item)
        etree.SubElement(content, 'Source').text = item.get('source')

        etree.SubElement(content, 'DirectoryText').text = self._format_text(item.get('abstract'))
        etree.SubElement(content, 'ContentText').text = self._format_html(item.get('body_html'))
        etree.SubElement(content, 'Language').text = '2' if 'fr' in item.get('language') else '1'

        if item['type'] == 'text' and item.get('body_html'):
            content.find('DirectoryText').text = format_maxlength(
                get_text(item['body_html'], 'html', lf_on_block=False).replace('\n', ' '),
                200)
            word_count = str(
                item['word_count'] if item.get('word_count') else get_word_count(item['body_html'])
            )
            etree.SubElement(content, 'Length').text = word_count
            etree.SubElement(content, 'WordCount').text = word_count
            etree.SubElement(content, 'BreakWordCount').text = word_count

        if item.get('keywords') and item.get('source') == globenewswire.SOURCE:
            etree.SubElement(content, 'Stocks').text = ','.join(item['keywords'])

        self._format_index(content, item)
        self._format_category(content, item)
        self._format_genre(content, item)
        self._format_urgency(content, item.get('urgency'))
        self._format_keyword(content, item.get('keywords'), ', ' if item.get('type') == 'picture' else ',')
        self._format_dateline(content, item.get('dateline'))
        self._format_writethru(content, item.get('rewrite_sequence'))

        if item.get('byline'):
            etree.SubElement(content, 'Byline').text = item['byline']

        if item.get('type') in PICTURE_TYPES:
            self._format_picture_metadata(content, item)
        else:
            etree.SubElement(content, 'EditorNote').text = item.get('ednote')
            if extra.get('update'):
                etree.SubElement(content, 'UpdateNote').text = extra['update']

        if item.get('associations'):
            self._format_associations(content, item)

    def _format_credit(self, item):
        credit = item.get('creditline')
        if credit == 'ASSOCIATED PRESS' or item.get('original_source') == 'AP':
            return 'THE ASSOCIATED PRESS'
        elif not credit and item.get('source') == 'CP':
            return 'THE CANADIAN PRESS'
        return credit or ''

    def _format_urgency(self, content, urgency):
        if urgency is None:
            urgency = 3
        etree.SubElement(content, 'RankingValue').text = str(urgency)
        cv = superdesk.get_resource_service('vocabularies').find_one(req=None, _id='urgency')
        items = [item for item in cv['items'] if str(item.get('qcode')) == str(urgency)]
        if items:
            etree.SubElement(content, 'Ranking').text = items[0]['name']

    def _format_keyword(self, content, keywords, glue):
        if keywords:
            etree.SubElement(content, 'Keyword').text = format_maxlength(glue.join(keywords), 150)

    def _format_writethru(self, content, num):
        etree.SubElement(content, 'WritethruValue').text = str(num or 0)

        if not num:
            return

        endings = {
            1: 'st',
            2: 'nd',
            3: 'rd',
        }

        test_num = num % 100

        if 4 <= test_num <= 20:
            ending = 'th'
        else:
            ending = endings.get(test_num % 10, 'th')

        etree.SubElement(content, 'WritethruNum').text = '{}{}'.format(num, ending)
        etree.SubElement(content, 'WriteThruType').text = 'Writethru'

    def _format_datetime(self, datetime, rel=False, local=False):
        if not datetime:
            return DEFAULT_DATETIME
        datetime = to_datetime(datetime)
        if rel or local:
            datetime = utc_to_local(cp.TZ, datetime)
        if rel:
            formatted = datetime.strftime('%Y-%m-%dT%H:%M:%S%z')
            return formatted[:-2] + ':' + formatted[-2:]  # add : to timezone offset
        return datetime.strftime('%Y-%m-%dT%H:%M:%S')

    def _format_text(self, value):
        return get_text(value or '', 'html', True).strip()

    def _format_html(self, value):
        return value or ''

    def _format_dateline(self, content, dateline):
        if dateline and dateline.get('located'):
            pieces = []
            located = dateline['located']
            for src, dest in DATELINE_MAPPING.items():
                etree.SubElement(content, dest).text = located.get(src)
                pieces.append(located.get(src) or '')
            etree.SubElement(content, 'Placeline').text = ';'.join(pieces)
            try:
                etree.SubElement(content, 'Latitude').text = str(located['location']['lat'])
                etree.SubElement(content, 'Longitude').text = str(located['location']['lon'])
            except KeyError:
                pass
        else:
            etree.SubElement(content, 'Placeline')

    def _format_index(self, content, item):
        SUBJECTS_ID = 'subject_custom'
        cv = superdesk.get_resource_service('vocabularies').find_one(req=None, _id=SUBJECTS_ID)

        codes = [
            s['qcode'] for s in item.get('subject', [])
            if s.get('name') and s.get('scheme') in (None, SUBJECTS_ID)
        ]

        names = self._resolve_names(codes, cv, item.get('language'))

        if names:
            etree.SubElement(content, 'IndexCode').text = ','.join(names)
        else:
            etree.SubElement(content, 'IndexCode')

    def _resolve_names(self, codes, cv, language):
        names = []
        for code in codes:
            item = _find_jimi_item(code, cv['items'])
            if item:
                name = _get_name(item, language)
                if name not in names:
                    names.append(name)
        return names

    def _format_category(self, content, item):
        try:
            etree.SubElement(content, 'Category').text = ','.join([cat['name'] for cat in item['anpa_category']])
        except (KeyError):
            pass

    def _format_genre(self, content, item):
        version_type = etree.SubElement(content, 'VersionType')
        if item.get('genre'):
            version_type.text = item['genre'][0]['name']

    def _format_picture_metadata(self, content, item):
        extra = item.get('extra') or {}
        etree.SubElement(content, 'HeadlineService').text = 'false'
        etree.SubElement(content, 'VideoType').text = 'None'
        etree.SubElement(content, 'PhotoType').text = 'None'
        etree.SubElement(content, 'GraphicType').text = 'None'

        etree.SubElement(content, 'DateTaken').text = self._format_datetime(item.get('firstcreated'))

        for scheme, elem in PICTURE_CATEGORY_MAPPING.items():
            code = [subj['qcode'] for subj in item.get('subject', []) if subj.get('scheme') == scheme]
            if code:
                dest = content.find(elem) if content.find(elem) is not None \
                    else etree.SubElement(content, elem)
                dest.text = code[0]

        pic_filename = self._format_picture_filename(item)
        if pic_filename:
            content.find('FileName').text = pic_filename
            etree.SubElement(content, 'ContentRef').text = pic_filename
            etree.SubElement(content, 'ViewFile').text = pic_filename

        if item.get('headline'):
            content.find('SlugProper').text = item['headline']

        if item.get('original_source'):
            content.find('Source').text = item['original_source']

        if extra.get(cp.ARCHIVE_SOURCE):
            etree.SubElement(content, 'ArchiveSources').text = extra[cp.ARCHIVE_SOURCE]

        if extra.get(cp.FILENAME):
            etree.SubElement(content, 'OrigTransRef').text = extra[cp.FILENAME]

        if extra.get(cp.PHOTOGRAPHER_CODE):
            etree.SubElement(content, 'BylineTitle').text = extra[cp.PHOTOGRAPHER_CODE].upper()

        if item.get('copyrightnotice'):
            etree.SubElement(content, 'Copyright').text = item['copyrightnotice'][:50]

        if item.get('description_text'):
            etree.SubElement(content, 'EnglishCaption').text = item['description_text'].replace('  ', ' ')

        if extra.get(cp.CAPTION_WRITER):
            etree.SubElement(content, 'CaptionWriter').text = extra[cp.CAPTION_WRITER]

        if item.get('ednote'):
            etree.SubElement(content, 'SpecialInstructions').text = item['ednote']

        if extra.get('itemid'):
            etree.SubElement(content, 'CustomField1').text = extra['itemid']

        if pic_filename:
            etree.SubElement(content, 'CustomField2').text = '/'.join(pic_filename.split('_', 1))

        if extra.get(cp.INFOSOURCE):
            etree.SubElement(content, 'CustomField6').text = extra[cp.INFOSOURCE]

        if extra.get(cp.XMP_KEYWORDS):
            etree.SubElement(content, 'XmpKeywords').text = extra[cp.XMP_KEYWORDS]

        if extra.get('container'):
            etree.SubElement(content, 'ContainerIDs').text = extra['container']
        else:
            self._format_refs(content, item)

    def _format_refs(self, content, item):
        refs = [
            ref.get('guid')
            for ref in superdesk.get_resource_service('news').get(req=None, lookup={'refs.guid': item['guid']})
        ]

        if refs:
            etree.SubElement(content, 'ContainerIDs').text = ', '.join(refs)

    def _format_picture_filename(self, item):
        try:
            return get_rendition_file_name(item['renditions']['original'])
        except KeyError:
            pass
        if item.get('extra') and item['extra'].get(cp.FILENAME):
            created = to_datetime(item['firstcreated'])
            return '{transref}-{date}_{year}_{time}'.format(
                transref=item['extra'][cp.FILENAME],
                year=created.strftime('%Y'),
                date='{}{}'.format(created.month, created.day),
                time=created.strftime('%H%M%S'),
            )

    def _format_associations(self, content, item):
        """When association is already published we need to resend it again
        with link to text item.
        """
        photos = []
        for assoc in item['associations'].values():
            if assoc:
                published = superdesk.get_resource_service('published').get_last_published_version(assoc['_id'])
                if published and published['pubstatus'] == 'usable' and False:  # disable for the time being
                    published.setdefault('extra', {})['container'] = item['guid']
                    publish_service = get_enqueue_service('publish')
                    subscribers = [
                        subs
                        for subs in publish_service.get_subscribers(published, None)[0]
                        if any([
                            dest['format'] == 'jimi'
                            for dest in subs.get('destinations', [])
                        ])
                    ]
                    publish_service.resend(published, subscribers)
                if assoc.get('type') == 'picture':
                    photos.append(assoc)
        etree.SubElement(content, 'PhotoType').text = get_count_label(len(photos))
        if photos:
            etree.SubElement(content, 'PhotoReference').text = ','.join(filter(None, [
                photo.get('guid')
                for photo
                in photos
            ]))


def get_count_label(count):
    if count == 0:
        return 'None'
    elif count == 1:
        return 'One'
    else:
        return 'Many'


def to_datetime(value):
    if value and isinstance(value, str):
        return arrow.get(value)
    return value


def _find_jimi_item(code, items):
    for item in items:
        if item.get('qcode') == code:
            if item.get('in_jimi'):
                return item
            elif item.get('parent'):
                return _find_jimi_item(item['parent'], items)
            break


def _get_name(item, language):
    lang = language.replace('_', '-')
    if '-CA' not in lang:
        lang = '{}-CA'.format(lang)
    try:
        return item['translations']['name'][lang]
    except (KeyError, ):
        return item['name']
