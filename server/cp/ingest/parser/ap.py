
import re
import json
import bson
import superdesk

from superdesk.datalayer import SuperdeskJSONEncoder
from superdesk.io.feed_parsers import APMediaFeedParser

from cp import HEADLINE2
from cp.orangelogic import OrangelogicSearchProvider


class CP_APMediaFeedParser(APMediaFeedParser):
    """
    Metadata: https://developer.ap.org/ap-media-api/agent/AP_Classification_Metadata.htm
    """

    PROFILE_ID = 'Story'
    RELATED_ID = 'media-gallery'

    # use preview for all now
    RENDITIONS_MAPPING = {
        'baseImage': 'preview',
        'viewImage': 'preview',
        'thumbnail': 'thumbnail',
    }

    def process_slugline(self, slugline):
        return re.sub(r'--+', '-', re.sub(r'[ !"#$%&()*+,./:;<=>?@[\]^_`{|}~\\]', '-', slugline))

    def parse(self, data, provider=None):
        item = super().parse(data, provider=provider)
        ap_item = data['data']['item']

        if item.get('slugline'):
            item['slugline'] = self.process_slugline(item['slugline'])

        if item.get('type') == 'text':
            item['profile'] = self.PROFILE_ID

        if ap_item.get('keywords'):
            item['keywords'] = ap_item['keywords']

        if ap_item.get('subject'):
            item['subject'] = self._parse_subject(ap_item['subject'])

        try:
            dateline = ap_item['datelinelocation']
        except KeyError:
            pass
        else:
            try:
                source = ap_item['infosource'][0]['name']
            except (KeyError, IndexError):
                source = item.get('source')
            item['dateline'] = {
                'text': ap_item.get('located', ''),
                'source': source,
                'located': {
                    'alt_name': '',
                    'city': dateline.get('city', ''),
                    'city_code': dateline.get('city', ''),
                    'state': dateline.get('countryareaname', ''),
                    'state_code': dateline.get('countryareacode', ''),
                    'country': dateline.get('countryname', ''),
                    'country_code': dateline.get('countrycode', ''),
                    'dateline': 'city',
                }
            }

            try:
                lon, lat = dateline['geometry_geojson']['coordinates']
                item['dateline']['located']['location'] = {'lat': lat, 'lon': lon}
            except KeyError:
                pass

        item.setdefault('extra', {})

        if item.get('abstract'):
            item['extra'][HEADLINE2] = item.pop('abstract')

        return item

    def _parse_subject(self, subject):
        parsed = []
        available = superdesk.get_resource_service('vocabularies').find_one(req=None, _id='subject_custom')
        for subj in available['items']:
            if subj.get('ap'):
                codes = subj['ap'].split(',')
                for ap_subj in subject:
                    if any([code for code in codes if ap_subj['code'].startswith(code)]):
                        parsed.append({
                            'name': subj['name'],
                            'qcode': subj['qcode'],
                            'scheme': available['_id'],
                            'translations': subj['translations'],
                        })
        return parsed
