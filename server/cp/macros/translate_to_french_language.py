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
from superdesk.errors import StopDuplication


logger = logging.getLogger(__name__)


def translate_to_french_language(item, **kwargs):
    """
    If an article language is English then this macro will set it's language to French.
    """
    not_text_items = ['picture', 'video', 'audio']

    desk_id = kwargs.get('dest_desk_id')
    if not desk_id:
        logger.warning("no destination id specified")
        return
    stage_id = kwargs.get('dest_stage_id')
    if not stage_id:
        logger.warning("no stage id specified")
        return

    new_stage = item.get('task').get('stage')
    desk = get_resource_service('desks').find_one(req=None, _id=desk_id)

    if (new_stage == desk.get('incoming_stage')
            and item.get('type') not in not_text_items
            and (item.get('language') == 'en-CA' or item.get('language') == 'en')):
        translate_service = get_resource_service('translate')

        translate_service._translate_item(item['guid'], 'fr-CA', item['task'], state='routed')

        # no need for further treatment, we stop here internal_destinations workflow
        raise StopDuplication

    return item


name = 'Translate To French Language'
label = lazy_gettext('Translate To French Language')
callback = translate_to_french_language
access_type = 'frontend'
action_type = 'direct'
print(label)
