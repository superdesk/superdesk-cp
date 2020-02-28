
import re
import logging
import requests

from superdesk.text_utils import get_text

SERVICE_URL = 'https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?recent=1'

CURRENCY_REGEX = re.compile(
    r'(^| |\b)(?P<currency>[A-Z]+)?\$ ?(?P<num>[0-9]+(?P<decimal>\.[0-9]+)?)(?P<mil> million)?($|\b)',
    re.MULTILINE,
)

sess = requests.Session()
logger = logging.getLogger(__name__)


def get_rate():
    res = sess.get(SERVICE_URL, timeout=(3, 10))
    res.raise_for_status()
    rate = float(res.json()['observations'][0]['FXUSDCAD']['v'])
    logger.debug('got USD2CAD rate %f', rate)
    return rate


def callback(item, **kwargs):
    diff = {}
    if not item.get('body_html'):
        return diff
    rate = get_rate()
    text = get_text(item['body_html'], 'html', True)

    def repl(m):
        if m.group('currency') and m.group('currency') != 'US':
            return
        converted = float(m.group('num')) * rate
        if m.group('decimal'):
            # convert 55.21 to 73.73 - round to 3 decimals and strip last one
            fixed = '{:.3f}'.format(converted)[:-1]
        else:
            # convert 55 to 73.70 - round to 1 decimal and add 0
            fixed = '{:.1f}0'.format(converted)
            fixed = fixed.replace('.00', '')
        # keep leeding whitespace so on client it won't
        # replace $500 in C$500
        diff[m.group(0).rstrip()] = '{} (C${}{})'.format(
            m.group(0).rstrip(),
            fixed,
            m.group('mil') or '',
        ).rstrip()

    re.sub(CURRENCY_REGEX, repl, text)

    return (item, diff)


name = 'usd_to_cad'
label = 'USD to CAD'
access_type = 'frontend'
action_type = 'interactive'
group = 'currency'
