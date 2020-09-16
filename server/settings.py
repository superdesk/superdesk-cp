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

from flask import json
from pathlib import Path
from superdesk.default_settings import (
    strtobool, env, SERVER_URL, CORE_APPS as _core_apps,
    CELERY_BEAT_SCHEDULE, timedelta,
)


ABS_PATH = str(Path(__file__).resolve().parent)

init_data = Path(ABS_PATH) / 'data'
if init_data.exists():
    INIT_DATA_PATH = init_data

INSTALLED_APPS = [
    'apps.languages',
    'planning',
    'analytics',

    'superdesk.auth.saml',
    'superdesk.macros.imperial',

    'cp.orangelogic',
    'cp.ingest',
    'cp.output',
    'cp.ultrad',
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

SECRET_KEY = env('SECRET_KEY', os.urandom(32))

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

DEFAULT_LANGUAGE = 'en-CA'

ARCHIVE_AUTOCOMPLETE = True
ARCHIVE_AUTOCOMPLETE_DAYS = 2

# special characters that are disallowed
DISALLOWED_CHARACTERS = ['!', '#', '$', '%', '&', '"', '(', ')', '*', '+', ',', '.', '/', ':', ';', '<', '=',
                         '>', '?', '@', '[', ']', '\\', '^', '_', '`', '{', '|', '}', '~']

TANSA_PROFILES = {
    'en-CA': 1108,
    'fr-CA': 1108,
}

GENERATE_SHORT_GUID = True

DEFAULT_URGENCY_VALUE_FOR_INGESTED_ARTICLES = 5

# publishing of associated and related items
PUBLISH_ASSOCIATED_ITEMS = True

# This value gets injected into NewsML 1.2 and G2 output documents.
NEWSML_PROVIDER_ID = 'thecanadianpress.com'
ORGANIZATION_NAME = env('ORGANIZATION_NAME', 'THE CANADIAN PRESS')
ORGANIZATION_NAME_ABBREVIATION = env('ORGANIZATION_NAME_ABBREVIATION', 'CP')

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

# if there is picture/audio/video content type defined in data/content_types
# use that
with open(os.path.join(str(INIT_DATA_PATH), 'content_types.json')) as _content_types_file:
    content_types = json.load(_content_types_file)
    for content_type in content_types:
        if content_type['_id'] in SCHEMA:
            SCHEMA[content_type['_id']] = content_type['schema']
            EDITOR[content_type['_id']] = content_type['editor']


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
}


# saml auth
USER_EXTERNAL_CREATE = True
USER_EXTERNAL_DESK = "CP New User"
USER_EXTERNAL_USERNAME_STRIP_DOMAIN = True
SAML_LABEL = env('SAML_LABEL', 'SSO')
SAML_BASE_PATH = env('SAML_PATH', os.path.join(ABS_PATH, 'saml'))
if SERVER_URL == 'http://localhost:5000/api':
    SAML_PATH = os.path.join(SAML_BASE_PATH, 'localhost')
elif SERVER_URL == 'https://scp-master.test.superdesk.org/api':
    SAML_PATH = os.path.join(SAML_BASE_PATH, 'test')
elif SERVER_URL == 'https://cp-uat-api.superdesk.pro/api':
    SAML_PATH = os.path.join(SAML_BASE_PATH, 'uat')
else:
    SAML_PATH = os.path.join(SAML_BASE_PATH, 'prod')

# disable db auth if saml is configured properly
if os.path.exists(os.path.join(SAML_PATH, 'certs')) and not strtobool(env('SUPERDESK_AUTH', '')):
    CORE_APPS = [app for app in _core_apps if app != 'apps.auth.db']


HIGHCHARTS_LICENSE_ID = env('HIGHCHARTS_LICENSE_ID', '')
HIGHCHARTS_LICENSE_TYPE = 'OEM'
HIGHCHARTS_LICENSEE = 'Sourcefabric Ventures s.r.o.'
HIGHCHARTS_LICENSEE_CONTACT = 'tech@sourcefabric.org'
HIGHCHARTS_LICENSE_CUSTOMER_ID = '2'
HIGHCHARTS_LICENSE_EXPIRY = 'Perpetual'

AP_INGEST_DEBUG = strtobool(env('AP_INGEST_DEBUG', 'false'))

GEONAMES_USERNAME = env('GEONAMES_USERNAME', 'andrew.lundy')
GEONAMES_FEATURE_CLASSES = ['P']
GEONAMES_SEARCH_STYLE = 'full'

DEFAULT_GENRE_VALUE_FOR_MANUAL_ARTICLES = None

OVERRIDE_EDNOTE_TEMPLATE = 'CORRECTS'

USER_USERNAME_PATTERN = '[\w]+'

FTP_TIMEOUT = int(env('FTP_TIMEOUT', 10))

CONTENT_EXPIRY_MINUTES = int(env('CONTENT_EXPIRY_MINUTES', 0))
INGEST_EXPIRY_MINUTES = int(env('INGEST_EXPIRY_MINUTES', 2 * 24 * 60))  # 2d
PUBLISHED_CONTENT_EXPIRY_MINUTES = int(env('PUBLISHED_CONTENT_EXPIRY_MINUTES', 60 * 24 * 60))  # 60d
AUDIT_EXPIRY_MINUTES = int(env('AUDIT_EXPIRY_MINUTES', 60 * 24 * 7))  # 7d
PUBLISH_QUEUE_EXPIRY_MINUTES = int(env('PUBLISH_QUEUE_EXPIRY_MINUTES', 60 * 24 * 7))  # 7d
ARCHIVED_EXPIRY_MINUTES = int(env('ARCHIVED_EXPIRY_MINUTES', 60 * 24 * 60))  # 60d

# disable use of XMP for photo assignments
PLANNING_USE_XMP_FOR_PIC_ASSIGNMENTS = False

# ultrad auth header
ULTRAD_AUTH = env('ULTRAD_AUTH', '')
ULTRAD_DESK = 'French'
ULTRAD_TODO_STAGE = 'Being translated'
ULTRAD_DONE_STAGE = 'Working Stage'

CELERY_BEAT_SCHEDULE.update({
    'ultrad:sync': {
        'task': 'cp.ultrad.sync',
        'schedule': timedelta(minutes=1),
    },
})
