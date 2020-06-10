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
from superdesk import get_resource_service


logger = logging.getLogger(__name__)


def set_item_language(item, **kwargs):
    """ This macro will set the language of the articles to the Desk language. """

    dest_desk_id = kwargs.get('desk').get('_id')
    item_source = item.get('source')

    if dest_desk_id and item_source:
        desk = get_resource_service('desks').find_one(req=None, _id=dest_desk_id)
        if item_source == 'THE CANADIAN PRESS':
            return
        elif desk.get('desk_language') == 'fr-CA':
            item['language'] = 'fr-CA'
        elif desk.get('desk_language') == 'en-CA' and item.get('language') != 'fr-CA':
            item['language'] = 'en-CA'
    elif kwargs['desk'].get('desk_language') == 'fr-CA':
        item['language'] = 'fr-CA'

name = 'Set Item Language'
label = name
callback = set_item_language
access_type = 'frontend'
action_type = 'direct'
