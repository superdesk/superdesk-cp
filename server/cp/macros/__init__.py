
import os

from superdesk.macros import load_macros


load_macros(os.path.realpath(os.path.dirname(__file__)), 'cp.macros')  # noqa
