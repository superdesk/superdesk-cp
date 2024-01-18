from superdesk.publish.formatters.ninjs_formatter import (
    NINJSFormatter,
    filter_empty_vals,
    get_locale_name,
)


def format_cv_item(item, language):
    """Format item from controlled vocabulary for output."""
    if item.get("scheme") == "subject":

        return filter_empty_vals(
            {
                "code": item.get("qcode"),
                "name": get_locale_name(item, language),
                "scheme": "http://cv.iptc.org/newscodes/mediatopic/",
            }
        )
    else:

        return filter_empty_vals(
            {
                "code": item.get("qcode"),
                "name": get_locale_name(item, language),
                "scheme": item.get("scheme"),
            }
        )


class CPNINJSFormatter(NINJSFormatter):
    type = "cpninjs"
    name = "CP NINJS"

    def _transform_to_ninjs(self, article, subscriber, recursive=True):
        ninjs = super()._transform_to_ninjs(article, subscriber, recursive=recursive)

        if (
            article.get("subject")
            or article.get("organisation")
            or article.get("place")
            or article.get("event")
            or article.get("person")
        ):
            combined_subjects = (
                self._get_subject(article)
                + self._get_organisation(article)
                + self._get_place(article)
                + self._get_event(article)
                + self._get_person(article)
            )
            ninjs["subject"] = combined_subjects

        return ninjs

    def _get_subject(self, article):
        """Get subject list for article."""
        return [
            format_cv_item(item, article.get("language", ""))
            for item in article.get("subject", [])
        ]

    #  Updated Code here to fetch Organisations from Article
    def _get_organisation(self, article):
        return [
            format_cv_item(item, article.get("language", ""))
            for item in article.get("organisation", [])
        ]

    #  Updated Code here to fetch Places from Article
    def _get_place(self, article):
        """Get place list for article."""
        return [
            format_cv_item(item, article.get("language", ""))
            for item in article.get("place", [])
        ]

    #  Updated Code here to fetch Events from Article
    def _get_event(self, article):
        """Get event list for article."""
        return [
            format_cv_item(item, article.get("language", ""))
            for item in article.get("event", [])
        ]

    #  Updated Code here to fetch Person from Article
    def _get_person(self, article):
        """Get person list for article."""
        return [
            format_cv_item(item, article.get("language", ""))
            for item in article.get("person", [])
        ]
