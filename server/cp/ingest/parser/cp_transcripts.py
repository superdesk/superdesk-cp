from typing import Dict, Any

from superdesk.io.feed_parsers.ninjs import NINJSFeedParser


class CPTranscriptsFeedParser(NINJSFeedParser):
    NAME = "cp_transcripts"
    label = "CP Transcripts"

    def _transform_from_ninjs(self, ninjs: Dict[str, Any]):
        original_guid = ninjs["guid"]
        version = int(ninjs["version"])
        ninjs["guid"] = f"{original_guid}.{version}"
        item = super()._transform_from_ninjs(ninjs)
        item["version"] = version
        item["body_html"] = (
            item["body_html"]
            if item["body_html"].strip().startswith("<p>")
            else "<p>{}</p>".format(item["body_html"])
        )
        item.setdefault("extra", {}).update(
            dict(
                publish_ingest_id_as_guid=True,
                cp_version=version,
                type="transcript",
            )
        )

        if version > 0:
            # set it as expected not based on what already arrived
            item["rewrite_of"] = f"{original_guid}.{version-1}"

        return item
