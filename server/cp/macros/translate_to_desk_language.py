# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

import logging
from flask_babel import lazy_gettext
from superdesk import get_resource_service


logger = logging.getLogger(__name__)


def translate_to_desk_language(item, **kwargs):
    """ This macro will set the language of the articles to the Desk language. """

    dest_desk = kwargs.get("dest_desk_id")

    if dest_desk:
        desk = get_resource_service("desks").find_one(req=None, _id=dest_desk)
    else:
        desk = kwargs.get("desk")

    if desk and desk.get("desk_language"):
        item["language"] = desk.get("desk_language")

    return item


name = "Translate To Desk Language"
label = lazy_gettext("Translate To Desk Language")
callback = translate_to_desk_language
access_type = "backend"
action_type = "direct"
