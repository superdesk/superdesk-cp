
import flask
import unittest
import superdesk
import lxml.etree as etree
import requests_mock

from flask import json
from unittest.mock import MagicMock, patch

from tests.mock import resources
from tests.ingest.parser import get_fixture_path

from cp.ingest import CP_APMediaFeedParser
from cp.output.formatter.jimi import JimiFormatter


parser = CP_APMediaFeedParser()
formatter = JimiFormatter()


class AP2JimiTestCase(unittest.TestCase):

    app = flask.Flask(__name__)
    app.locators = MagicMock()

    provider = {}
    subscriber = {}

    def parse_format(self, source, binary):
        with open(get_fixture_path(source, 'ap')) as fp:
            data = json.load(fp)

        with self.app.app_context():
            with patch.dict(superdesk.resources, resources):
                with requests_mock.mock() as mock:
                    with open(get_fixture_path(binary, 'ap'), 'rb') as f:
                        mock.get(data['data']['item']['renditions']['preview']['href'], content=f.read())
                    parsed = parser.parse(data, self.provider)
                parsed['_id'] = 'generated-id'
                parsed['family_id'] = parsed['_id']
                jimi = formatter.format(parsed, self.subscriber)[0][1]

        root = etree.fromstring(jimi.encode(formatter.ENCODING))
        return root.find('ContentItem')

    def test_getty_picture(self):
        """
        ref: tests/io/fixtures/6dd9971f75c24ce59865879cf315d7fe-6dd9971f75c24ce59.xml
        """
        item = self.parse_format('ap-getty-picture.json', 'preview.jpg')
        self.assertEqual('Stuart Franklin', item.find('Byline').text)
        self.assertEqual('S', item.find('Category').text)
        self.assertEqual('THE ASSOCIATED PRESS', item.find('Credit').text)
        self.assertEqual('Virus Outbreak Germany Soccer Bundesliga', item.find('SlugProper').text)
        self.assertEqual('Unknown AP', item.find('Source').text)
        self.assertEqual('Bremen', item.find('City').text)
        self.assertEqual('Germany', item.find('Country').text)
        self.assertEqual('Bremen;;Germany', item.find('Placeline').text)
        self.assertEqual('DMSC113', item.find('OrigTransRef').text)
        self.assertEqual('POOL', item.find('BylineTitle').text)
        self.assertEqual('bl', item.find('CaptionWriter').text)
        self.assertEqual('(c) Getty Images Europe/Pool', item.find('Copyright').text)
        self.assertEqual("Frankfurt's Stefan IIsanker, right, celebrates after he scores his side second goal during "
                         "the German Bundesliga soccer match between SV Werder Bremen and Eintracht Frankfurt "
                         "in Bremen, Germany, Wednesday, June 3, 2020. Because of the coronavirus outbreak all soccer "
                         "matches of the German Bundesliga take place without spectators. "
                         "(Stuart Franklin/Pool via AP)", item.find('EnglishCaption').text)
        self.assertEqual('2020-06-03T20:22:03', item.find('DateTaken').text)
        self.assertEqual('SOC', item.find('SupplementalCategories').text)
        self.assertEqual('POOL PHOTO, THE DEUTSCHE FUSSBALL LIGA DFL DOES NOT ALLOW THE IMAGES TO BE USED AS '
                         'SEQUENCES TO EMULATE VIDEO.', item.find('SpecialInstructions').text)
        self.assertEqual('Unknown AP', item.find('ArchiveSources').text)
        self.assertEqual('6dd9971f75c24ce59865879cf315d7fe', item.find('CustomField1').text)
        self.assertEqual('POOL Getty Images', item.find('CustomField6').text)

    def test_ap_picture(self):
        """
        ref: tests/io/fixtures/AB101-65_2020_101001.xml
        """
        item = self.parse_format('ap-picture.json', 'preview-keywords.jpg')
        self.assertEqual('AB101-65_2020_101001', item.find('FileName').text)
        self.assertEqual('I', item.find('Category').text)
        self.assertEqual('Santos Munoz', item.find('Headline2').text)
        self.assertEqual('THE ASSOCIATED PRESS', item.find('Credit').text)
        self.assertEqual('Virus Outbreak Spain', item.find('SlugProper').text)
        self.assertEqual('The Associated Press', item.find('Source').text)
        self.assertEqual('Coronavirus, COVID-19', item.find('Keyword').text)
        self.assertEqual('Pamplona', item.find('City').text)
        self.assertEqual('Spain', item.find('Country').text)
        self.assertEqual('42.81687', item.find('Latitude').text)  # using data from ap, jimi has it wrong
        self.assertEqual('-1.64323', item.find('Longitude').text)
        self.assertEqual('Pamplona;;Spain', item.find('Placeline').text)
        self.assertEqual('AB101', item.find('OrigTransRef').text)
        self.assertEqual('STR', item.find('BylineTitle').text)
        self.assertEqual('AB', item.find('CaptionWriter').text)
        self.assertEqual('Copyright 2019 The Associated Press. All rights re', item.find('Copyright').text)
        self.assertEqual('2020-06-05T10:10:01', item.find('DateTaken').text)
        self.assertEqual('AP', item.find('ArchiveSources').text)
        self.assertEqual('Coronavirus, COVID-19', item.find('XmpKeywords').text)
        self.assertEqual('de1bb822362146388852c8b7eee93c76', item.find('CustomField1').text)
        self.assertEqual('AB101-65/2020_101001', item.find('CustomField2').text)
        self.assertEqual('AP', item.find('CustomField6').text)
