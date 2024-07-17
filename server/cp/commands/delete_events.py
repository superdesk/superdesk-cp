import sys

from datetime import datetime
from superdesk import Command, Option, get_resource_service
from superdesk.metadata.item import ITEM_STATE, CONTENT_STATE


class DeleteEvents(Command):
    """Usage:

    honcho run manage.py cp:delete_events -f <file>

    where <file> is a file with event IDs to delete.
    """

    option_list = [
        Option("--file", "-f", default="-"),
    ]

    def run(self, file):
        if file == "-":
            input_file = sys.stdin
        else:
            input_file = open(file, "r")

        events_service = get_resource_service("events")
        events_post_service = get_resource_service("events_post")
        removed_count = 0
        missing_start_time = datetime(2024, 1, 1, 0, 0, 0)

        try:
            for line in input_file:
                _id = line.strip()
                if not _id or not _id.isnumeric():
                    continue
                _id = f"urn:onclusive:{_id}"
                print("ID", _id)
                event = events_service.find_one(req=None, _id=_id.strip())
                if event:
                    update = {
                        "pubstatus": "cancelled",
                        ITEM_STATE: CONTENT_STATE.KILLED,
                    }
                    events_service.patch_in_mongo(event["_id"], update, event)
                    print("patch.")
                else:
                    new_event = {
                        "guid": _id,
                        "pubstatus": "cancelled",
                        ITEM_STATE: CONTENT_STATE.KILLED,
                        "type": "event",
                        "dates": {
                            "start": missing_start_time,
                            "end": missing_start_time,
                            "all_day": True,
                            "tz": "UTC",
                        },
                        "source": "Onclusive",
                    }
                    events_service.post_in_mongo([new_event])
                    events_post_service.post(
                        [
                            {
                                "event": new_event["_id"],
                                "etag": new_event["_etag"],
                                "pubstatus": "cancelled",
                                "update_method": "single",
                            }
                        ]
                    )
                    print("post.")
                removed_count += 1
            print(f"Removed {removed_count} events.")
        finally:
            if file != "-":
                input_file.close()
