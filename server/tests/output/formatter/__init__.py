
import flask
import unittest
import superdesk
import lxml.etree as etree

from tests.mock import resources
from unittest.mock import patch


class BaseXmlFormatterTestCase(unittest.TestCase):

    subscriber = {}
    formatter = None
    article = None

    def setUp(self):
        self.app = flask.Flask(__name__)
        self.app.config.update({
            'VERSION': 'version',
        })
        self.app.app_context().push()

    def format(self, updates=None, _all=False):
        article = self.article.copy()
        article.update(updates or {})
        with patch.dict(superdesk.resources, resources):
            formatted = self.formatter.format(article, self.subscriber)
            if _all:
                return formatted
            seq, xml_str = formatted[0]
        return xml_str

    def parse(self, xml):
        return etree.fromstring(xml.encode(self.formatter.ENCODING))
