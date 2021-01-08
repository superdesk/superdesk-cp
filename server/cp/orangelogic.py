
import math
import logging
import requests
import superdesk
import mimetypes

import cp

from pytz import UTC
from datetime import datetime
from urllib.parse import urljoin
from flask import current_app as app, json
from requests.exceptions import HTTPError
from superdesk.utils import ListCursor
from superdesk.timer import timer
from superdesk.utc import local_to_utc
from superdesk.search_provider import SearchProvider
from superdesk.io.commands.update_ingest import update_renditions
from superdesk.media.image import get_meta_iptc, get_meta

from cp.utils import parse_xmp
from cp.ingest.parser.ap import append_matching_subject


AUTH_API = '/API/Authentication/v1.0/Login'
SEARCH_API = '/API/Search/v3.0/search'
DOWNLOAD_API = '/htm/GetDocumentAPI.aspx'

TIMEOUT = (5, 10)
DATE_FORMAT = 'u'

IPTC_SOURCE_MAPPING = {
    'AP Third Party': 'Unknown AP',
}

COUNTRY_MAPPING = {
    'CHN': 'China',
}


tokens = {}
sess = requests.Session()
logger = logging.getLogger(__name__)


def get_api_sort(sort):
    if sort == {'versioncreated': 'asc'}:
        return 'Oldest first'
    else:
        return 'Newest first'


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
        'original': 'Path_TR1',
        'baseImage': 'Path_TR1',
        'viewImage': 'Path_TR7',
        'thumbnail': 'Path_TR7',
        'webHigh': 'Path_WebHigh',
    }

    FIELDS = [
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
        'MediaEncryptedIdentifier',
    ]

    def __init__(self, provider):
        super().__init__(provider)
        self.config = provider.get('config') or {}
        self.url = app.config.get('ORANGELOGIC_URL') or self.URL

    def _url(self, path):
        return urljoin(self.url, path)

    def _request(self, api, method='GET', **kwargs):
        url = self._url(api)
        resp = sess.request(method, url, params=kwargs, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp

    def _login(self):
        with timer('orange.login'):
            resp = self._request(
                AUTH_API,
                method='POST',
                Login=self.config.get('username'),
                Password=self.config.get('password'),
                format='json',
            )
        tokens[self.config['username']] = resp.json()['APIResponse']['Token']

    def _auth_request(self, api, **kwargs):
        repeats = 2
        while repeats > 0:
            if not self.token:
                self._login()
            try:
                kwargs['token'] = self.token
                with timer('orange.request'):
                    return self._request(api, **kwargs)
            except HTTPError as err:
                logger.error(err)
                self._login()  # auth error
                repeats -= 1
                if repeats == 0:
                    raise

    @property
    def token(self):
        try:
            key = self.config['username']
            return tokens[key]
        except KeyError:
            return

    def find(self, query, params=None):
        if params is None:
            params = {}

        size = 25  # int(query.get('size', 25))
        page = math.ceil((int(query.get('from', 0)) + 1) / size)
        try:
            sort = query.get('sort')[0]
        except (IndexError, AttributeError, TypeError):
            sort = {'versioncreated': 'desc'}

        kwargs = {
            'pagenumber': page,
            'countperpage': size,
            'fields': ','.join(self.FIELDS),
            'Sort': get_api_sort(sort),
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

        items = self._parse_items(data)
        return OrangelogicListCursor(items, data['APIResponse']['GlobalInfo']['TotalCount'])

    def _parse_items(self, data):
        items = []
        for item in data['APIResponse']['Items']:
            guid = item['SystemIdentifier']
            items.append({
                '_id': guid,
                '_fetchable': True,
                'guid': guid,
                'type': self.MEDIA_TYPE_MAP[item['MediaType'].lower()],
                'media': item['MediaEncryptedIdentifier'],
                'source': item['PhotographerFastId'],
                'slugline': item['Title'],
                'headline': item['CaptionShort'],
                'byline': item['Photographer'],
                'copyrightholder': item['copyright'],
                'description_text': item['Caption'],
                'firstcreated': self.parse_datetime(item['CreateDate']),
                'versioncreated': self.parse_datetime(item['MediaDate']) or self.parse_datetime(item['CreateDate']),
                'renditions': {
                    key: rendition(item[path])
                    for key, path in self.RENDITIONS_MAP.items()
                    if item.get(path) and item[path].get('URI')
                },
            })
        return items

    def parse_datetime(self, value):
        if not value:
            return None
        local = datetime.strptime(value, '%m/%d/%Y %H:%M:%S %p')
        return local_to_utc(self.TZ, local)

    def fetch(self, guid):
        kwargs = {
            'query': 'SystemIdentifier:{}'.format(guid),
            'fields': ','.join(self.FIELDS),
            'format': 'json',
            'DateFormat': 'u',
        }
        resp = self._auth_request(SEARCH_API, **kwargs)

        data = resp.json()
        item = self._parse_items(data)[0]

        url = self._url(DOWNLOAD_API)
        params = {
            'F': 'TRX',
            'DocID': item.pop('media'),
            'token': self.token,
        }

        href = requests.Request('GET', url, params=params).prepare().url
        update_renditions(item, href, None)

        if item['type'] == 'picture':
            _parse_binary(item)

        # it's in superdesk now, so make it ignore the api
        item['fetch_endpoint'] = ''

        item.setdefault('language', 'en')

        return item


def _parse_binary(item):
    binary = app.media.get(item['renditions']['original']['media'])
    iptc = get_meta_iptc(binary)
    if not iptc:
        return

    item.setdefault('extra', {})

    if iptc.get('By-line'):
        item['byline'] = iptc['By-line']

    if iptc.get('Category'):
        append_matching_subject(item, cp.PHOTO_CATEGORIES, iptc['Category'])

    if iptc.get('Credit'):
        item['creditline'] = 'THE ASSOCIATED PRESS' if iptc['Credit'] == 'AP' else iptc['Credit']

    if iptc.get('Source'):
        item['original_source'] = IPTC_SOURCE_MAPPING.get(iptc['Source'], iptc['Source'])
        item['extra'][cp.ARCHIVE_SOURCE] = item['original_source']

    if iptc.get('City') or item.get('Country/Primary Location Name'):
        country = iptc.get('Country/Primary Location Name')
        item['dateline'] = {
            'located': {
                'city': iptc.get('City'),
                'country': COUNTRY_MAPPING.get(country, country) if country else None,
            }
        }

    if iptc.get('By-line Title'):
        item['extra'][cp.PHOTOGRAPHER_CODE] = iptc['By-line Title']

    if iptc.get('Writer/Editor'):
        item['extra'][cp.CAPTION_WRITER] = iptc['Writer/Editor']

    if iptc.get('Copyright Notice'):
        item['copyrightnotice'] = iptc['Copyright Notice']

    if iptc.get('Caption/Abstract'):
        item['description_text'] = iptc['Caption/Abstract']

    if iptc.get('Special Instructions'):
        item['ednote'] = iptc['Special Instructions']

    if iptc.get('Original Transmission Reference'):
        item['extra']['itemid'] = iptc['Original Transmission Reference']

    binary.seek(0)
    xmp = parse_xmp(binary)
    if not xmp:
        return

    if xmp.get('http://ns.adobe.com/photoshop/1.0/'):
        for key, val, _ in xmp['http://ns.adobe.com/photoshop/1.0/']:
            if key == 'photoshop:Urgency':
                item['urgency'] = int(val)
            elif key == 'photoshop:DateCreated':
                item['firstcreated'] = _parse_xmp_datetime(val)

    if xmp.get('http://purl.org/dc/elements/1.1/'):
        for key, val, _ in xmp['http://purl.org/dc/elements/1.1/']:
            if key == 'dc:rights' and val:
                item['extra'][cp.INFOSOURCE] = val
            elif key == 'dc:rights[1]' and val:
                item['extra'][cp.INFOSOURCE] = val


def _parse_xmp_datetime(val):
    try:
        return datetime.strptime(val[:19], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=UTC)
    except ValueError:
        return datetime.strptime(val[:19], '%Y-%m-%d').replace(tzinfo=UTC)


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
