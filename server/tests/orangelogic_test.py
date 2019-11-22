
import os
import flask
import unittest

from httmock import urlmatch, HTTMock
from cp.orangelogic import OrangelogicSearchProvider, AUTH_API, SEARCH_API


def read_fixture(filename):
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        return f.read()


@urlmatch(netloc=r'example\.com$')
def orangelogic_mock(url, request):
    if url.path == AUTH_API:
        return read_fixture('orangelogic_auth.json')
    if url.path == SEARCH_API:
        return read_fixture('orangelogic_search.json')
    raise ValueError(url.path)


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

        with HTTMock(orangelogic_mock):
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
            'width': 1200,
            'height': 675,
            'mimetype': 'image/jpeg',
        }, items[0]['renditions']['viewImage'])
