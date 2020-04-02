import flask
import unittest
import lxml.etree as etree

from ..parser import get_fixture_path

from cp.ingest.parser.globenewswire import GlobeNewswireParser


class GlobeNewswireParserTestCase(unittest.TestCase):
    app = flask.Flask(__name__)

    def get_xml(self, filename):
        return etree.parse(get_fixture_path(filename, 'globenewswire')).getroot()

    def test_parser(self):
        xml = self.get_xml('0b78.xml')
        parser = GlobeNewswireParser()
        self.assertTrue(parser.can_parse(xml))
        with self.app.app_context():
            item = parser.parse(xml)[0]
        self.assertIsNotNone(item)

        self.assertIsNone(item.get('byline'))
        self.assertEqual('en', item['language'])
        self.assertEqual('usable', item['pubstatus'])
        self.assertEqual('GNW-en-10--AXL', item['slugline'])
        self.assertEqual(['TSX VENTURE:AXL'], item['keywords'])

        self.assertGreaterEqual(item['word_count'], 1)
        self.assertRegex(item['body_html'], r'^<p>CALGARY')
        self.assertNotIn('https://www.globenewswire.com/newsroom/ti', item['body_html'])

        self.assertEqual('Press Release', item['description_text'])
        self.assertEqual('NEWS RELEASE TRANSMITTED BY Globe Newswire', item['body_footer'])

    def test_parser_slugline(self):
        xml = self.get_xml('1bf6.xml')
        parser = GlobeNewswireParser()
        with self.app.app_context():
            item = parser.parse(xml)[0]
        self.assertEqual('GNW-en-10--CAL-MIS-FNC', item['slugline'])
