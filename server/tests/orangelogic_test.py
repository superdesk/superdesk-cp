
import flask
import unittest

from cp.orangelogic import OrangelogicSearchProvider


class OrangelogicTestCase(unittest.TestCase):

    provider = {'config': {'username': 'foo', 'password': 'bar'}}

    def setUp(self):
        self.app = flask.Flask(__name__)
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        if hasattr(self, 'ctx'):
            self.ctx.pop()

    def test_instance(self):
        OrangelogicSearchProvider(self.provider)

    def test_find(self):
        service = OrangelogicSearchProvider(self.provider)
        items = service.find({})
        self.assertEqual(50, len(items))
        self.assertGreater(items.count(), 50)
