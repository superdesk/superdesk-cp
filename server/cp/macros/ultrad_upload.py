
from flask_babel import lazy_gettext
from flask import current_app as app

from cp.ultrad import upload_document, ULTRAD_ID


def callback(item, **kwargs):
    item.setdefault('extra', {})
    if item['extra'].get(ULTRAD_ID):
        app.logger.info('item %s is already in ultrad', item['guid'])
        return item

    if not item.get('body_html'):
        app.logger.debug('nothing to translate for item %s', item['guid'])
        return item

    ultrad_id = upload_document(item)
    if ultrad_id:
        item['extra'][ULTRAD_ID] = ultrad_id

    return item


name = 'ultrad-upload'
label = lazy_gettext('Upload to Ultrad')
group = lazy_gettext('translate')
access_type = 'frontend'
action_type = 'direct'
