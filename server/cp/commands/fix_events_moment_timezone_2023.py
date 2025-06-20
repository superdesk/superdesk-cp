import click

from datetime import datetime, timedelta
from quart import current_app as app

from superdesk import get_resource_service
from superdesk.commands import cli


@cli.command("cp:fix_event_dates_2023")
@click.option("-s", "--start", default="2023-03-12T07:00:00+00:00")
@click.option("-e", "--end", default="2023-11-05T07:00:00+00:00")
@click.option("-o", "--offset", default="-1")
async def cli_fix_event_dates_2023(start: str, end: str, offset: str) -> None:
    """Fix events affected by moment timezone issue

    which were saved during summer time using the offset of winter time (or vice versa in Australia).
    """

    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    offset_td = timedelta(hours=int(offset))
    europe_start = datetime.fromisoformat("2023-03-26T01:00:00+00:00")
    europe_end = datetime.fromisoformat("2023-10-29T01:00:00+00:00")

    app.logger.info(
        "Updating events from %s to %s",
        start_dt,
        end_dt,
    )

    query = {
        "dates.start": {
            "$gte": start_dt,
            "$lt": end_dt,
        },
        "dates.end": {"$gte": start_dt, "$lt": end_dt},
        "$or": [  # we had a fix in production for a bit, but later reverted
            {"_created": {"$lt": datetime.fromisoformat("2023-03-30T09:30:00+00:00")}},
            {"_created": {"$gt": datetime.fromisoformat("2023-03-30T18:30:00+00:00")}},
        ],
        "ingest_provider": {"$exists": 0},  # ignore ingested events
        "dates.tz": {
            "$nin": [
                "America/Regina",
                "America/Whitehorse",
            ]
        },
    }

    updated_count = 0
    events_service = get_resource_service("events")
    async for event in await events_service.get_from_mongo_async(
        req=None, lookup=query
    ):
        dates = event["dates"].copy()
        if dates.get("tz") and "Europe" in dates.get("tz"):
            if dates["start"] < europe_start or dates["end"] > europe_end:
                continue
        if dates["start"] > start_dt:
            dates["start"] += offset_td
        if dates["end"] < end_dt:
            dates["end"] += offset
        updates = {"dates": dates}

        await events_service.update_async(event["_id"], updates, event)
        await app.on_updated_events.call_async(updates, event)  # type: ignore[attr-defined]
        app.logger.info("Event updated: %s", event.get("name") or event.get("_id"))
        updated_count += 1

    app.logger.info("Updated %d events", updated_count)
