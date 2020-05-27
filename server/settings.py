#!/usr/bin/env python
# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014, 2015 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

import os
from pathlib import Path
from superdesk.default_settings import strtobool, env


ABS_PATH = str(Path(__file__).resolve().parent)

init_data = Path(ABS_PATH) / 'data'
if init_data.exists():
    INIT_DATA_PATH = init_data

INSTALLED_APPS = [
    'apps.languages',
    'planning',

    'superdesk.macros.imperial',

    'cp.orangelogic',
    'cp.ingest',
    'cp.output',
]

MACROS_MODULE = 'cp.macros'

RENDITIONS = {
    'picture': {
        'thumbnail': {'width': 220, 'height': 120},
        'viewImage': {'width': 640, 'height': 640},
        'baseImage': {'width': 1400, 'height': 1400},
    },
    'avatar': {
        'thumbnail': {'width': 60, 'height': 60},
        'viewImage': {'width': 200, 'height': 200},
    }
}

WS_HOST = env('WSHOST', '0.0.0.0')
WS_PORT = env('WSPORT', '5100')

LOG_CONFIG_FILE = env('LOG_CONFIG_FILE', 'logging_config.yml')

REDIS_URL = env('REDIS_URL', 'redis://localhost:6379')
if env('REDIS_PORT'):
    REDIS_URL = env('REDIS_PORT').replace('tcp:', 'redis:')
BROKER_URL = env('CELERY_BROKER_URL', REDIS_URL)

SECRET_KEY = env('SECRET_KEY', '')

# Highcharts Export Server - default settings
ANALYTICS_ENABLE_SCHEDULED_REPORTS = strtobool(
    env('ANALYTICS_ENABLE_SCHEDULED_REPORTS', 'true')
)
HIGHCHARTS_SERVER_HOST = env('HIGHCHARTS_SERVER_HOST', 'localhost')
HIGHCHARTS_SERVER_PORT = env('HIGHCHARTS_SERVER_PORT', '6060')

LANGUAGES = [
    {'language': 'en-CA', 'label': 'English', 'source': True, 'destination': True},
    {'language': 'fr-CA', 'label': 'Français', 'source': True, 'destination': True}
]

ARCHIVE_AUTOCOMPLETE = True
ARCHIVE_AUTOCOMPLETE_DAYS = 2

# special characters that are disallowed
DISALLOWED_CHARACTERS = ['!', '#', '$', '%', '&', '"', '(', ')', '*', '+', ',', '.', '/', ':', ';', '<', '=',
                         '>', '?', '@', '[', ']', '\\', '^', '_', '`', '{', '|', '}', '~']

TANSA_PROFILES = {
    'en-CA': 507,
    'fr-CA': 507,
}

GENERATE_SHORT_GUID = True

DEFAULT_URGENCY_VALUE_FOR_INGESTED_ARTICLES = 5

# publishing of associated and related items
PUBLISH_ASSOCIATED_ITEMS = True

# This value gets injected into NewsML 1.2 and G2 output documents.
NEWSML_PROVIDER_ID = 'thecanadianpress.com'
ORGANIZATION_NAME = env('ORGANIZATION_NAME', 'THE CANADIAN PRESS')
ORGANIZATION_NAME_ABBREVIATION = env('ORGANIZATION_NAME_ABBREVIATION', 'CP')

# schema for images, video, audio
SCHEMA = {
    'picture': {
        'slugline': {'required': False},
        'headline': {'required': False},
        'description_text': {'required': True},
        'byline': {'required': False},
        'copyrightnotice': {'required': False},
        'usageterms': {'required': False},
        'ednote': {'required': False},
    },
    'video': {
        'slugline': {'required': False},
        'headline': {'required': False},
        'description_text': {'required': True},
        'byline': {'required': True},
        'copyrightnotice': {'required': False},
        'usageterms': {'required': False},
        'ednote': {'required': False},
    },
}

# editor for images, video, audio
EDITOR = {
    'picture': {
        'headline': {'order': 1, 'sdWidth': 'full'},
        'description_text': {'order': 2, 'sdWidth': 'full', 'textarea': True},
        'byline': {'order': 3, 'displayOnMediaEditor': True},
        'copyrightnotice': {'order': 4, 'displayOnMediaEditor': True},
        'slugline': {'displayOnMediaEditor': True},
        'ednote': {'displayOnMediaEditor': True},
        'usageterms': {'order': 5, 'displayOnMediaEditor': True},
    },
    'video': {
        'headline': {'order': 1, 'sdWidth': 'full'},
        'description_text': {'order': 2, 'sdWidth': 'full', 'textarea': True},
        'byline': {'order': 3, 'displayOnMediaEditor': True},
        'copyrightnotice': {'order': 4, 'displayOnMediaEditor': True},
        'slugline': {'displayOnMediaEditor': True},
        'ednote': {'displayOnMediaEditor': True},
        'usageterms': {'order': 5, 'displayOnMediaEditor': True},
    },
}

SCHEMA['audio'] = SCHEMA['video']
EDITOR['audio'] = EDITOR['video']

# media required fields for upload
VALIDATOR_MEDIA_METADATA = {
    "slugline": {
        "required": False,
    },
    "headline": {
        "required": False,
    },
    "description_text": {
        "required": True,
    },
    "byline": {
        "required": False,
    },
    "copyrightnotice": {
        "required": False,
    },
    "usageterms": {
        "required": False,
    },
}
