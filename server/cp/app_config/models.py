from datetime import datetime, timezone

# Define the schema as a simple dictionary to avoid import issues
SCHEMA = {
    "key": {
        "type": "string",
        "required": True,
        "unique": True,
        "minlength": 1,
        "maxlength": 100,
    },
    "value": {
        "type": "string",
        "required": True,
        "minlength": 1,
    },
    "description": {
        "type": "string",
        "required": False,
        "minlength": 1,
        "maxlength": 500,
    },
    "category": {
        "type": "string",
        "required": False,
    },
    "is_active": {
        "type": "boolean",
        "default": True,
    },
    "expiry_date": {
        "type": "string",
        "required": False,
    },
}
