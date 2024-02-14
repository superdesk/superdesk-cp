import os
import flask
import unittest
import lxml.etree as etree

from superdesk.io.feed_parsers import FeedParser


def get_fixture_path(filename, provider):
    return os.path.join(
        os.path.dirname(__file__),
        "fixtures",
        provider,
        filename,
    )


class ParserTestCase(unittest.TestCase):
    parser: FeedParser
    provider: str

    app = flask.Flask(__name__)

    def get_xml(self, filename):
        return etree.parse(get_fixture_path(filename, self.provider)).getroot()

    def parse(self, filename):
        xml = self.get_xml(filename)
        self.assertTrue(self.parser.can_parse(xml))
        with self.app.app_context():
            return self.parser.parse(xml)[0]
