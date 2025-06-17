from superdesk.tests import TestCase
import superdesk

from superdesk.core import json
from unittest.mock import patch
from tests.mock import resources

from superdesk.utc import utcnow
from cp.output import CPPublishService, JimiFormatter


now = utcnow()


class CPPublishServiceTestCase(TestCase):
    formatter = JimiFormatter()

    async def format_queue_item(self, item):
        with patch.dict(superdesk.resources, resources):
            resources["archive"].service.find_one_async.side_effect = [
                {"guid": "bar", "firstcreated": now, "unique_id": 1, "type": "text"},
            ]

            return {
                "item_id": "foo-bar",
                "item_version": 3,
                "content_type": "text",
                "destination": {"config": {"file_extension": "xml"}},
                "published_seq_num": 5,
                "formatted_item": (await self.formatter.format(item, {}))[0][1],
            }

    async def test_get_filename(self):
        item = {
            "type": "text",
            "guid": "foo",
            "language": "en",
            "rewrite_of": "bar",
            "firstcreated": now,
            "versioncreated": now,
            "unique_id": 2,
        }

        queue_item = await self.format_queue_item(item)
        self.assertEqual("bar.xml", CPPublishService.get_filename(queue_item))

    def test_get_filename_non_jimi(self):
        with patch.dict(superdesk.resources, resources):
            queue_item = {
                "item_id": "foo-bar",
                "item_version": 3,
                "content_type": "text",
                "destination": {"config": {"file_extension": "xml"}},
                "published_seq_num": 5,
                "formatted_item": json.dumps({}),
            }
            self.assertEqual("foo-bar.xml", CPPublishService.get_filename(queue_item))

            queue_item["formatted_item"] = (
                "<?xml version='1.0' encoding='utf-8'?><test></test>"
            )
            self.assertEqual("foo-bar.xml", CPPublishService.get_filename(queue_item))

            queue_item[
                "formatted_item"
            ] = """<?xml version='1.0' encoding='utf-8'?>
                <Publish><ContentItem></ContentItem></Publish>"""
            self.assertEqual("foo-bar.xml", CPPublishService.get_filename(queue_item))

    async def test_get_filename_media(self):
        item = {
            "type": "picture",
            "guid": "foo",
            "language": "en",
            "firstcreated": now,
            "versioncreated": now,
            "unique_id": 2,
            "renditions": {
                "original": {
                    "media": "media-id",
                    "mimetype": "image/jpeg",
                },
            },
        }
        queue_item = await self.format_queue_item(item)
        self.assertEqual("media-id.xml", CPPublishService.get_filename(queue_item))
