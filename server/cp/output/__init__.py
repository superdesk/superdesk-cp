import os
import lxml.etree as etree

from .formatter.jimi import JimiFormatter  # noqa
from .formatter.newsmlg2 import CPNewsMLG2Formatter  # noqa
from .formatter.cp_ninjs_formatter import CPNINJSFormatter  # noqa
from .formatter.semaphore import SemaphoreFormatter  # noqa

from superdesk.publish.publish_service import PublishService, set_publish_service


class CPPublishService(PublishService):
    @classmethod
    def get_filename(cls, queue_item):
        orig = PublishService.get_filename(queue_item)
        name, ext = os.path.splitext(orig)
        try:
            item = etree.fromstring(queue_item["formatted_item"].encode("utf-8"))
            filename = item.find("ContentItem").find("FileName").text
            return "{}{}".format(filename, ext)
        except (etree.XMLSyntaxError, AttributeError):
            pass
        return "{}{}".format("-".join(name.split("-")[:-2]), ext)


set_publish_service(CPPublishService)
