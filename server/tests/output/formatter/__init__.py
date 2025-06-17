from superdesk.tests import TestCase
import superdesk
import lxml.etree as etree

from tests.mock import resources
from unittest.mock import patch


class BaseXmlFormatterTestCase(TestCase):
    subscriber = {}
    formatter = None
    article = None

    app_config = {
        # "VERSION": "version",
        # "DEFAULT_LANGUAGE": "en",
        # "MAX_VALUE_OF_PUBLISH_SEQUENCE": 9999,
    }

    async def format(self, updates=None, _all=False):
        article = self.article.copy()
        article.update(updates or {})
        with patch.dict(superdesk.resources, resources):
            formatted = await self.formatter.format(article, self.subscriber)
            if _all:
                return formatted
            seq, xml_str = formatted[0]
        return xml_str

    def parse(self, xml):
        return etree.fromstring(xml.encode(self.formatter.ENCODING))
