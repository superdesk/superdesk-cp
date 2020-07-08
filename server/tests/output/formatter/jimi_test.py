
import cp
import unittest
import superdesk
import lxml.etree as etree
import cp.ingest.parser.globenewswire as globenewswire

from pytz import UTC
from datetime import datetime
from unittest.mock import patch

from superdesk.metadata.utils import generate_guid

from cp.output.formatter.jimi import JimiFormatter

from tests.mock import resources, SEQUENCE_NUMBER


class JimiFormatterTestCase(unittest.TestCase):

    subscriber = {}
    formatter = JimiFormatter()
    article = {
        '_id': 'id',
        'family_id': 'famid',
        'type': 'text',
        'headline': 'Headline',
        'slugline': 'slug',
        'creditline': 'Credit',
        'source': 'Source',
        'ednote': 'Ednote',
        'word_count': 123,
        'abstract': '<p>Abstract</p>',
        'body_html': '<p>Body HTML</p>',
        'keywords': ['Foo bar', 'baz'],
        'anpa_category': [{'name': 'National', 'qcode': 'n'}],
        'subject': [
            {'name': 'health', 'qcode': '07000000', 'scheme': 'subject_custom'},
            {'name': 'citizens', 'qcode': '20000575', 'scheme': 'subject_custom'},
            {'name': 'made-up', 'qcode': '12345678901234', 'scheme': 'subject_custom'},
            {'name': 'Foo', 'qcode': '1231245', 'scheme': 'foo'},
            {'name': 'Broadcast', 'qcode': 'Broadcast', 'scheme': 'distribution'},
            {'name': 'The Associated Press', 'qcode': 'ap---', 'scheme': 'destinations'},
        ],
        'urgency': 2,
        'language': 'en-CA',

        'firstcreated': datetime(2020, 4, 1, 11, 13, 12, 25, tzinfo=UTC),
        'versioncreated': datetime(2020, 4, 1, 11, 23, 12, 25, tzinfo=UTC),
        'firstpublished': datetime(2020, 4, 1, 11, 33, 12, 25, tzinfo=UTC),

        'genre': [
            {'name': 'NewsAlert', 'qcode': 'NewsAlert'},
        ],

        'extra': {
            cp.HEADLINE2: 'headline2',
        },
    }

    def format(self, updates=None, _all=False):
        article = self.article.copy()
        article.update(updates or {})
        with patch.dict(superdesk.resources, resources):
            formatted = self.formatter.format(article, self.subscriber)
            if _all:
                return formatted
            seq, xml_str = formatted[0]
        print('xml', xml_str)
        return xml_str

    def get_root(self, xml):
        return etree.fromstring(xml.encode(self.formatter.ENCODING))

    def format_item(self, updates=None, return_root=False):
        xml = self.format(updates)
        root = self.get_root(xml)
        if return_root:
            return root
        return root.find('ContentItem')

    def test_can_format(self):
        self.assertTrue(self.formatter.can_format('jimi', {}))

    def test_format(self):
        xml = self.format()
        self.assertIn("<?xml version='1.0' encoding='utf-8'?>", xml)
        root = etree.fromstring(xml.encode(self.formatter.ENCODING))

        self.assertEqual('Publish', root.tag)
        self.assertEqual('false', root.find('Reschedule').text)
        self.assertEqual('false', root.find('IsRegional').text)
        self.assertEqual('true', root.find('CanAutoRoute').text)
        self.assertEqual(str(SEQUENCE_NUMBER), root.find('PublishID').text)
        self.assertEqual('Broadcast', root.find('Services').text)
        self.assertEqual(None, root.find('Username').text)
        self.assertEqual('false', root.find('UseLocalsOut').text)
        self.assertEqual('ap---', root.find('PscCodes').text)
        self.assertEqual('2020-04-01T11:33:12', root.find('PublishDateTime').text)

        item = root.find('ContentItem')
        self.assertEqual(None, item.find('Name').text)
        self.assertEqual('false', item.find('Cachable').text)

        # ids
        self.assertEqual(self.article['_id'], item.find('ContentItemID').text)
        self.assertEqual(self.article['family_id'], item.find('NewsCompID').text)
        self.assertEqual(self.article['family_id'], item.find('SystemSlug').text)
        self.assertEqual(self.article['family_id'], item.find('FileName').text)

        # obvious
        self.assertEqual('Text', item.find('ContentType').text)
        self.assertEqual(self.article['headline'], item.find('Headline').text)
        self.assertEqual('headline2', item.find('Headline2').text)
        self.assertEqual(self.article['creditline'], item.find('Credit').text)
        self.assertEqual(self.article['slugline'], item.find('SlugProper').text)
        self.assertEqual(self.article['source'], item.find('Source').text)
        self.assertEqual(self.article['ednote'], item.find('EditorNote').text)
        self.assertEqual(str(self.article['word_count']), item.find('WordCount').text)
        self.assertEqual(str(self.article['word_count']), item.find('BreakWordCount').text)
        self.assertEqual(str(self.article['word_count']), item.find('Length').text)
        self.assertEqual('Abstract', item.find('DirectoryText').text)
        self.assertEqual('<p>Body HTML</p>', item.find('ContentText').text)
        self.assertEqual(None, item.find('Placeline').text)
        self.assertEqual('0', item.find('WritethruValue').text)
        self.assertEqual('Foo bar,baz', item.find('Keyword').text)
        self.assertEqual('National', item.find('Category').text)
        self.assertEqual('Health,Politics', item.find('IndexCode').text)
        self.assertEqual(str(self.article['urgency']), item.find('RankingValue').text)
        self.assertEqual('News - Need to Know', item.find('Ranking').text)
        self.assertEqual('1', item.find('Language').text)

        # timestamps
        self.assertEqual('0001-01-01T00:00:00', item.find('EmbargoTime').text)
        self.assertEqual('2020-04-01T11:13:12', item.find('CreatedDateTime').text)
        self.assertEqual('2020-04-01T07:23:12-04:00', item.find('UpdatedDateTime').text)

        # etc
        self.assertEqual('NewsAlert', item.find('VersionType').text)

    def test_writethru(self):
        expected_data = {
            1: '1st',
            2: '2nd',
            3: '3rd',
            4: '4th',
            5: '5th',
            10: '10th',
            100: '100th',
            101: '101st',
        }

        for val, num in expected_data.items():
            item = self.format_item({'rewrite_sequence': val})
            self.assertEqual(num, item.find('WritethruNum').text)
            self.assertEqual(str(val), item.find('WritethruValue').text)
            self.assertEqual('Writethru', item.find('WriteThruType').text)

    def test_embargo(self):
        item = self.format_item({'embargoed': self.article['firstcreated']})
        self.assertEqual('2020-04-01T11:13:12', item.find('EmbargoTime').text)

    def test_dateline(self):
        item = self.format_item({
            'dateline': {
                'source': 'AAP',
                'text': 'sample dateline',
                'located': {
                    'alt_name': '',
                    'state': 'California',
                    'city_code': 'Los Angeles',
                    'city': 'Los Angeles',
                    'dateline': 'city',
                    'country_code': 'US',
                    'country': 'USA',
                    'tz': 'America/Los_Angeles',
                    'state_code': 'CA',
                    'location': {
                        'lat': 34.0522,
                        'lon': -118.2347,
                    },
                }
            },
        })
        self.assertEqual('Los Angeles', item.find('City').text)
        self.assertEqual('California', item.find('Province').text)
        self.assertEqual('USA', item.find('Country').text)
        self.assertEqual('Los Angeles;California;USA', item.find('Placeline').text)
        self.assertEqual('34.0522', item.find('Latitude').text)
        self.assertEqual('-118.2347', item.find('Longitude').text)

    def test_globenewswire(self):
        output = self.format({
            'source': globenewswire.SOURCE,
            'headline': 'Foo',
            'keywords': ['TSX VENTURE:AXL', 'OTC:NTGSF'],
            'anpa_category': [{
                'name': globenewswire.DESCRIPTION['en'],
                'qcode': 'p',
            }],
            'subject': [
                {'name': 'FOO', 'qcode': 'FOO', 'scheme': cp.SERVICE},
                {'name': 'BAR', 'qcode': 'BAR', 'scheme': cp.SERVICE},
            ],
            'extra': {},
        }, _all=True)

        self.assertEqual(2, len(output))

        root = etree.fromstring(output[0][1].encode(self.formatter.ENCODING))
        item = root.find('ContentItem')

        self.assertEqual('Print', root.find('Services').text)
        self.assertEqual('FOO', root.find('PscCodes').text)

        self.assertEqual('Press Release', item.find('Category').text)
        self.assertIsNone(item.find('IndexCode').text)
        self.assertEqual('FOO,BAR', item.find('Note').text)
        self.assertEqual('TSX VENTURE:AXL,OTC:NTGSF', item.find('Stocks').text)
        self.assertEqual('Foo', item.find('Headline').text)
        self.assertEqual('Foo', item.find('Headline2').text)
