import superdesk
from .update_event_types import UpdateEventTypesCommand


superdesk.command("cp:update_event_types", UpdateEventTypesCommand())
