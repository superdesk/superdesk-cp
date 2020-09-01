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
import superdesk
from flask_babel import _


logger = logging.getLogger(__name__)


def find_name_item(cv_id, name):
    cv = superdesk.get_resource_service('vocabularies').find_one(req=None, _id=cv_id)
    if not cv or not cv.get('items'):
        return
    for item in cv['items']:
        if item.get('name') == name.strip():
            return item


def callback(item, **kwargs):
    """ This macro will set the language of the articles to the Desk language. """
    rule = kwargs.get('rule')
    if rule:
        service, destination = rule['name'].split(':')
        mapping = {
            'distribution': service,
            'destinations': destination,
        }

        for cv_id, name in mapping.items():
            subject = find_name_item(cv_id, name)
            if subject:
                item.setdefault('subject', []).append({
                    'name': subject['name'],
                    'qcode': subject['qcode'],
                    'scheme': cv_id,
                })
            else:
                logger.error('no item found in vocabulary %s with name %s', cv_id, name.strip())
    return item


name = 'auto-routing'
label = _('AutoRouting macro')
access_type = 'backend'
action_type = 'direct'
