import cp

from . import ParserTestCase

from cp.ingest import BusinessWireParser


class BusinessWireTestCase(ParserTestCase):

    parser = BusinessWireParser()
    provider = "businesswire"

    def test_parser(self):
        filename = "20210130005024r1.xml"
        item = self.parse(filename)
        self.assertIsNotNone(item)
        self.assertEqual(
            "Interactive Brokers Lifts All Trading Restrictions on Options",
            item["headline"],
        )
        self.assertEqual(
            "Interactive Brokers lifts all trading restrictions on options",
            item["abstract"],
        )
        self.assertRegex(item["body_html"], r"^<p>")
        self.assertIn(
            {
                "name": "Interactive Brokers Group",
                "qcode": "Interactive Brokers Group",
                "scheme": cp.ORGANISATION,
            },
            item["subject"],
        )
