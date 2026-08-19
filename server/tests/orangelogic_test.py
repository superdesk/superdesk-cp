import os
import io
import pytz
import re
from aioresponses import aioresponses

from superdesk.flask import Flask
from superdesk.tests import TestCase
import superdesk
import lxml.etree as etree

from datetime import datetime
from unittest.mock import patch
from httmock import urlmatch, HTTMock

# from requests.exceptions import HTTPError
from aiohttp.client_exceptions import ClientError
from superdesk.utc import tzinfo
from tests.mock import resources, media_storage

from cp.orangelogic import OrangelogicSearchProvider, _parse_xmp_datetime
from cp.output.formatter.jimi import JimiFormatter


def fixture(filename):
    return os.path.join(os.path.dirname(__file__), "fixtures", filename)


def read_fixture(filename, mode="r"):
    with open(fixture(filename), mode=mode) as f:
        return f.read()


def set_rendition(item, *args, **kwargs):
    item["renditions"]["original"] = {
        "media": "media-id",
    }


auth_url = re.compile(r"^https://example\.com/API/Auth")
search_url = re.compile(r"^https://example\.com/API/Search")


def auth_ok(aiohttp_mock: aioresponses):
    aiohttp_mock.post(auth_url, body=read_fixture("orangelogic_auth.json"))


def search_ok(aiohttp_mock: aioresponses):
    aiohttp_mock.get(search_url, body=read_fixture("orangelogic_search.json"))


def auth_error(aiohttp_mock: aioresponses):
    aiohttp_mock.post(auth_url, status=400)


def search_error(aiohttp_mock: aioresponses):
    aiohttp_mock.get(search_url, status=400)


def fetch_ok(aiohttp_mock: aioresponses):
    aiohttp_mock.get(search_url, body=read_fixture("orangelogic_fetch.json"))


class MockAsyncFile:
    def __init__(self, data):
        self.data = data

    async def read(self):
        return self.data


class OrangelogicTestCase(TestCase):
    provider = {"config": {"username": "foo", "password": "bar"}}
    app_config = {"ORANGELOGIC_URL": "https://example.com/"}

    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.app.media = media_storage
        self.service = OrangelogicSearchProvider(self.provider)

    async def asyncTearDown(self):
        await super().asyncTearDown()
        if self.service and self.service.session:
            await self.service.session.close()

    async def test_find(self):
        with aioresponses() as aiohttp_mock:
            auth_ok(aiohttp_mock)
            search_ok(aiohttp_mock)
            items = await self.service.find_async({})

        self.assertEqual(5, len(items))
        self.assertEqual(items.count(), 2021650)

        # test video
        self.assertEqual("video", items[0]["type"])

        self.assertEqual(
            {
                "href": "https://example.com/video.mp4",
                "width": 1280,
                "height": 720,
                "mimetype": "video/mp4",
            },
            items[0]["renditions"]["webHigh"],
        )

        self.assertEqual(
            {
                "href": "https://example.com/thumb.jpg",
                "width": 341,
                "height": 192,
                "mimetype": "image/jpeg",
            },
            items[0]["renditions"]["thumbnail"],
        )

        self.assertEqual(
            {
                "href": "https://example.com/thumb.jpg",
                "width": 341,
                "height": 192,
                "mimetype": "image/jpeg",
            },
            items[0]["renditions"]["viewImage"],
        )

    async def test_repeat_and_raise_on_error(self):
        with aioresponses() as aiohttp_mock:
            auth_ok(aiohttp_mock)
            search_error(aiohttp_mock)
            with self.assertRaises(ClientError):
                items = await self.service.find_async({})

        with aioresponses() as aiohttp_mock:
            auth_error(aiohttp_mock)
            search_error(aiohttp_mock)
            with self.assertRaises(ClientError):
                items = await self.service.find_async({})

    @patch("cp.orangelogic.update_renditions_async", side_effect=set_rendition)
    async def test_fetch_to_jimi(self, update_renditions_mock):
        self.app.media.get_async.return_value = MockAsyncFile(
            read_fixture(
                "9e627f74b97841b3b8562b6547ada9c7-d1538139479c43e88021152.jpg", "rb"
            )
        )

        with aioresponses() as aiohttp_mock:
            auth_ok(aiohttp_mock)
            fetch_ok(aiohttp_mock)

            with patch.dict(superdesk.resources, resources):
                fetched = await self.service.fetch_async({})

            update_renditions_mock.assert_awaited_once_with(
                fetched,
                "https://example.com/htm/GetDocumentAPI.aspx?F=TRX&DocID=2RLQZBCB4R4R4&token=token.foo",
                None,
            )

        self.assertEqual("picture", fetched["type"])
        self.assertIsInstance(fetched["firstcreated"], datetime)

        # populate ids
        fetched["family_id"] = fetched["guid"]
        fetched["unique_id"] = 1

        with patch.dict(superdesk.resources, resources):
            formatter = JimiFormatter()
            xml = (await formatter.format(fetched, {}))[0][1]

        root = etree.fromstring(xml.encode(formatter.ENCODING))

        self.assertEqual("Pictures", root.find("Services").text)

        item = root.find("ContentItem")

        self.assertEqual("Zhang Yuwei", item.find("Byline").text)
        self.assertEqual("I", item.find("Category").text)
        self.assertEqual("News - Optional", item.find("Ranking").text)
        self.assertEqual("5", item.find("RankingValue").text)
        self.assertEqual("THE ASSOCIATED PRESS", item.find("Credit").text)
        self.assertEqual("Virus Outbreak China Vaccine", item.find("SlugProper").text)
        self.assertEqual("Unknown AP", item.find("Source").text)
        self.assertEqual("Beijing", item.find("City").text)
        self.assertEqual("China", item.find("Country").text)
        self.assertEqual("Beijing;;China", item.find("Placeline").text)
        # self.assertEqual('XIN902', item.find('OrigTransRef').text)
        self.assertEqual("SUB", item.find("BylineTitle").text)
        self.assertEqual("NHG", item.find("CaptionWriter").text)
        self.assertEqual("Xinhua", item.find("Copyright").text)
        self.assertIn(
            "In this April 10, 2020, photo released by Xinhua News Agency, a staff",
            item.find("EnglishCaption").text,
        )
        self.assertEqual("2020-04-12T00:09:37", item.find("DateTaken").text)
        self.assertEqual(
            "NO SALES, PHOTO RELEASED BY XINHUA NEWS AGENCY APRIL 10, 2020 PHOTO",
            item.find("SpecialInstructions").text,
        )
        self.assertEqual("Unknown AP", item.find("ArchiveSources").text)
        self.assertEqual(
            "9e627f74b97841b3b8562b6547ada9c7", item.find("CustomField1").text
        )
        self.assertEqual("Xinhua", item.find("CustomField6").text)
        self.assertEqual(
            "9e627f74b97841b3b8562b6547ada9c7", item.find("SystemSlug").text
        )

    def test_parse_datetime(self):
        self.assertEqual(
            datetime(2015, 4, 13, 0, 0, 0, tzinfo=pytz.UTC),
            _parse_xmp_datetime("2015-04-13"),
        )

        self.assertEqual(
            datetime(2015, 4, 13, 1, 2, 3, tzinfo=pytz.UTC),
            _parse_xmp_datetime("2015-04-13T01:02:03"),
        )

        self.assertEqual(
            datetime(2015, 4, 13, 1, 2, 3, tzinfo=pytz.UTC),
            _parse_xmp_datetime("2015-04-13T01:02:03.000"),
        )
