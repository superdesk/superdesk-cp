from flask import current_app, json

from superdesk.publish import register_transmitter
from superdesk.publish.publish_service import PublishService
from cp.ai.translate import Translate  # Import the Translate integration class


class TranslateTransmitter(PublishService):
    def _transmit(self, queue_item, subscriber):
        translate = Translate(current_app)  # Initialize the Translate integration
        item = json.loads(queue_item["formatted_item"])
        # Transmit the item using the Translate integration
        translated_item = translate.data_operation("translate", "translate", None, item)
        # Here you might want to do something with the translated_item,
        # such as saving it or sending it somewhere else


# Register the Translate transmitter
register_transmitter("translate", TranslateTransmitter(), [])
