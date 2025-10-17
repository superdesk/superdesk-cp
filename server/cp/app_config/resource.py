from superdesk.resource import Resource
from superdesk.services import BaseService
from datetime import datetime, timezone
from .models import SCHEMA
import logging
import requests

logger = logging.getLogger(__name__)


class AppConfigResource(Resource):
    """Resource for application configuration items."""

    endpoint_name = "app_config"
    resource_methods = ["GET", "POST"]
    item_methods = ["GET", "PATCH", "PUT", "DELETE"]
    schema = SCHEMA

    # Use privileges that the admin user actually has
    privileges = {
        "GET": "archive",  # User has 'archive: 1'
        "POST": "archive",  # User has 'archive: 1'
        "PATCH": "archive",  # User has 'archive: 1'
        "PUT": "archive",  # User has 'archive: 1'
        "DELETE": "archive",  # User has 'archive: 1'
    }


class AppConfigService(BaseService):
    """Service for application configuration items."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_create(self, docs):
        """Handle insertion of configuration items - runs BEFORE schema validation."""
        for doc in docs:
            existing = self.find_one(req=None, key=doc["key"])
            if existing:
                raise ValueError(f"Configuration key '{doc['key']}' already exists")

            # Special handling for semaphore_api_key insertions
            if doc.get("key") == "semaphore_api_key" and "value" in doc:
                self._validate_and_update_semaphore_api_key(doc, {})

    def on_created(self, docs):
        """Handle creation of configuration items - runs AFTER the creation is applied."""
        pass

    def on_update(self, updates, original):
        """Handle updates to configuration items - runs BEFORE the update is applied."""

        if "key" in updates and updates["key"] != original["key"]:
            existing = self.find_one(req=None, key=updates["key"])
            if existing:
                raise ValueError(f"Configuration key '{updates['key']}' already exists")

        if original.get("key") == "semaphore_api_key" and "value" in updates:
            self._validate_and_update_semaphore_api_key(updates, original)

    def on_updated(self, updates, original):
        """Handle updates to configuration items - runs AFTER the update is applied."""
        pass

    def on_delete(self, doc):
        """Handle deletion of configuration items."""
        # Add any cleanup logic here
        pass

    def _validate_and_update_semaphore_api_key(self, updates, original):
        """Validate and update semaphore API key with proper expiry information"""
        try:
            from settings import SEMAPHORE_TOKEN_URL, SEMAPHORE_API_KEY_URL

            # Validate the new API key
            new_api_key = updates["value"]
            logger.info("Validating new Semaphore API key...")

            # Get access token using the provided API key
            token_response = self._get_semaphore_access_token(
                new_api_key, SEMAPHORE_TOKEN_URL
            )
            if not token_response:
                logger.error("Failed to get access token for API key validation")
                raise ValueError("Invalid API key - failed to get access token")

            access_token = token_response.get("access_token")
            if not access_token:
                logger.error("No access token in response for API key validation")
                raise ValueError("Invalid API key - no access token received")

            # Get key info using the access token
            key_info = self._get_semaphore_key_info(access_token, SEMAPHORE_API_KEY_URL)
            if not key_info:
                logger.error("API key validation failed - could not get key info")
                raise ValueError("Invalid API key - validation failed")

            # Update the expiry date with the validated information
            updates["expiry_date"] = key_info["expiryDate"]

            # Set appropriate description based on whether this is insert or update
            if original:  # Update case
                updates[
                    "description"
                ] = f"""Semaphore API key for autotagger.
                 Expiry: {key_info['expiryDate']}.
                 Last updated: {datetime.now(timezone.utc).isoformat()}"""
            else:  # Insert case
                updates[
                    "description"
                ] = f"""Semaphore API key for autotagger.
                 Expiry: {key_info['expiryDate']}.
                 Created: {datetime.now(timezone.utc).isoformat()}"""

            # Ensure category is set
            if "category" not in updates:
                updates["category"] = "api_key"

            # Ensure is_active is set
            if "is_active" not in updates:
                updates["is_active"] = True

            logger.info(
                f"API key validation successful. New expiry: {key_info['expiryDate']}"
            )

        except Exception as e:
            logger.error(f"Error validating Semaphore API key: {e}")
            raise ValueError(f"API key validation failed: {str(e)}")

    def _get_semaphore_access_token(self, api_key: str, token_url: str):
        """Get access token using API key"""
        try:
            payload = f"grant_type=apikey&key={api_key}"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            response = requests.post(
                token_url, headers=headers, data=payload, timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(
                    f"Token request failed: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            return None

    def _get_semaphore_key_info(self, access_token: str, api_key_url: str):
        """Get key information using access token"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(api_key_url, headers=headers, timeout=30)

            if response.status_code == 200:
                key_info = response.json()
                logger.info(
                    f"API key validation successful. Expiry: {key_info.get('expiryDate')}"
                )
                return key_info
            else:
                logger.warning(
                    f"Key info request failed: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Error getting key info: {str(e)}")
            return None
