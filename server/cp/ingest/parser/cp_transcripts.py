from typing import Dict, Any, Optional

from superdesk import get_resource_service
from superdesk.io.feed_parsers.ninjs import NINJSFeedParser
from superdesk.text_utils import plain_text_to_html


def get_previous_version(original_ingest_id: str, version_number: int) -> Optional[Dict[str, Any]]:
    while version_number >= 0:
        ingest_id = f"{original_ingest_id}.{version_number}"
        prev_item = get_resource_service("archive").find_one(req=None, ingest_id=ingest_id)

        if prev_item is not None:
            return prev_item
        version_number -= 1

    return None


class CPTranscriptsFeedParser(NINJSFeedParser):
    NAME = "cp_transcripts"
    label = "CP Transcripts"

    def _transform_from_ninjs(self, ninjs: Dict[str, Any]):
        original_guid = ninjs["guid"]
        version = int(ninjs["version"])
        ninjs["guid"] = f"{original_guid}.{version}"
        item = super()._transform_from_ninjs(ninjs)
        item["version"] = version
        item["body_html"] = plain_text_to_html(item["body_html"])
        item.setdefault("extra", {}).update(dict(
            publish_ingest_id_as_guid=True,
            cp_version=version,
            type="transcript",
        ))

        previous_item = get_previous_version(original_guid, version - 1)
        if previous_item is not None:
            item["rewrite_of"] = previous_item["ingest_id"]
        return item
