
import cp
import superdesk
import lxml.etree as etree

from collections import OrderedDict
from superdesk.utc import utc_to_local
from superdesk.text_utils import get_text
from superdesk.publish.formatters import Formatter

import cp.ingest.parser.globenewswire as globenewswire


DEFAULT_DATETIME = '0001-01-01T00:00:00'

DATELINE_MAPPING = OrderedDict((
    ('city', 'City'),
    ('state', 'Province'),
    ('country', 'Country'),
))


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

    def _format_item(self, root, item, pub_seq_num, service, services):
        content = etree.SubElement(root, 'ContentItem')

        # root system fields
        etree.SubElement(root, 'Reschedule').text = 'false'
        etree.SubElement(root, 'IsRegional').text = 'false'
        etree.SubElement(root, 'CanAutoRoute').text = 'true'
        etree.SubElement(root, 'PublishID').text = str(pub_seq_num)
        etree.SubElement(root, 'Services').text = 'Print'
        etree.SubElement(root, 'Username')
        etree.SubElement(root, 'UseLocalsOut').text = 'false'
        etree.SubElement(root, 'PscCodes').text = 'ap---' if not service else service

        # content system fields
        etree.SubElement(content, 'Name')
        etree.SubElement(content, 'Cachable').text = 'false'
        etree.SubElement(content, 'ContentItemID').text = str(item['_id'])
        etree.SubElement(content, 'FileName').text = str(item['family_id'])
        etree.SubElement(content, 'NewsCompID').text = str(item['family_id'])
        etree.SubElement(content, 'SystemSlug').text = str(item['family_id'])

        if service:
            etree.SubElement(content, 'Note').text = ','.join(services)

        # timestamps
        firstpublished = item.get('firstpublished') or item['versioncreated']
        etree.SubElement(root, 'PublishDateTime').text = self._format_datetime(firstpublished)
        etree.SubElement(content, 'EmbargoTime').text = self._format_datetime(item.get('embargoed'))
        etree.SubElement(content, 'CreatedDateTime').text = self._format_datetime(item['firstcreated'])
        etree.SubElement(content, 'UpdatedDateTime').text = self._format_datetime(item['versioncreated'], True)

        # obvious
        word_count = str(item['word_count']) if item.get('word_count') else None
        etree.SubElement(content, 'ContentType').text = item['type'].capitalize()
        etree.SubElement(content, 'Headline').text = item.get('headline')
        etree.SubElement(content, 'SlugProper').text = item.get('slugline')
        etree.SubElement(content, 'Credit').text = item.get('creditline')
        etree.SubElement(content, 'Source').text = item.get('source')
        etree.SubElement(content, 'EditorNote').text = item.get('ednote')
        etree.SubElement(content, 'Length').text = word_count
        etree.SubElement(content, 'WordCount').text = word_count
        etree.SubElement(content, 'BreakWordCount').text = word_count
        etree.SubElement(content, 'DirectoryText').text = self._format_text(item.get('abstract'))
        etree.SubElement(content, 'ContentText').text = self._format_html(item.get('body_html'))
        etree.SubElement(content, 'Language').text = '2' if 'fr' in item.get('language') else '1'

        if item.get('keywords') and item.get('source') == globenewswire.SOURCE:
            etree.SubElement(content, 'Stocks').text = ','.join(item['keywords'])

        # extra
        extra = item.get('extra') or {}

        etree.SubElement(content, 'Headline2').text = extra.get(cp.HEADLINE2) if extra.get(cp.HEADLINE2) \
            else item['headline']

        self._format_index(content, item)
        self._format_category(content, item)
        self._format_genre(content, item)
        self._format_urgency(content, item.get('urgency'))
        self._format_keyword(content, item.get('keywords'))
        self._format_dateline(content, item.get('dateline'))
        self._format_writethru(content, item.get('rewrite_sequence'))

    def _format_urgency(self, content, urgency):
        if urgency is None:
            urgency = 3
        etree.SubElement(content, 'RankingValue').text = str(urgency)
        cv = superdesk.get_resource_service('vocabularies').find_one(req=None, _id='urgency')
        items = [item for item in cv['items'] if str(item.get('qcode')) == str(urgency)]
        if items:
            etree.SubElement(content, 'Ranking').text = items[0]['name']

    def _format_keyword(self, content, keywords):
        if keywords:
            etree.SubElement(content, 'Keyword').text = ','.join(keywords)

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

    def _format_datetime(self, datetime, rel=False):
        if not datetime:
            return DEFAULT_DATETIME
        if rel:
            relative = utc_to_local('America/Toronto', datetime)
            formatted = relative.strftime('%Y-%m-%dT%H:%M:%S%z')
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
                names.append(_get_name(item, language))
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


def _find_jimi_item(code, items):
    for item in items:
        if item.get('qcode') == code:
            if item.get('in_jimi'):
                return item
            elif item.get('parent'):
                return _find_jimi_item(item['parent'], items)
            break


def _get_name(item, language):
    try:
        return item['translations']['name'][language]
    except (KeyError, ):
        return item['name']
