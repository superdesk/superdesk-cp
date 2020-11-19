
import flask
import unittest
import superdesk

from unittest.mock import patch
from tests.mock import resources
from cp.macros.auto_routing import callback


class AutoRoutingMacroTestCase(unittest.TestCase):

    def setUp(self):
        self.app = flask.Flask(__name__)

    def test_auto_routing_matches_service_destination(self):
        item = {}
        rule = {'name': 'Broadcast: The Associated Press (APR)'}

        with self.app.app_context():
            with patch.dict(superdesk.resources, resources):
                callback(item, rule=rule)

        self.assertIn('subject', item)
        self.assertIn({
            'name': 'Broadcast',
            'qcode': 'Broadcast',
            'scheme': 'distribution',
        }, item['subject'])
        self.assertIn({
            'name': 'The Associated Press',
            'qcode': 'ap---',
            'scheme': 'destinations',
        }, item['subject'])

    def test_auto_routing_not_matching_service_or_dest_logs_error(self):
        item = {}
        rule = {'name': 'Foo: Bar'}

        LOG_PREFIX = 'ERROR:cp.macros.auto_routing:'

        with self.app.app_context():
            with patch.dict(superdesk.resources, resources):
                with self.assertLogs('cp.macros.auto_routing', 'ERROR') as log:
                    callback(item, rule=rule)
                    self.assertIsNone(item.get('subject'))
                    self.assertEqual(log.output, [
                        '{}no item found in vocabulary distribution with name Foo'.format(LOG_PREFIX),
                        '{}no item found in vocabulary destinations with name Bar'.format(LOG_PREFIX),
                    ])
