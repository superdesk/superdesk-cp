
import os
import math
import pytz
import logging
import requests
import superdesk

from datetime import datetime
from urllib.parse import urljoin
from flask import current_app as app, json
from superdesk.utils import ListCursor
from superdesk.search_provider import SearchProvider


AUTH_API = '/API/Authentication/v1.0/Login'
SEARCH_API = '/API/Search/v3.0/search'

TIMEOUT = (5, 25)
DATE_FORMAT = 'u'


logging.basicConfig()
logger = logging.getLogger(__name__)


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
    }

    def __init__(self, provider):
        super().__init__(provider)
        self.sess = requests.Session()
        self.token = os.environ.get('ORANGELOGIC_TOKEN')
        self.config = provider.get('config') or {}
        app.config.setdefault('ORANGELOGIC_URL', self.URL)
        self.sess.cookies.set('CP1-Session', 'teisjyoygrznnvsrefvb4wfn')
        self.sess.cookies.set('CP1-Session-Alt', 'teisjyoygrznnvsrefvb4wfn')
        self.token = 'foo'

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
                'MediaDate',
                'CreateDate',
                'GlobalEditDate',
                'MediaType',
                'Path_TR1',
                'Path_TR7',
                'Path_WebHigh',
                'Path_WebLow',
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
                'source': item['PhotographerFastId'],
                'slugline': item['Title'],
                'headline': item['CaptionShort'],
                'byline': item['Photographer'],
                'copyrightholder': item['copyright'],
                'description_text': item['Caption'],
                'firstcreated': self.parse_datetime(item['CreateDate']),
                'versioncreated': self.parse_datetime(item['MediaDate'] or item['GlobalEditDate']),
                'renditions': {
                    'thumbnail': {
                        'href': thumb['URI'],
                        'width': int(thumb['Width']),
                        'height': int(thumb['Height']),
                        'mimetype': 'image/jpeg',
                    },
                    'viewImage': {
                        'href': view['URI'],
                        'width': int(view['Width']),
                        'height': int(view['Height']),
                        'mimetype': 'image/jpeg',
                    },
                },
            })

        return OrangelogicListCursor(items, data['APIResponse']['GlobalInfo']['TotalCount'])
        return items

    def parse_datetime(self, value):
        local = datetime.strptime(value, '%m/%d/%Y %H:%M:%S %p')
        return local.replace(tzinfo=pytz.UTC)


def init_app(app):
    superdesk.register_search_provider('orangelogic', provider_class=OrangelogicSearchProvider)
