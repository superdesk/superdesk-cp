
import os

from superdesk.macros import load_macros

import superdesk.macros.abstract_populator
import superdesk.macros.assign_status
import superdesk.macros.desk_routing
import superdesk.macros.extract_html
import superdesk.macros.internal_destination_auto_publish
import superdesk.macros.take_key_validator
import superdesk.macros.validate_for_publish


def init_app(_app):
    load_macros(os.path.realpath(os.path.dirname(__file__)), 'cp.macros')  # noqa
