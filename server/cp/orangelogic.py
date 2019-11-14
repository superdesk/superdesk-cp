
import os
import math
import logging
import requests
import superdesk

from flask import current_app as app, json
from urllib.parse import urljoin
from datetime import datetime
from superdesk.search_provider import SearchProvider
from superdesk.utc import local_to_utc


AUTH_API = '/API/Authentication/v1.0/Login'
SEARCH_API = '/API/Search/v3.0/search'

TIMEOUT = (5, 25)
DATE_FORMAT = 'u'


logging.basicConfig()
logger = logging.getLogger(__name__)


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
    }

    def __init__(self, provider):
        super().__init__(provider)
        self.sess = requests.Session()
        self.token = os.environ.get('ORANGELOGIC_TOKEN')
        self.config = provider.get('config') or {}
        app.config.setdefault('ORANGELOGIC_URL', self.URL)

    def _request(self, api, method='GET', **kwargs):
        url = urljoin(app.config['ORANGELOGIC_URL'], api)
        logging.info('request %s %s', api, json.dumps(kwargs))
        resp = self.sess.request(method, url, params=kwargs, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp

    def _auth_request(self, api, **kwargs):
        if not self.token:
            resp = self._request(AUTH_API, method='POST',
                                 Login=self.config.get('username'),
                                 Password=self.config.get('password'))
            self.token = resp.get('token')
        kwargs['token'] = self.token
        resp = self._request(api, **kwargs)
        return resp

    def find(self, query):
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
                'MediaDate',
                'CreateDate',
                'GlobalEditDate',
                'MediaType',
                'Path_TR1',
                'Path_TR7',
                'Photographer',
                'copyright',
                'Artist',
            ]),
            'Sort': 'Newest',
            'format': 'json',
        }

        try:
            kwargs['query'] = query['query']['filtered']['query']['query_string']['query']
        except (KeyError, TypeError):
            pass

        resp = self._auth_request(SEARCH_API, **kwargs)
        data = resp.json()

        with open('/tmp/resp.json', mode='w') as out:
            out.write(json.dumps(data, indent=2))

        items = []
        for item in data['APIResponse']['Items']:
            guid = item['MediaNumber']
            view = item['Path_TR1']
            thumb = item['Path_TR7']
            items.append({
                '_id': guid,
                'guid': guid,
                'type': self.MEDIA_TYPE_MAP[item['MediaType'].lower()],
                'source': item['Artist'],
                'slugline': item['Title'],
                'headline': item['CaptionShort'],
                'byline': item['Photographer'],
                'copyrightholder': item['copyright'],
                'description_text': item['Caption'],
                'firstcreated': self.parse_datetime(item['CreateDate']),
                'versioncreated': self.parse_datetime(item['GlobalEditDate']),
                'renditions': {
                    'thumbnail': {
                        'href': thumb['URI'],
                        'width': int(thumb['Width']),
                        'height': int(thumb['Height']),
                    },
                    'viewImage': {
                        'href': view['URI'],
                        'width': int(view['Width']),
                        'height': int(view['Height']),
                    },
                },
            })

        return items

    def parse_datetime(self, value):
        local = datetime.strptime(value, '%m/%d/%Y %H:%M:%S %p')
        return local_to_utc(self.TZ, local)


def init_app(app):
    superdesk.register_search_provider('orangelogic', provider_class=OrangelogicSearchProvider)
