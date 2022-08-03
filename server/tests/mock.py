import os
import json

from unittest.mock import create_autospec

from superdesk.publish.subscribers import SubscribersService
from superdesk.vocabularies import VocabulariesService
from superdesk.storage.desk_media_storage import SuperdeskGridFSMediaStorage
from apps.archive.news import NewsService
from apps.archive.archive import ArchiveService
from apps.publish.published_item import PublishedItemService
from superdesk.io import IngestService
from superdesk.places.places_autocomplete import PlacesAutocompleteService
from superdesk.geonames import geonames_request, format_geoname_item
from flask import current_app as app
from planning.events.events import EventsService

SEQUENCE_NUMBER = 100

with open(
    os.path.join(os.path.dirname(__file__), "..", "data", "vocabularies.json")
) as f:
    cv_lists = json.load(f)
    cvs = {}
    for cv in cv_lists:
        cvs[cv["_id"]] = cv


def get_cv(req, _id):
    return cvs.get(_id)


def get_rightsinfo(article):
    return {
        "copyrightholder": "copyrightholder",
        "copyrightnotice": "copyrightnotice",
        "usageterms": "usageterms",
    }


def get_place(geoname_id, language="en"):
    assert geoname_id
    params = [
        ("geonameId", geoname_id),
        ("lang", language),
        ("style", app.config.get("GEONAMES_SEARCH_STYLE", "full")),
    ]
    json_data = geonames_request("getJSON", params)
    return format_geoname_item(json_data)


class Resource:
    def __init__(self, service):
        self.service = service


subscriber_service = create_autospec(SubscribersService)
subscriber_service.generate_sequence_number.return_value = SEQUENCE_NUMBER

vocabularies_service = create_autospec(VocabulariesService)
vocabularies_service.find_one.side_effect = get_cv
vocabularies_service.get_rightsinfo.side_effect = get_rightsinfo

news_service = create_autospec(NewsService)
ingest_service = create_autospec(IngestService)
archive_service = create_autospec(ArchiveService)
published_service = create_autospec(PublishedItemService)

media_storage = create_autospec(SuperdeskGridFSMediaStorage)

ingest_service.find_one.return_value = None
archive_service.find_one.return_value = None

places_autocomplete_service = create_autospec(PlacesAutocompleteService)
places_autocomplete_service.get_place.side_effect = get_place

event_service = create_autospec(EventsService)
event_service.find_one.return_value = None

resources = {
    "news": Resource(news_service),
    "ingest": Resource(ingest_service),
    "archive": Resource(archive_service),
    "published": Resource(published_service),
    "subscribers": Resource(subscriber_service),
    "vocabularies": Resource(vocabularies_service),
    "places_autocomplete": Resource(places_autocomplete_service),
    "events": Resource(event_service),
}
