
import re
import decimal
import logging
import requests
import functools

from superdesk.text_utils import get_text

SERVICE_URL = 'https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?recent=1'

CURRENCY_REGEX = re.compile(r'''
    (^|\ |\b)
    (?P<currency>[A-Z]+)?\$\ ?
    (?P<num>[0-9]+(,?[0-9]+)*(?P<decimal>\.[0-9]+)?)
    (?P<mil>\ (mil|bil|tril)lions?)?
    ($|\b)
    ''', re.MULTILINE | re.VERBOSE)

CURRENCY_REGEX_FR = re.compile(r'''
    (^|\ |\b)
    (?P<num>[0-9]+(\ ?[0-9]+)*(?P<decimal>\,[0-9]+)?)
    (?P<mil>\ (mil|bil|tril)lions?)?\ ?
    \$\ ?(?P<currency>[A-Z]+)?
    ($|\b)
    ''', re.MULTILINE | re.VERBOSE)

sess = requests.Session()
logger = logging.getLogger(__name__)


def get_rate():
    res = sess.get(SERVICE_URL, timeout=(3, 10))
    res.raise_for_status()
    rate = decimal.Decimal(res.json()['observations'][0]['FXUSDCAD']['v'])
    logger.debug('got USD2CAD rate %f', rate)
    return rate


def callback(item, **kwargs):
    diff = {}
    if not item.get('body_html'):
        return diff
    rate = get_rate()
    text = get_text(item['body_html'], 'html', True)

    def repl(m, is_fr=False):
        if m.group('currency') and m.group('currency') != 'US':
            return
        if is_fr:
            num = m.group('num').replace(',', '.').replace(' ', '')
        else:
            num = m.group('num').replace(',', '')
        print('num', num)
        converted = decimal.Decimal(num) * rate
        if m.group('decimal'):
            _format = '{:.3f}'  # convert 55.21 to 73.73 - round to 3 decimals and strip last one
            if is_fr and ' ' in m.group('num') or not is_fr and ',' in m.group('num'):
                _format = '{:,.3f}'
            fixed = _format.format(converted)[:-1]
        else:
            _format = '{:.1f}0'  # convert 55 to 73.70 - round to 1 decimal and add 0
            if is_fr and ' ' in m.group('num') or not is_fr and ',' in m.group('num'):
                _format = '{:,.1f}0'
            fixed = _format.format(converted).replace('.00', '')
        # keep leeding whitespace so on client it won't
        # replace $500 in C$500
        diff[m.group(0).rstrip()] = '{whitespace} ({en_currency}{value}{mil}{fr_currency})'.format(
            whitespace=m.group(0).rstrip(),
            en_currency='' if is_fr else 'C$',
            value=fixed if not is_fr else fixed.replace(',', ' ').replace('.', ','),
            mil=m.group('mil') or '',
            fr_currency=' $ CAN' if is_fr else '',
        ).rstrip()

    re.sub(CURRENCY_REGEX, repl, text)
    re.sub(CURRENCY_REGEX_FR, functools.partial(repl, is_fr=True), text)

    return (item, diff)


name = 'usd_to_cad'
label = 'USD to CAD'
access_type = 'frontend'
action_type = 'interactive'
group = 'currency'
