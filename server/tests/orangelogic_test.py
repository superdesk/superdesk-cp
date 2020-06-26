
import os
import flask
import unittest

from unittest.mock import patch
from httmock import urlmatch, HTTMock, remember_called
from requests.exceptions import HTTPError
from cp.orangelogic import OrangelogicSearchProvider, AUTH_API, SEARCH_API


def read_fixture(filename):
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        return f.read()


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


class OrangelogicTestCase(unittest.TestCase):

    provider = {'config': {'username': 'foo', 'password': 'bar'}}

    def setUp(self):
        self.app = flask.Flask(__name__)
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

    @patch('cp.orangelogic.update_renditions')
    def test_fetch(self, update_renditions_mock):
        service = OrangelogicSearchProvider(self.provider)

        with HTTMock(auth_ok, search_ok):
            item = service.fetch({})
            update_renditions_mock.assert_called_once_with(
                item,
                'https://example.com/htm/GetDocumentAPI.aspx?F=TRX&DocID=encID&token=token.foo',
                None,
            )
