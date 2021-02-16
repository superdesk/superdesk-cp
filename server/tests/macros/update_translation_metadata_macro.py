import cp
import flask
import unittest
import superdesk

from unittest.mock import patch
from tests.mock import resources
from cp.macros.update_translation_metadata_macro import update_translation_metadata_macro as macro

class UpdateTranslationMetadataMacroTestCase(unittest.TestCase):
    def setUp(self):
        self.app = flask.Flask(__name__)

    def test_remove_destination_and_add_presse_canadienne_staff_as_destination(self):
        '''
        Remove the current destination and add the Presse Canadienne staff as destination
        make the anpa_take_key as an empty string
        '''

        item = {
            '_id': 'urn:newsml:localhost:5000:2019-12-10T14:43:46.224107:d13ac5ae-7f43-4b7f-89a5-2c6835389564',
            'guid': 'urn:newsml:localhost:5000:2019-12-10T14:43:46.224107:d13ac5ae-7f43-4b7f-89a5-2c6835389564',
            'headline': 'test headline',
            'slugine': 'test slugline',
            'state': 'in_progress',
            'type': 'text',
            'language': 'en',
            'anpa_take_key': 'update',
            'subject': [{
                'name' : 'Command News',
                'qcode' : 'CMPD1',
                'scheme': 'destinations'
            }]
        }

        with self.app.app_context():
            with patch.dict(superdesk.resources, resources):
                macro(item)

        self.assertIn('subject', item)
        self.assertIn(
            {
                'name': 'Presse Canadienne staff',
                'qcode': 'sfstf',
                'scheme': 'destinations',
            },
            item['subject'],
        )
        self.assertEqual(item.get('anpa_take_key'), '')

    def test_override_destination_canadian_press_staff_to_presse_canadienne_staff(self):
        '''
        if Canadian Press Staff destination is present override it with Presse Canadienne staff
        '''
        item = {
            '_id': 'urn:newsml:localhost:5000:2019-12-10T14:43:46.224107:d13ac5ae-7f43-4b7f-89a5-2c6835389564',
            'guid': 'urn:newsml:localhost:5000:2019-12-10T14:43:46.224107:d13ac5ae-7f43-4b7f-89a5-2c6835389564',
            'headline': 'test headline',
            'slugine': 'test slugline',
            'state': 'in_progress',
            'type': 'text',
            'language': 'en',
            'subject': [{
                'name' : 'Canadian Press Staff',
                'qcode' : 'cpstf',
                'scheme': 'destinations'
            }]
        }

        with self.app.app_context():
            with patch.dict(superdesk.resources, resources):
                macro(item)

        self.assertIn('subject', item)
        self.assertIn(
            {
                'name': 'Presse Canadienne staff',
                'qcode': 'sfstf',
                'scheme': 'destinations',
            },
            item['subject'],
        )

    def test_override_destination_the_associated_press_to_l_associated_press(self):
        '''
        if The Associated Press destination is present override it with L'Associated Press 
        '''
        item = {
            '_id': 'urn:newsml:localhost:5000:2019-12-10T14:43:46.224107:d13ac5ae-7f43-4b7f-89a5-2c6835389564',
            'guid': 'urn:newsml:localhost:5000:2019-12-10T14:43:46.224107:d13ac5ae-7f43-4b7f-89a5-2c6835389564',
            'headline': 'test headline',
            'slugine': 'test slugline',
            'state': 'in_progress',
            'type': 'text',
            'language': 'en',
            'subject': [{
                'name' : 'The Associated Press',
                'qcode' : 'ap---',
                'scheme': 'destinations'
            }]
        }

        with self.app.app_context():
            with patch.dict(superdesk.resources, resources):
                macro(item)

        self.assertIn('subject', item)
        self.assertIn(
            {
                'name' : "L'Associated Press",
                'qcode' : 'apfra',
                'scheme': 'destinations',
            },
            item['subject'],
        )

    def test_destination_is_empty_add_presse_canadienne_staff(self):
        '''
        if the destination is empty add Presse Canadienne staff
        '''
        item = {
            '_id': 'urn:newsml:localhost:5000:2019-12-10T14:43:46.224107:d13ac5ae-7f43-4b7f-89a5-2c6835389564',
            'guid': 'urn:newsml:localhost:5000:2019-12-10T14:43:46.224107:d13ac5ae-7f43-4b7f-89a5-2c6835389564',
            'headline': 'test headline',
            'slugine': 'test slugline',
            'state': 'in_progress',
            'type': 'text',
            'keywords': ['foo', 'bar'],
            'language': 'en'
        }

        with self.app.app_context():
            with patch.dict(superdesk.resources, resources):
                macro(item)

        self.assertIn('subject', item)
        self.assertIn(
            {
                'name': 'Presse Canadienne staff',
                'qcode': 'sfstf',
                'scheme': 'destinations',
            },
            item['subject'],
        )

