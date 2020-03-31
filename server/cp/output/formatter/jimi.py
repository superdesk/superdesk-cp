
import superdesk
import lxml.etree as etree

from superdesk.utc import utc_to_local
from superdesk.text_utils import get_text
from superdesk.publish.formatters import Formatter


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
        etree.SubElement(content, 'NewsCompID').text = '2'

        # timestamps
        firstpublished = item.get('firstpublished') or item['versioncreated']
        etree.SubElement(root, 'PublishDateTime').text = self._format_datetime(firstpublished)
        etree.SubElement(content, 'EmbargoTime').text = '0001-01-01T00:00:00'
        etree.SubElement(content, 'CreatedDateTime').text = self._format_datetime(item['firstcreated'])
        etree.SubElement(content, 'UpdatedDateTime').text = self._format_datetime(item['versioncreated'], True)

        # obvious
        word_count = str(item['word_count']) if item.get('word_count') else None
        etree.SubElement(content, 'ContentType').text = item['type'][0].upper() + item['type'][1:]
        etree.SubElement(content, 'Headline').text = item.get('headline')
        etree.SubElement(content, 'SlugProper').text = item.get('slugline')
        etree.SubElement(content, 'Credit').text = item.get('creditline')
        etree.SubElement(content, 'Source').text = item.get('source')
        etree.SubElement(content, 'EditorNote').text = item.get('ednote')
        etree.SubElement(content, 'Length').text = word_count
        etree.SubElement(content, 'WordCount').text = word_count
        etree.SubElement(content, 'BreakWordCount').text = word_count
        etree.SubElement(content, 'WritethruNum').text = self._get_writethru_num(item.get('rewrite_sequence'))
        etree.SubElement(content, 'DirectoryText').text = self._format_text(item.get('abstract'))
        etree.SubElement(content, 'ContentText').text = self._format_html(item.get('body_html'))
        etree.SubElement(content, 'Placeline')

    def _get_writethru_num(self, seq=None):
        return '1st'

    def _format_datetime(self, datetime, rel=False):
        if rel:
            relative = utc_to_local('America/Toronto', datetime)
            formatted = relative.strftime('%Y-%m-%dT%H:%M:%S%z')
            return formatted[:-2] + ':' + formatted[-2:]  # add : to timezone offset
        return datetime.strftime('%Y-%m-%dT%H:%M:%S')

    def _format_text(self, value):
        return get_text(value or '', 'html', True).strip()

    def _format_html(self, value):
        return value or ''
