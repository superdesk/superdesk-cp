import superdesk
import json
import os
from typing import Optional


class UpdateEventTypesCommand(superdesk.Command):
    """Update event_types in Vocabularies"""

    """
     Command Examples:
        $ python manage.py cp:update_event_types --file /tmp/iptc-media-topcs.json"""

    option_list = [
        superdesk.Option(
            "--file",
            "-f",
            dest="filename",
            required=True,
            help="Use a local json file to update event_types",
        ),
    ]

    def run(self, filename: Optional[str]):
        print()
        with open(
            os.path.join(
                os.path.dirname(__file__), "../..", "data", "vocabularies.json"
            ),
            "r+",
        ) as vocabularies:
            cvs = json.load(vocabularies)
            event_types = next((cv for cv in cvs if cv.get("_id") == "event_types"))

            with open(filename) as updated_file:
                updated_event_types = json.load(updated_file)
                items = []
                for event in updated_event_types["eventTypes"]:
                    items.append(
                        {
                            "name": event["name"],
                            "parent": event["broader"][0]["name"]
                            if event.get("broader")
                            else None,
                            "qcode": event["name"],
                            "is_active": True,
                        }
                    )
                event_types["items"] = items
                event_types["init_version"] += 1
                vocabularies.seek(0)
                vocabularies.truncate()
                json.dump(cvs, vocabularies, indent=4, ensure_ascii=False)
