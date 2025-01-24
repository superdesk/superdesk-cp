from superdesk.signals import item_publish
from settings import DEFAULT_AUTHOR_EN, DEFAULT_AUTHOR_FR
import superdesk


def set_byline_on_publish(sender, item, updates, **kwargs):
    updated = item.copy()
    updated.update(updates)

    if updated.get("byline"):
        return

    if not updated.get("authors"):
        language = updated.get("language", "en-CA")
        default_author_username = (
            DEFAULT_AUTHOR_EN if language == "en-CA" else DEFAULT_AUTHOR_FR
        )

        users_service = superdesk.get_resource_service("users")
        default_user = users_service.find_one(
            req=None, username=default_author_username
        )

        if not default_user:
            raise ValueError(
                f"Default user '{default_author_username}' not found in the database."
            )

        byline = default_user.get("username", "Unknown User")
        default_email = default_user.get("email", "contact@cp.ca")

        item["byline"] = updates["byline"] = byline
        item["authors"] = updates["authors"] = [
            {
                "name": byline,
                "email": default_email,
            }
        ]
        return

    byline = ", ".join(
        [get_author_name(author) for author in updated.get("authors", [])]
    )
    item["byline"] = updates["byline"] = byline

    for author in updated.get("authors", []):
        author["email"] = fetch_author_email(author)


def get_author_name(author) -> str:
    return author.get("sub_label") or author.get("name")


def fetch_author_email(author):
    """
    Fetch the email for the author.
    """
    if "user" in author:
        user_info = author["user"]
        if isinstance(user_info, dict) and "email" in user_info:
            return user_info["email"]
    return author.get("email", "")


def init_app(app):
    item_publish.connect(set_byline_on_publish)
