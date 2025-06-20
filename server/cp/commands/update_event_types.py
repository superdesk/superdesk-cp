import json
import os
import logging

import click

from superdesk.commands import cli


@cli.command("cp:update_event_types")
@click.option(
    "-f",
    "--file",
    "filename",
    required=True,
    help="Use a local json file to update event_types",
)
def cli_update_event_types(filename: str) -> None:
    """Update event_types in Vocabularies

    Command Examples:
       $ python manage.py cp:update_event_types --file /tmp/iptc-media-topcs.json
    """

    with open(
        os.path.join(os.path.dirname(__file__), "../..", "data", "vocabularies.json"),
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
                assert type(name) is str, name
                obj = {
                    "name": name,
                    "parent": _get_parent(event),
                    "qcode": name,
                    "is_active": True,
                    "subject": _get_subject(event),
                    "onclusive_ids": (
                        event["sourceMeta"][0]["key"]
                        if event.get("sourceMeta")
                        else None
                    ),
                }
                if type(event["name"]) is not str:
                    obj["translations"] = {
                        "name": {
                            key.replace("ca", "CA"): val
                            for key, val in event["name"].items()
                        }
                    }
                items.append(obj)
            event_types["items"] = items
            event_types["init_version"] += 1
            vocabularies.seek(0)
            vocabularies.truncate()
            json.dump(cvs, vocabularies, indent=4, ensure_ascii=False)
            logging.info("Events types sucessfully updated ")


def _get_subject(event):
    if event.get("subject"):
        subj = []
        for i in event["subject"]:
            subj.append(i["name"])
        return subj
    return None


def _get_parent(event):
    if event.get("broader"):
        broader = event["broader"][0]["name"]
        if type(broader) is not str and broader.get("en-ca"):
            return broader["en-ca"]
        return broader
