import logging
import aiohttp

from quart import current_app as app
from urllib.parse import urljoin

from apps.tasks import send_to
from superdesk import get_resource_service
from superdesk.lock import lock, unlock, touch
from superdesk.text_utils import get_text
from superdesk.celery_app import celery
from superdesk.editor_utils import Editor3Content
from superdesk.metadata.item import CONTENT_STATE


logger = logging.getLogger(__name__)

ULTRAD_ID = "ultrad_id"
ULTRAD_URL = "https://pc-trad.herokuapp.com/cms/"
ULTRAD_TIMEOUT = aiohttp.ClientTimeout(total=15, connect=3)

IN_PROGRESS_STATES = [
    CONTENT_STATE.ROUTED,
    CONTENT_STATE.FETCHED,
    CONTENT_STATE.PROGRESS,
    CONTENT_STATE.SUBMITTED,
]


class UltradException(RuntimeError):
    pass


def get_headers():
    return {"Accept": "application/json", "x-ultrad-auth": app.config["ULTRAD_AUTH"]}


async def upload_document(item: dict) -> str | None:
    item_name = item.get("headline") or item.get("slugline")
    if not item_name or not item.get("body_html"):
        return None

    payload = {
        "lang": {
            "fromLang": "en",
            "toLang": "fr",
        },
        "name": item_name,
        "state": "new",
        "text": {
            "original": get_text(item["body_html"]),
        },
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            ULTRAD_URL, json=payload, headers=get_headers(), timeout=ULTRAD_TIMEOUT
        ) as resp:
            raise_for_resp_error(resp)
            data = await get_json(resp)
    return data["_id"]


async def get_document(ultrad_id: str) -> dict:
    url = urljoin(ULTRAD_URL, ultrad_id)
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url, headers=get_headers(), timeout=ULTRAD_TIMEOUT
        ) as resp:
            raise_for_resp_error(resp)
            return await get_json(resp)


def raise_for_resp_error(resp: aiohttp.ClientResponse) -> None:
    try:
        resp.raise_for_status()
    except aiohttp.ClientResponseError:
        logger.error(
            "HTTP error %d: %s when doing %s on %s",
            resp.status,
            resp.text,
            resp.method,
            resp.url,
        )
        raise UltradException()


async def get_json(resp: aiohttp.ClientResponse) -> dict:
    try:
        return await resp.json()
    except ValueError:
        logger.error('error when parsing ultrad response "%s"', resp.text)
        raise UltradException()


@celery.task(soft_time_limit=300)
async def sync():
    lock_name = "ultrad"
    if not lock(lock_name):
        logger.info("lock taken %s", lock_name)
        return
    try:
        todo_stages_cursor = await get_resource_service("stages").get_async(
            req=None, lookup={"name": app.config["ULTRAD_TODO_STAGE"]}
        )
        if not await todo_stages_cursor.count():
            logger.warning(
                "ultrad todo stage not found, name=%s", app.config["ULTRAD_TODO_STAGE"]
            )
            return
        async for todo_stage in todo_stages_cursor:
            desk = await get_resource_service("desks").find_one_async(
                req=None, _id=todo_stage["desk"]
            )
            if not desk:
                logger.warning(
                    "ultrad desk not found for stage desk=%s", todo_stage["desk"]
                )
                continue
            lookup = {"task.stage": todo_stage["_id"]}
            items_cursor = await get_resource_service("archive").get_async(
                req=None, lookup=lookup
            )
            logger.info(
                "checking %d items on ultrad on desk %s",
                await items_cursor.count(),
                desk["name"],
            )
            async for item in items_cursor:
                if not touch(lock_name, expire=300):
                    logger.warning("lost lock %s", lock_name)
                    break
                if item.get("lock_user") and item.get("lock_session"):
                    logger.info("skipping locked item guid=%s", item["guid"])
                    continue
                if item["state"] not in IN_PROGRESS_STATES:
                    logger.info(
                        "ignore item due to state guid=%s state=%s",
                        item["guid"],
                        item["state"],
                    )
                    continue
                try:
                    ultrad_id = item["extra"][ULTRAD_ID]
                except KeyError:
                    continue
                try:
                    ultrad_doc = await get_document(ultrad_id)
                except UltradException:
                    continue
                if ultrad_doc["state"] == "revised":
                    try:
                        updated = item.copy()
                        updated["body_html"] = ultrad_doc["text"]["edited"]
                    except KeyError:
                        logger.info(
                            "no content in ultrad for item guid=%s ultrad_id=%s",
                            item["guid"],
                            ultrad_id,
                        )
                        continue
                    logger.info(
                        "updating item from ultrad guid=%s ultrad_id=%s",
                        item["guid"],
                        ultrad_id,
                    )
                    editor = Editor3Content(updated)
                    editor._create_state_from_html(updated["body_html"])
                    editor.update_item()
                    send_to(
                        updated, desk_id=desk["_id"], stage_id=desk["working_stage"]
                    )
                    updates = {
                        "task": updated["task"],
                        "body_html": updated["body_html"],
                        "fields_meta": updated["fields_meta"],
                    }
                    # don't use patch, it assumes there is a user
                    await get_resource_service("archive").update_async(
                        item["_id"], updates, item
                    )
                    await get_resource_service("archive").on_updated_async(
                        updates, item
                    )
                else:
                    logger.debug(
                        "skip updating item guid=%s ultrad_id=%s state=%s",
                        item["guid"],
                        ultrad_id,
                        ultrad_doc["state"],
                    )
    finally:
        unlock(lock_name)
