
import os
import io
import pytz
import flask
import unittest
import superdesk
import lxml.etree as etree

from datetime import datetime
from unittest.mock import patch
from httmock import urlmatch, HTTMock
from requests.exceptions import HTTPError
from superdesk.utc import tzinfo
from tests.mock import resources, media_storage

from cp.orangelogic import OrangelogicSearchProvider, _parse_xmp_datetime
from cp.output.formatter.jimi import JimiFormatter


def fixture(filename):
    return os.path.join(os.path.dirname(__file__), 'fixtures', filename)


def read_fixture(filename, mode='r'):
    with open(fixture(filename), mode=mode) as f:
        return f.read()


def set_rendition(item, *args, **kwargs):
    item['renditions']['original'] = {
        'media': 'media-id',
    }


@urlmatch(netloc=r'example\.com$', path=r'/API/Auth')
def auth_ok(url, request):
    return read_fixture('orangelogic_auth.json')


@urlmatch(netloc=r'example\.com$', path=r'/API/Search')
def search_ok(url, request):
    return read_fixture('orangelogic_search.json')


@urlmatch(netloc=r'example\.com$', path=r'/API/Auth')
def auth_error(url, request):
    return {'status_code': 400}


@urlmatch(netloc=r'example\.com$', path=r'/API/Search')
def search_error(url, request):
    return {'status_code': 400}


@urlmatch(netloc=r'example\.com$', path=r'/API/Search')
def fetch_ok(url, request):
    return read_fixture('orangelogic_fetch.json')


class OrangelogicTestCase(unittest.TestCase):

    provider = {'config': {'username': 'foo', 'password': 'bar'}}

    def setUp(self):
        self.app = flask.Flask(__name__)
        self.app.media = media_storage
        self.app.config['ORANGELOGIC_URL'] = 'https://example.com/'
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        if hasattr(self, 'ctx'):
            self.ctx.pop()

    def test_instance(self):
        OrangelogicSearchProvider(self.provider)

    def test_find(self):
        service = OrangelogicSearchProvider(self.provider)

        with HTTMock(auth_ok, search_ok):
            items = service.find({})

        self.assertEqual(5, len(items))
        self.assertEqual(items.count(), 2021650)

        # test video
        self.assertEqual('video', items[0]['type'])

        self.assertEqual({
            'href': 'https://example.com/video.mp4',
            'width': 1280,
            'height': 720,
            'mimetype': 'video/mp4',
        }, items[0]['renditions']['webHigh'])

        self.assertEqual({
            'href': 'https://example.com/thumb.jpg',
            'width': 341,
            'height': 192,
            'mimetype': 'image/jpeg',
        }, items[0]['renditions']['thumbnail'])

        self.assertEqual({
            'href': 'https://example.com/view.jpg',
            'width': 800,
            'height': 600,
            'mimetype': 'image/jpeg',
        }, items[0]['renditions']['viewImage'])

    def test_repeat_and_raise_on_error(self):
        service = OrangelogicSearchProvider(self.provider)

        with HTTMock(auth_ok, search_error):
            with self.assertRaises(HTTPError):
                items = service.find({})

        with HTTMock(auth_error, search_error):
            with self.assertRaises(HTTPError):
                items = service.find({})

    @patch('cp.orangelogic.update_renditions', side_effect=set_rendition)
    def test_fetch_to_jimi(self, update_renditions_mock):
        service = OrangelogicSearchProvider(self.provider)

        update_renditions_mock.side_effects = set_rendition

        self.app.media.get.return_value = io.BytesIO(
            read_fixture('9e627f74b97841b3b8562b6547ada9c7-d1538139479c43e88021152.jpg', 'rb')
        )

        with HTTMock(auth_ok, fetch_ok):
            with patch.dict(superdesk.resources, resources):
                fetched = service.fetch({})
            update_renditions_mock.assert_called_once_with(
                fetched,
                'https://example.com/htm/GetDocumentAPI.aspx?F=TRX&DocID=2RLQZBCB4R4R4&token=token.foo',
                None,
            )

        self.assertEqual('picture', fetched['type'])
        self.assertIsInstance(fetched['firstcreated'], datetime)

        # populate ids
        fetched['family_id'] = fetched['guid']

        with patch.dict(superdesk.resources, resources):
            formatter = JimiFormatter()
            xml = formatter.format(fetched, {})[0][1]

        root = etree.fromstring(xml.encode(formatter.ENCODING))

        self.assertEqual('Pictures', root.find('Services').text)

        item = root.find('ContentItem')

        self.assertEqual('Zhang Yuwei', item.find('Byline').text)
        self.assertEqual('I', item.find('Category').text)
        self.assertEqual('News - Optional', item.find('Ranking').text)
        self.assertEqual('5', item.find('RankingValue').text)
        self.assertEqual('THE ASSOCIATED PRESS', item.find('Credit').text)
        self.assertEqual('Virus Outbreak China Vaccine', item.find('SlugProper').text)
        self.assertEqual('Unknown AP', item.find('Source').text)
        self.assertEqual('Beijing', item.find('City').text)
        self.assertEqual('China', item.find('Country').text)
        self.assertEqual('Beijing;;China', item.find('Placeline').text)
        # self.assertEqual('XIN902', item.find('OrigTransRef').text)
        self.assertEqual('SUB', item.find('BylineTitle').text)
        self.assertEqual('NHG', item.find('CaptionWriter').text)
        self.assertEqual('Xinhua', item.find('Copyright').text)
        self.assertIn("In this April 10, 2020, photo released by Xinhua News Agency, a staff",
                      item.find('EnglishCaption').text)
        self.assertEqual('2020-04-12T00:09:37', item.find('DateTaken').text)
        self.assertEqual('NO SALES, PHOTO RELEASED BY XINHUA NEWS AGENCY APRIL 10, 2020 PHOTO',
                         item.find('SpecialInstructions').text)
        self.assertEqual('Unknown AP', item.find('ArchiveSources').text)
        self.assertEqual('9e627f74b97841b3b8562b6547ada9c7', item.find('CustomField1').text)
        self.assertEqual('Xinhua', item.find('CustomField6').text)

    def test_parse_datetime(self):
        self.assertEqual(
            datetime(2015, 4, 13, 0, 0, 0, tzinfo=pytz.UTC),
            _parse_xmp_datetime('2015-04-13'),
        )

        self.assertEqual(
            datetime(2015, 4, 13, 1, 2, 3, tzinfo=pytz.UTC),
            _parse_xmp_datetime('2015-04-13T01:02:03'),
        )

        self.assertEqual(
            datetime(2015, 4, 13, 1, 2, 3, tzinfo=pytz.UTC),
            _parse_xmp_datetime('2015-04-13T01:02:03.000'),
        )
