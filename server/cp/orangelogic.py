
import os
import math
import pytz
import requests
import superdesk
import mimetypes

from datetime import datetime
from urllib.parse import urljoin
from flask import current_app as app, json
from requests.exceptions import HTTPError
from superdesk.utils import ListCursor
from superdesk.timer import timer
from superdesk.utc import local_to_utc
from superdesk.search_provider import SearchProvider


AUTH_API = '/API/Authentication/v1.0/Login'
SEARCH_API = '/API/Search/v3.0/search'

TIMEOUT = (5, 25)
DATE_FORMAT = 'u'


class OrangelogicListCursor(ListCursor):

    def __init__(self, docs, count):
        super().__init__(docs)
        self._count = count

    def __len__(self):
        return len(self.docs)

    def count(self, **kwargs):
        return self._count


class OrangelogicSearchProvider(SearchProvider):

    label = 'Orange Logic'

    TZ = 'America/Toronto'
    URL = 'https://canadianpress3227prod.orangelogic.com/'

    MEDIA_TYPE_MAP = {
        'image': 'picture',
        'video': 'video',
        'audio': 'audio',
        'package': 'composite',
        'graphic': 'graphic',
        'story': 'composite',
    }

    RENDITIONS_MAP = {
        'baseImage': 'Path_TR1',
        'viewImage': 'Path_TR4',
        'thumbnail': 'Path_TR7',
        'webHigh': 'Path_WebHigh',
    }

    def __init__(self, provider):
        super().__init__(provider)
        self.sess = requests.Session()
        self.token = None
        self.config = provider.get('config') or {}
        app.config.setdefault('ORANGELOGIC_URL', self.URL)

    def _request(self, api, method='GET', **kwargs):
        url = urljoin(app.config['ORANGELOGIC_URL'], api)
        resp = self.sess.request(method, url, params=kwargs, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp

    def _login(self):
        resp = self._request(AUTH_API, method='POST',
                             Login=self.config.get('username'),
                             Password=self.config.get('password'),
                             format='json')
        self.token = resp.json()['APIResponse']['Token']

    def _auth_request(self, api, **kwargs):
        repeats = 2
        while repeats > 0:
            if not self.token:
                self._login()
            try:
                kwargs['token'] = self.token
                return self._request(api, **kwargs)
            except HTTPError:
                self.token = None
                repeats -= 1
                if repeats == 0:
                    raise

    def find(self, query, params=None):
        if params is None:
            params = {}

        size = int(query.get('size', 50))
        page = math.ceil((int(query.get('from', 0)) + 1) / size)

        kwargs = {
            'pagenumber': page,
            'countperpage': size,
            'fields': ','.join([
                'Title',
                'SystemIdentifier',
                'MediaNumber',
                'Caption',
                'CaptionShort',
                'EditDate',
                'MediaDate',
                'CreateDate',
                'GlobalEditDate',
                'MediaType',
                'Path_TR1',
                'Path_TR4',
                'Path_TR7',
                'Path_WebHigh',
                'Photographer',
                'PhotographerFastId',
                'copyright',
            ]),
            'Sort': 'Newest',
            'format': 'json',
            'DateFormat': 'u',
        }

        query_components = {}

        try:
            query_components['Text'] = query['query']['filtered']['query']['query_string']['query']
        except (KeyError, TypeError):
            pass

        if params:
            if params.get('mediaTypes'):
                selected = [k for k, v in params['mediaTypes'].items() if v]
                if selected:
                    query_components['MediaType'] = '({})'.format(' OR '.join(selected))

        kwargs['query'] = ' '.join(['{}:{}'.format(key, val) for key, val in query_components.items() if val])

        if params:
            for param, op in (('from', '>:'), ('to', '<:')):
                if params.get(param):
                    kwargs['query'] = '{} MediaDate{}{}'.format(kwargs['query'], op, params[param]).strip()

        with timer('orange'):
            resp = self._auth_request(SEARCH_API, **kwargs)
            data = resp.json()

        with open('/tmp/resp.json', mode='w') as out:
            out.write(json.dumps(data, indent=2))

        items = []
        for item in data['APIResponse']['Items']:
            guid = item['MediaNumber']
            items.append({
                '_id': guid,
                'guid': guid,
                'type': self.MEDIA_TYPE_MAP[item['MediaType'].lower()],
                'source': item['PhotographerFastId'],
                'slugline': item['Title'],
                'headline': item['CaptionShort'],
                'byline': item['Photographer'],
                'copyrightholder': item['copyright'],
                'description_text': item['Caption'],
                'firstcreated': self.parse_datetime(item['CreateDate']),
                'versioncreated': self.parse_datetime(item['GlobalEditDate']),
                'renditions': {
                    key: rendition(item[path])
                    for key, path in self.RENDITIONS_MAP.items()
                    if item.get(path) and item[path].get('URI')
                },
            })

        return OrangelogicListCursor(items, data['APIResponse']['GlobalInfo']['TotalCount'])

    def parse_datetime(self, value):
        local = datetime.strptime(value, '%m/%d/%Y %H:%M:%S %p')
        return local_to_utc(self.TZ, local)

    def fetch(self, guid):
        return


def rendition(data):
    rend = {
        'href': data['URI'],
        'mimetype': mimetypes.guess_type(data['URI'])[0],
    }

    if data.get('Width'):
        rend['width'] = int(data['Width'])

    if data.get('Height'):
        rend['height'] = int(data['Height'])

    return rend


def init_app(app):
    superdesk.register_search_provider('orangelogic', provider_class=OrangelogicSearchProvider)
