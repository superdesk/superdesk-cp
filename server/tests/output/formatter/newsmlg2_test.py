
import cp

from . import BaseXmlFormatterTestCase

from superdesk.utc import utcnow
from cp.output.formatter.newsmlg2 import CPNewsMLG2Formatter

NSMAP = {
    None: 'http://iptc.org/std/nar/2006-10-01/',
}


class NewsmlG2TestCase(BaseXmlFormatterTestCase):

    now = utcnow()
    formatter = CPNewsMLG2Formatter()
    article = {
        '_id': 'id',
        'guid': 'guid',
        'type': 'text',
        'state': 'published',
        'version': 1,
        'firstcreated': now,
        'versioncreated': now,
        'headline': 'short headline',
        'extra': {
            cp.HEADLINE2: 'long headline',
        },
    }

    def test_format(self):
        xml = self.format()
        root = self.parse(xml)

        item = root.find('itemSet', NSMAP).find('newsItem', NSMAP)
        self.assertIsNotNone(item)

        content_meta = item.find('contentMeta', NSMAP)
        self.assertIsNotNone(content_meta)

        headlines = content_meta.findall('headline', NSMAP)
        self.assertEqual(2, len(headlines))
        self.assertEqual('long headline', headlines[0].text)
        self.assertIsNone(headlines[0].attrib.get('role'))
        self.assertEqual('short headline', headlines[1].text)
        self.assertEqual('short', headlines[1].attrib.get('role'))
