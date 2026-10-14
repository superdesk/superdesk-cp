import json
from flask import url_for

from superdesk import get_resource_service


async def test_search_planning_with_es_query(
    prodapi_app_with_data, prodapi_app_with_data_client
):
    """Test searching the Production API / Planning endpoint using raw Elasticsearch query."""

    async with prodapi_app_with_data.test_request_context("/"):
        params = dict(
            sort='[("_id", 1)]',
            source=json.dumps(
                {
                    "query": {
                        "bool": {
                            "filter": [
                                {"term": {"state": "scheduled"}},
                                {"term": {"language": "en-CA"}},
                                {
                                    "range": {
                                        "planning_date": {
                                            "gte": "2019-09-10||/d",
                                            "lte": "2019-09-10||/d",
                                            "time_zone": "America/Toronto",
                                        },
                                    },
                                },
                            ],
                        },
                    },
                }
            ),
            projections=json.dumps(["planning_date", "coverages"]),
        )
        url = url_for("planning|resource", **params)

        resp = await prodapi_app_with_data_client.get(url)
        resp_data = json.loads((await resp.get_data()).decode("utf-8"))

        assert resp_data["_meta"]["total"] == 1
        assert sorted(list(resp_data["_items"][0].keys())) == sorted(
            ["_id", "_links", "planning_date", "coverages"]
        )
        assert resp_data["_items"][0]["_id"] == "plan_3"
