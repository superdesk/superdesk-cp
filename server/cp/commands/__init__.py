import superdesk
from .update_event_types import UpdateEventTypesCommand
from .fix_events_moment_timezone_2023 import FixEventsCommand


superdesk.command("cp:update_event_types", UpdateEventTypesCommand())
superdesk.command("cp:fix_event_dates_2023", FixEventsCommand())
