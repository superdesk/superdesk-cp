import superdesk
import json
import os
import logging


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

    def run(self, filename: str):
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
                    name = (
                        event["name"]
                        if type(event["name"]) is str
                        else event["name"]["en-ca"]
                    )
                    items.append(
                        {
                            "name": name,
                            "parent": self.get_parent(event),
                            "qcode": name,
                            "is_active": True,
                            "subject": self.get_subject(event),
                            "onclusive_ids": event["sourceMeta"][0]["key"]
                            if event.get("sourceMeta")
                            else None,
                        }
                    )
                    if type(event["name"]) is not str:
                        items.append({"translations": {"name": event["name"]}})

                event_types["items"] = items
                event_types["init_version"] += 1
                vocabularies.seek(0)
                vocabularies.truncate()
                json.dump(cvs, vocabularies, indent=4, ensure_ascii=False)
                logging.info("Events types sucessfully updated ")

    def get_subject(self, event):
        if event.get("subject"):
            subj = []
            for i in event["subject"]:
                subj.append(i["name"])
            return subj
        return None

    def get_parent(self, event):
        if event.get("broader"):
            broader = event["broader"][0]["name"]
            if type(broader) is not str and broader.get("en-ca"):
                return broader["en-ca"]
            return broader
