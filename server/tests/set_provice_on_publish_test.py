import flask
import unittest
import superdesk

from tests.mock import resources
from unittest.mock import patch
from cp.set_province_on_publish import set_province_on_publish


class PublishSignalTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.app = flask.Flask(__name__)
        self.app.config.update(
            {
                "VERSION": "version",
                "DEFAULT_LANGUAGE": "en",
            }
        )
        self.app.app_context().push()

    def test_publish_signal(self):
        with patch.dict(superdesk.resources, resources):
            item = {
                "dateline": {
                    "source": "CP",
                    "date": "2022-12-14T13:06:39+0000",
                    "located": {
                        "dateline": "city",
                        "country_code": "CA",
                        "tz": "America/Toronto",
                        "city_code": "Toronto",
                        "state_code": "08",
                        "state": "Ontario",
                        "city": "Toronto",
                        "country": "Canada",
                        "code": "6167865",
                        "scheme": "geonames",
                        "place": {
                            "scheme": "geonames",
                            "code": "6167865",
                            "name": "Toronto",
                            "state": "Ontario",
                            "region": "",
                            "country": "Canada",
                            "state_code": "08",
                            "region_code": "",
                            "country_code": "CA",
                            "continent_code": "NA",
                            "feature_class": "P",
                            "location": {"lat": 43.70011, "lon": -79.4163},
                            "tz": "America/Toronto",
                        },
                    },
                },
            }

            updates = {}

            set_province_on_publish(None, item, updates, foo=1)
            set_province_on_publish(None, item, updates, foo=1)

            assert "subject" in item
            regions = [
                subj for subj in item["subject"] if subj.get("scheme") == "regions"
            ]
            assert 1 == len(regions)
            assert "Ontario" == regions[0]["name"]
            assert "ON" == regions[0]["qcode"]

            assert "subject" in updates
            assert 1 == len(updates["subject"])
            assert item["subject"] == updates["subject"]

    def test_empty_located(self):
        set_province_on_publish(None, {"dateline": {"located": None}}, {}, bar=1)
