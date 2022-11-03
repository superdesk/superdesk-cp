import superdesk
from .update_event_types import UpdateVocabulariesCommand


superdesk.command("cp:update_event_types", UpdateVocabulariesCommand())
