
import superdesk
import lxml.etree as etree

from collections import OrderedDict
from superdesk.utc import utc_to_local
from superdesk.text_utils import get_text
from superdesk.publish.formatters import Formatter


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
        pub_seq_num = superdesk.get_resource_service('subscribers').generate_sequence_number(subscriber)
        root = etree.Element('Publish')
        self._format_item(root, article)
        xml = etree.tostring(root, pretty_print=True, encoding=self.ENCODING, xml_declaration=True)
        return [(pub_seq_num, xml.decode(self.ENCODING))]

    def _format_item(self, root, item):
        content = etree.SubElement(root, 'ContentItem')

        # root system fields
        etree.SubElement(root, 'Reschedule').text = 'false'
        etree.SubElement(root, 'IsRegional').text = 'false'
        etree.SubElement(root, 'CanAutoRoute').text = 'true'
        etree.SubElement(root, 'PublishID').text = '1'
        etree.SubElement(root, 'Services').text = 'Print'
        etree.SubElement(root, 'Username')
        etree.SubElement(root, 'UseLocalsOut').text = 'false'
        etree.SubElement(root, 'PscCodes').text = 'ap---'

        # content system fields
        etree.SubElement(content, 'Name')
        etree.SubElement(content, 'Cachable').text = 'false'
        etree.SubElement(content, 'NewsCompID').text = item['_id']

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

        self._format_keyword(content, item.get('keywords'))
        self._format_dateline(content, item.get('dateline'))
        self._format_writethru(content, item.get('rewrite_sequence'))

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
        else:
            etree.SubElement(content, 'Placeline')
