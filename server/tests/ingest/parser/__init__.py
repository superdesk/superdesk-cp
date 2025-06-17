import os
import lxml.etree as etree

from superdesk.tests import TestCase
from superdesk.io.feed_parsers import FeedParser


def get_fixture_path(filename, provider):
    return os.path.join(
        os.path.dirname(__file__),
        "fixtures",
        provider,
        filename,
    )


class ParserTestCase(TestCase):
    parser: FeedParser
    provider: str

    def get_xml(self, filename):
        return etree.parse(get_fixture_path(filename, self.provider)).getroot()

    async def parse(self, filename):
        xml = self.get_xml(filename)
        self.assertTrue(self.parser.can_parse(xml))
        # with self.app.app_context():
        return (await self.parser.parse(xml))[0]
