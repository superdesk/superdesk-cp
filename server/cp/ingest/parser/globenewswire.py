
import logging
import lxml.etree as etree
import lxml.html as lxml_html

from superdesk.text_utils import get_word_count
from superdesk.io.feed_parsers.newsml_2_0 import NewsMLTwoFeedParser


DESCRIPTION = 'Press Release'
KEYWORD_ROLE = 'MWKeyRole:Ticker'
BODY_FOOTER = {
    'en': 'NEWS RELEASE TRANSMITTED BY Globe Newswire',
    'fr': 'COMMUNIQUE DE PRESSE TRANSMIS PAR Globe Newswire',
}
NS = {
    'iptc': 'http://iptc.org/std/nar/2006-10-01/',
    'xhtml': 'http://www.w3.org/1999/xhtml',
}

logger = logging.getLogger(__name__)


class GlobeNewswireParser(NewsMLTwoFeedParser):

    NAME = 'globenewswire'
    label = 'Globe Newswire'

    def parse_content_meta(self, tree, item):
        meta = super().parse_content_meta(tree, item)

        item['language'] = item['language'].split('-')[0]

        item['slugline'] = 'GNW-{lang}-{time}--{symbols}'.format(
            lang=item['language'],
            time=meta.find(self.qname('contentCreated')).text[17:19],
            symbols='-'.join(self._get_stock_symbols(tree)),
        )

        keywords = meta.findall(self.qname('keyword'))
        item['keywords'] = [k.text for k in keywords if k.text and k.get('role') == KEYWORD_ROLE]

        item['description_text'] = DESCRIPTION
        item['body_footer'] = BODY_FOOTER[item['language']]

        return meta

    def parse_inline_content(self, tree, item, ns=NS['xhtml']):
        """
        Get contents of span/div with class mw_release and
        clean html in there.
        """
        html = tree.find(self.qname('html', ns))
        content = {'contenttype': tree.get('contenttype')}
        contents = []
        cleaner = lxml_html.clean.Cleaner(
            scripts=True,
            javascript=True,
            style=True,
            comments=True,
            add_nofollow=False,
            kill_tags=['style', 'script'],
            safe_attrs=['alt', 'src', 'rel'],
        )
        divs = html.xpath('./xhtml:body/xhtml:*[@class="mw_release"]', namespaces=NS)
        for div in divs:
            for child in div:
                if 'img' in child.tag:
                    continue
                child_html = lxml_html.fromstring(lxml_html.tostring(child, encoding='unicode'))
                clean_html = cleaner.clean_html(child_html)
                contents.append(lxml_html.tostring(clean_html, encoding='unicode'))
        content['content'] = '\n'.join(contents)
        return content

    def parse_content_set(self, tree, item):
        super().parse_content_set(tree, item)
        item['word_count'] = get_word_count(item.get('body_html'))

    def _get_stock_symbols(self, tree):
        symbols = [
            elem.get('literal')
            for elem in tree.xpath('./iptc:assert/iptc:related[@rel="MWFinRel:Instrument"][@literal]', namespaces=NS)
        ]
        if symbols:
            return symbols
        subjects = tree.xpath('./iptc:contentMeta/iptc:subject[starts-with(@qcode,"MWSubject:")]', namespaces=NS)
        return [subj.get('qcode').split(':')[-1] for subj in subjects]
