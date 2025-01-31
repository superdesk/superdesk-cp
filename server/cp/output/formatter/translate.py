import logging
from superdesk.text_utils import get_text
from .cp_ninjs_formatter import CPNINJSFormatter
from cp.ai.translate import Translate  # Import the Translate integration class

logger = logging.getLogger(__name__)


class TranslateFormatter(CPNINJSFormatter):
    def can_format(self, format_type, article):
        return format_type.lower() == "translate" and article.get("type") == "text"

    def _transform_to_ninjs(self, article, subscriber, recursive=True):
        translate = Translate(self.app)  # Initialize the Translate integration
        formatted_data = {}  # Define how you want to format the data for translation

        try:
            # Format the data for translation
            formatted_data = {
                "guid": article.get("guid"),
                "language": article.get("language"),
                "slugline": article.get("slugline"),
                "headline": get_text(article.get("headline", "")),
                "body_html": get_text(article.get("body_html", "")),
                "abstract": get_text(article.get("abstract", "")),
                "headline_extended": get_text(article.get("headline_extended", ""))
            }

            # Perform the translation
            translated_item = translate.data_operation("translate", "translate", None, formatted_data)

            # You might want to do something with the translated_item here,
            # such as updating the article or returning it

            return translated_item

        except Exception as e:
            logger.error(f"Error formatting data for translation: {str(e)}")
            return {}  # Return an empty dictionary in case of an error
