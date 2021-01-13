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


def update_translation_metadata_macro(item, **kwargs):
    if item.get('anpa_take_key'):
        item['anpa_take_key'] = ''

    if item.get('correction_sequence'):
        item['correction_sequence'] = 0

    cv = get_resource_service('vocabularies').find_one(req=None, _id='destinations')
    if not cv or not cv.get('items'):
        return

    for value in cv['items']:
        subject = item.get('subject', [])
        is_destination = any(sub for sub in subject if sub.get('name') == 'Presse Canadienne staff')

        if value.get('name') == 'Presse Canadienne staff' and not is_destination:
            item.setdefault('subject', []).append({
                'name': value['name'],
                'qcode': value['qcode'],
                'scheme': 'destinations',
            })

    return item


name = 'Update translation metadata macro'
label = lazy_gettext('Update translation metadata macro')
callback = update_translation_metadata_macro
access_type = 'backend'
action_type = 'interactive'
