import cp
import flask
import unittest
import lxml.etree as etree

from ..parser import get_fixture_path

from cp.ingest.parser.globenewswire import GlobeNewswireParser


class GlobeNewswireParserTestCase(unittest.TestCase):
    app = flask.Flask(__name__)

    def get_xml(self, filename):
        return etree.parse(get_fixture_path(filename, 'globenewswire')).getroot()

    def parse(self, filename):
        xml = self.get_xml(filename)
        parser = GlobeNewswireParser()
        self.assertTrue(parser.can_parse(xml))
        with self.app.app_context():
            return parser.parse(xml)[0]

    def test_parser(self):
        item = self.parse('0b78.xml')
        self.assertIsNotNone(item)

        self.assertIsNone(item.get('byline'))
        self.assertEqual('en', item['language'])
        self.assertEqual('usable', item['pubstatus'])
        self.assertEqual('GNW-en-10--AXL', item['slugline'])
        self.assertEqual(['TSX VENTURE:AXL', 'OTC:NTGSF'], item['keywords'])
        self.assertEqual(3, item['urgency'])
        self.assertEqual(3, item['priority'])
        self.assertEqual({
            'name': 'Press Release',
            'qcode': 'p',
        }, item['anpa_category'][0])
        self.assertEqual('Globenewswire', item['source'])
        self.assertEqual('Press Release', item['description_text'])

        self.assertIn({'name': 'TSXVO', 'qcode': 'TSXVO', 'scheme': cp.SERVICE}, item['subject'])

        self.assertGreaterEqual(item['word_count'], 1)
        self.assertRegex(item['body_html'], r'^<p>CALGARY')
        self.assertNotIn('https://www.globenewswire.com/newsroom/ti', item['body_html'])
        self.assertIn('<p>NEWS RELEASE TRANSMITTED BY Globe Newswire</p>', item['body_html'])

    def test_parser_slugline(self):
        item = self.parse('1bf6.xml')
        self.assertIsNotNone(item)
        self.assertEqual('GNW-en-10--CAL-MIS-FNC', item['slugline'])
        self.assertIn('<a href="https://www.globenewswire.com/', item['body_html'])

    def test_fr(self):
        item = self.parse('fr.xml')
        self.assertIsNotNone(item)
        self.assertEqual('fr', item['language'])
        self.assertEqual('Communiqué', item['description_text'])

    def test_abstract(self):
        self.maxDiff = None
        item = self.parse('202006097942547-en.newsml')
        self.assertEqual('FOR: AUXLY CANNABIS GROUP INC. '
                         'TORONTO, June 09, 2020 (GLOBE NEWSWIRE) -- Auxly Cannabis Group Inc. '
                         '(TSX.V: XLY) (OTCQX: CBWTF) '
                         '(“Auxly” or the “Company”) has issued an additional $3 million wort',
                         item['abstract'])
