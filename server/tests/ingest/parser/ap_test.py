
import unittest


from cp.ingest import CP_APMediaFeedParser


class CP_AP_ParseTestCase(unittest.TestCase):

    def test_slugline(self):
        parser = CP_APMediaFeedParser()
        self.assertEqual('foo-bar-baz', parser.process_slugline('foo bar/baz'))
        self.assertEqual('foo-bar', parser.process_slugline('foo-bar'))
        self.assertEqual('foo-bar', parser.process_slugline('foo - bar'))
