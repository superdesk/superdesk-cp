
import json
import flask
import unittest
import superdesk

from unittest.mock import MagicMock, patch
from tests.ingest.parser import get_fixture_path

from tests.mock import resources

from cp import HEADLINE2
from cp.ingest import CP_APMediaFeedParser


with open(get_fixture_path('item.json', 'ap')) as fp:
    data = json.load(fp)


class CP_AP_ParseTestCase(unittest.TestCase):

    app = flask.Flask(__name__)
    app.locators = MagicMock()

    def test_slugline(self):
        parser = CP_APMediaFeedParser()
        self.assertEqual('foo-bar-baz', parser.process_slugline('foo bar/baz'))
        self.assertEqual('foo-bar', parser.process_slugline('foo-bar'))
        self.assertEqual('foo-bar', parser.process_slugline('foo - bar'))

    def test_parse(self):
        provider = {}
        parser = CP_APMediaFeedParser()

        with self.app.app_context():
            with patch.dict(superdesk.resources, resources):
                item = parser.parse(data, provider)

        self.assertEqual('ba7d03f0cd24a17faa81bebc724bcf3f_0a8aza0c0', item['guid'])
        self.assertEqual('Story', item['profile'])
        self.assertEqual('WY-Exchange-Coronavirus-Tech', item['slugline'])
        self.assertEqual('headline1', item['headline'])
        self.assertEqual('headline1', item['extra'][HEADLINE2])
        self.assertIn('copyright information', item['copyrightnotice'])
        self.assertIn('editorial use only', item['usageterms'])
        self.assertEqual('The Associated Press', item['source'])
        self.assertEqual(5, item['urgency'])
        self.assertEqual('Margaret Austin', item['byline'])
        self.assertIn('General news', item['keywords'])

        self.assertIn({
            'name': 'Feature',
            'qcode': 'Feature',
        }, item['genre'])

        self.assertEqual('UPDATES: With AP Photos.', item['extra']['update'])
        self.assertEqual('', item['ednote'])

        self.assertEqual('NYSE:WFC', item['extra']['stocks'])

        self.assertIn({
            'name': 'International',
            'qcode': 'w',
        }, item['anpa_category'])

        subjects = [s['name'] for s in item['subject']]
        self.assertIn('science and technology', subjects)
        self.assertIn('health', subjects)
        self.assertIn('mass media', subjects)
        self.assertIn('technology and engineering', subjects)

        dateline = item['dateline']
        self.assertEqual('Wyoming Tribune Eagle', dateline['source'])
        self.assertEqual('CHEYENNE, Wyo.', dateline['text'])
        self.assertIn('located', dateline)
        self.assertEqual('Cheyenne', dateline['located']['city'])
        self.assertEqual('Wyoming', dateline['located']['state'])
        self.assertEqual('WY', dateline['located']['state_code'])
        self.assertEqual('United States', dateline['located']['country'])
        self.assertEqual('USA', dateline['located']['country_code'])
        self.assertEqual(41.13998, dateline['located']['location']['lat'])
        self.assertEqual(-104.82025, dateline['located']['location']['lon'])

        self.assertIn('associations', item)
        self.assertIn('media-gallery--1', item['associations'])
        self.assertIn('media-gallery--2', item['associations'])
