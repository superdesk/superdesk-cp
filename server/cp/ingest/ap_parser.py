
import re

from superdesk.io.feed_parsers import APMediaFeedParser


class CP_APMediaFeedParser(APMediaFeedParser):

    def process_slugline(self, slugline):
        return re.sub(r'--+', '-', re.sub(r'[ !"#$%&()*+,./:;<=>?@[\]^_`{|}~\\]', '-', slugline))

    def parse(self, s_json, provider=None):
        item = super().parse(s_json, provider=provider)
        if item.get('slugline'):
            item['slugline'] = self.process_slugline(item['slugline'])
        return item
