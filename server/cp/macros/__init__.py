
import os

from superdesk.macros import load_macros, init_app as core_init_app


def init_app(_app):
    core_init_app(_app)
    load_macros(os.path.realpath(os.path.dirname(__file__)), 'cp.macros')  # noqa
