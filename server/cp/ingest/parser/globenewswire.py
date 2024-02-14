import cp
import logging
import lxml.html as lxml_html

from cp.utils import format_maxlength
from superdesk.text_utils import get_word_count, get_text
from superdesk.io.feed_parsers.newsml_2_0 import NewsMLTwoFeedParser


SOURCE = "Globenewswire"
KEYWORD_ROLE = "MWKeyRole:Ticker"

DESCRIPTION = {
    "en": "Press Release",
    "fr": "Communiqué",
}

BODY_FOOTER = {
    "en": "NEWS RELEASE TRANSMITTED BY Globe Newswire",
    "fr": "COMMUNIQUE DE PRESSE TRANSMIS PAR Globe Newswire",
}

NS = {
    "iptc": "http://iptc.org/std/nar/2006-10-01/",
    "xhtml": "http://www.w3.org/1999/xhtml",
}

logger = logging.getLogger(__name__)


class GlobeNewswireParser(NewsMLTwoFeedParser):
    NAME = "globenewswire"
    label = SOURCE
    ALLOWED_EXT = {".newsml", ".xml"}

    def parse_content_subject(self, tree, item):
        pass

    def parse_item(self, tree):
        item = super().parse_item(tree)
        meta = tree.find(self.qname("contentMeta"))

        organisation = meta.xpath(
            './iptc:subject[@type="cpnat:organisation"][@literal]', namespaces=NS
        )
        if organisation:
            org_name = organisation[0].get("literal")
            item["abstract"] = format_maxlength(
                "FOR: {}. {}".format(
                    org_name.upper().rstrip("."),
                    get_text(item["body_html"]).replace("  ", " "),
                ),
                200,
            )
            item.setdefault("subject", []).append(
                {
                    "name": org_name,
                    "qcode": org_name,
                    "scheme": cp.ORGANISATION,
                }
            )

        return item

    def parse_item_meta(self, tree, item):
        super().parse_item_meta(tree, item)
        meta = tree.find(self.qname("itemMeta"))
        services = meta.findall(self.qname("service"))
        for service in services:
            if service.get("qcode") and service.get("qcode").startswith("MWNetwork:"):
                code = service.get("qcode").split(":")[1]
                item.setdefault("subject", []).append(
                    {
                        "name": code,
                        "qcode": code,
                        "scheme": cp.SERVICE,
                    }
                )

    def parse_content_meta(self, tree, item):
        meta = super().parse_content_meta(tree, item)

        item["language"] = item["language"].split("-")[0]
        item["description_text"] = DESCRIPTION[item["language"]]

        item["slugline"] = "GNW-{lang}-{time}--{symbols}".format(
            lang=item["language"],
            time=meta.find(self.qname("contentCreated")).text[17:19],
            symbols="-".join(self._get_stock_symbols(tree)),
        )

        keywords = meta.findall(self.qname("keyword"))
        item["keywords"] = [
            k.text for k in keywords if k.text and k.get("role") == KEYWORD_ROLE
        ]

        item["source"] = SOURCE
        item["urgency"] = item["priority"] = 3
        item["anpa_category"] = [{"name": item["description_text"], "qcode": "p"}]
        item["abstract"] = meta.find(self.qname("description")).text

        return meta

    def parse_inline_content(self, tree, item, ns=NS["xhtml"]):
        """
        Get contents of span/div with class mw_release and
        clean html in there.
        """
        html = tree.find(self.qname("html", ns))
        content = {"contenttype": tree.get("contenttype")}
        contents = []
        cleaner = lxml_html.clean.Cleaner(
            scripts=True,
            javascript=True,
            style=True,
            comments=True,
            add_nofollow=True,
            kill_tags=["style", "script"],
            safe_attrs=["alt", "src", "rel", "href", "target"],
        )
        divs = html.xpath('./xhtml:body/xhtml:*[@class="mw_release"]', namespaces=NS)
        for div in divs:
            for child in div:
                if "img" in child.tag:
                    continue
                child_html = lxml_html.fromstring(
                    lxml_html.tostring(child, encoding="unicode")
                )
                clean_html = cleaner.clean_html(child_html)
                if clean_html.tag == "table":
                    clean_td_br(clean_html)
                clean_td_br(clean_html)
                contents.append(lxml_html.tostring(clean_html, encoding="unicode"))
        content["content"] = "\n".join(contents)
        return content

    def parse_content_set(self, tree, item):
        super().parse_content_set(tree, item)
        item["word_count"] = get_word_count(item.get("body_html"))
        item["body_html"] = "{}\n<p>{}</p>".format(
            item["body_html"],
            BODY_FOOTER[item["language"]],
        )

    def _get_stock_symbols(self, tree):
        symbols = [
            elem.get("literal")
            for elem in tree.xpath(
                './iptc:assert/iptc:related[@rel="MWFinRel:Instrument"][@literal]',
                namespaces=NS,
            )
        ]
        if symbols:
            return symbols
        subjects = tree.xpath(
            './iptc:contentMeta/iptc:subject[starts-with(@qcode,"MWSubject:")]',
            namespaces=NS,
        )
        return [subj.get("qcode").split(":")[-1] for subj in subjects]


def clean_td_br(table):
    """Avoid double <br><br> in <td>.

    SDCP-266
    """
    for tr in table:
        if tr.tag != "tr":
            continue
        for td in tr:
            for elem in td:
                if (
                    elem.tag == "br"
                    and elem.getnext() is not None
                    and elem.getnext().tag == "br"
                ):
                    td.remove(elem)
