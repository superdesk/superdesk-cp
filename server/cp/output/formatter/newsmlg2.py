
from superdesk.publish import formatters
import cp

from superdesk.publish.formatters.newsml_g2_formatter import NewsMLG2Formatter, SubElement


class CPNewsMLG2Formatter(NewsMLG2Formatter):

    def _format_headline(self, article, content_meta):
        """Appends the headline element to the contentMeta element

        :param dict article:
        :param Element content_meta:
        """
        try:
            headline = article['extra'][cp.HEADLINE2]
            SubElement(content_meta, 'headline').text = headline
            SubElement(content_meta, 'headline', attrib={'role': 'short'}).text = article.get('headline', '')
        except KeyError:
            super()._format_headline(article, content_meta)

    def _format_rights(self, item, article):
        try:
            super()._format_rights(item, article)
        except KeyError:
            pass

    def can_format(self, format_type, article):
        return format_type == 'cpnewsmlg2'
