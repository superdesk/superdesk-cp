import cp

from superdesk.etree import etree
from superdesk.io.feed_parsers import NewsMLOneFeedParser

NS = {
    "xhtml": "http://www.w3.org/1999/xhtml",
}


class BusinessWireParser(NewsMLOneFeedParser):

    COMPONENT_ROLE_MAPPING = {
        "Body": "body_html",
        "HeadLine": "headline",
        "Abstract": "abstract",
    }

    def parse_content(self, item, xml):
        components = xml.findall("NewsItem/NewsComponent/NewsComponent/NewsComponent")
        for component in components:
            role = component.find("Role")
            if role is None:
                continue
            dest = self.COMPONENT_ROLE_MAPPING.get(role.get("FormalName"))
            if not dest:
                continue
            body = component.find(
                "ContentItem/DataContent/xhtml:html/xhtml:body", namespaces=NS
            )
            if dest == "headline":
                item[dest] = etree.tostring(
                    body, encoding="unicode", method="text"
                ).strip()
            elif dest == "abstract":
                item[dest] = component.find("ContentItem/DataContent").text
            else:
                item[dest] = "\n".join(
                    [
                        etree.tostring(elem, encoding="unicode", method="html").replace(
                            ' xmlns="http://www.w3.org/1999/xhtml"', ""
                        )
                        for elem in body
                    ]
                )

        party = xml.find("NewsItem/NewsComponent/AdministrativeMetadata/Source/Party")
        if party is not None and party.get("FormalName"):
            item.setdefault("subject", []).append(
                {
                    "name": party.get("FormalName"),
                    "qcode": party.get("FormalName"),
                    "scheme": cp.ORGANISATION,
                }
            )

    def populate_fields(self, item):
        return [super().populate_fields(item)]
