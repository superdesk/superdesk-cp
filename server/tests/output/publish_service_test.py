
import unittest
import superdesk

from flask import json
from unittest.mock import patch
from tests.mock import resources

from superdesk.utc import utcnow
from cp.output import CPPublishService, JimiFormatter


class CPPublishServiceTestCase(unittest.TestCase):

    formatter = JimiFormatter()

    def test_get_filename(self):
        now = utcnow()
        with patch.dict(superdesk.resources, resources):
            resources['archive'].service.find_one.side_effect = [
                {'guid': 'bar', 'firstcreated': now},
            ]

            item = {
                'type': 'text',
                'guid': 'foo',
                'language': 'en',
                'rewrite_of': 'bar',
                'firstcreated': now,
                'versioncreated': now,
            }

            queue_item = {
                'item_id': 'foo-bar',
                'item_version': 3,
                'content_type': 'text',
                'destination': {'config': {'file_extension': 'xml'}},
                'published_seq_num': 5,
                'formatted_item': self.formatter.format(item, {})[0][1]
            }

            self.assertEqual('bar.xml', CPPublishService.get_filename(queue_item))

    def test_get_filename_non_jimi(self):
        with patch.dict(superdesk.resources, resources):
            queue_item = {
                'item_id': 'foo-bar',
                'item_version': 3,
                'content_type': 'text',
                'destination': {'config': {'file_extension': 'xml'}},
                'published_seq_num': 5,
                'formatted_item': json.dumps({})
            }
            self.assertEqual('foo-bar.xml', CPPublishService.get_filename(queue_item))

            queue_item['formatted_item'] = "<?xml version='1.0' encoding='utf-8'?><test></test>"
            self.assertEqual('foo-bar.xml', CPPublishService.get_filename(queue_item))

            queue_item['formatted_item'] = """<?xml version='1.0' encoding='utf-8'?>
                <Publish><ContentItem></ContentItem></Publish>"""
            self.assertEqual('foo-bar.xml', CPPublishService.get_filename(queue_item))
