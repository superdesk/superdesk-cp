
import unittest

from httmock import urlmatch, HTTMock
from cp.macros import usd_to_cad as macro


SERVICE_JSON = """
{
    "observations": [
        {
            "d": "2020-02-25",
            "FXUSDCAD": {
                "v": "1.3281"
            }
        }
    ]
}
"""


@urlmatch(netloc=r'www\.bankofcanada\.ca$', path=r'/valet/observations/FXUSDCAD/json')
def rates(url, request):
    return SERVICE_JSON


class USD2CADMacroTestCase(unittest.TestCase):

    def test_metadata(self):
        self.assertIsNotNone(getattr(macro, 'name'))
        self.assertIsNotNone(getattr(macro, 'label'))

    def test_convertions(self):
        test = {
            '$52': 'C$69.10',
            '$52.34': 'C$69.51',
            '$56': 'C$74.40',
            '$52 million': 'C$69.10 million',
            'US$52': 'C$69.10',
            'US$52.34': 'C$69.51',
            '$ 52': 'C$69.10',
            'US$ 52': 'C$69.10',
            'US$300 (C$394)': '',
            'C$69': '',
            '123': '',
            'C$500': '',
            'C$ 120': '',
            'ABC$120': '',
            'foo $100 foo': {'key': ' $100', 'repl': 'C$132.80'},
            ' $200.': {'key': ' $200', 'repl': 'C$265.60'},
            '52,34 millions $': '69,51 millions C$',
            '52,34 $': '69,51 C$',
            '2,24$': '2,97 C$',
        }

        item = {'body_html': '\n'.join(test.keys())}

        with HTTMock(rates):
            (_, diff) = macro.callback(item)

        for key, val in test.items():
            if val and isinstance(val, str):
                self.assertIn(key, diff.keys())
                self.assertEqual('{} ({})'.format(key, val), diff[key])
            elif val:
                self.assertIn(val['key'], diff.keys())
                self.assertEqual('{} ({})'.format(val['key'], val['repl']), diff[val['key']])
            else:
                self.assertNotIn(key, diff)
