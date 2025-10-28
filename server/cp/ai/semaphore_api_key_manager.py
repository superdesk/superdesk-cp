# server/cp/ai/semaphore_api_key_manager.py
import logging
import requests
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import superdesk

logger = logging.getLogger(__name__)


class SemaphoreAPIKeyManager:
    """Manages Semaphore API keys with automatic renewal using Superdesk vocabularies"""

    def __init__(self, app):
        self.base_url = app.config.get("SEMAPHORE_BASE_URL")
        self.token_url = app.config.get("SEMAPHORE_TOKEN_URL")
        self.api_key_url = app.config.get("SEMAPHORE_API_KEY_URL")
        self.current_key = None
        self.key_expiry = None
        self.renewal_threshold_days = 7

    def _ensure_api_config_loaded(self):
        """Ensure app_config is loaded when needed (lazy loading)"""
        try:
            # Try to get the service - it might not be available yet
            api_config_service = superdesk.get_resource_service("app_config")
            semaphore_api_config = api_config_service.find_one(
                req=None, key="semaphore_api_key"
            )

            if semaphore_api_config:
                if semaphore_api_config.get("value"):
                    api_key = semaphore_api_config["value"]
                    self.current_key = api_key
                    expiry_date = semaphore_api_config.get("expiry_date", "")
                    if expiry_date:
                        try:
                            self.key_expiry = datetime.fromisoformat(
                                expiry_date.replace("Z", "+00:00")
                            )
                        except Exception as e:
                            logger.warning(
                                f"Could not parse expiry from description: {e}"
                            )
                            self.key_expiry = None
                    else:
                        self.key_expiry = None

        except Exception as e:
            logger.warning(f"Could not load key from app_config: {str(e)}")

    def get_valid_api_key(self) -> str:
        """Get a valid API key, renewing if necessary"""
        # Simple cache for valid keys
        self._ensure_api_config_loaded()
        if self.current_key and not self._is_key_expired_or_near_expiry():
            return self.current_key

        if self._is_key_expired_or_near_expiry():
            self._renew_api_key()

        if not self.current_key:
            raise ValueError("No valid API key available")

        return self.current_key

    def _is_key_expired_or_near_expiry(self) -> bool:
        """Check if current API key is expired or will expire within threshold"""
        current_time = datetime.now(timezone.utc)

        if not self.key_expiry:
            return True

        # Add buffer time to avoid edge cases
        threshold_date = current_time + timedelta(days=self.renewal_threshold_days)

        is_expired = self.key_expiry <= threshold_date

        return is_expired

    def _renew_api_key(self):
        """Renew the API key using Semaphore API"""
        try:
            # First, get current key info to check expiry
            current_key_info = self._get_current_key_info()

            if current_key_info and not self._is_key_expired_or_near_expiry():
                # Key is still valid, just update our local state
                self.current_key = current_key_info.get("apikey")
                self.key_expiry = datetime.fromisoformat(
                    current_key_info.get("expiryDate").replace("Z", "+00:00")
                )
                return

            # Generate new key
            new_key_data = self._generate_new_key()

            if new_key_data and "apikey" in new_key_data:
                self.current_key = new_key_data["apikey"]
                self.key_expiry = datetime.fromisoformat(
                    new_key_data["expiryDate"].replace("Z", "+00:00")
                )

                # Persist the new key to vocabularies
                self._persist_key(new_key_data)

            else:
                logger.error("Failed to get valid API key from renewal endpoint")

        except Exception as e:
            logger.error(f"Failed to renew API key: {str(e)}")
            if not self.current_key:
                logger.error("No current key available, raising error")
                raise

    def _get_current_key_info(self) -> Optional[Dict[str, Any]]:
        """Get current API key information from Semaphore"""
        try:
            # First get access token using current key
            if not self.current_key:
                logger.warning("No current key available for getting key info")
                return None

            token_response = self._get_access_token(self.current_key)
            if not token_response:
                logger.error("Failed to get access token for current key")
                return None

            access_token = token_response.get("access_token")
            if not access_token:
                logger.error("No access token in response")
                return None

            # Get current key info
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(self.api_key_url, headers=headers, timeout=30)

            if response.status_code == 200:
                key_info = response.json()
                return key_info
            else:
                logger.error(
                    f"Failed to get key info: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Error getting current key info: {str(e)}")
            return None

    def _generate_new_key(self) -> Optional[Dict[str, Any]]:
        """Generate a new API key from Semaphore"""

        try:
            # Get access token using current key
            token_response = self._get_access_token(self.current_key)
            if not token_response:
                return None

            access_token = token_response.get("access_token")
            if not access_token:
                return None

            # Generate new key
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.put(self.api_key_url, headers=headers, timeout=30)

            if response.status_code == 200:
                new_key_data = response.json()
                return new_key_data
            else:
                return None

        except Exception as e:
            logger.error(f"Error generating new API key: {str(e)}")
            return None

    def _get_access_token(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get access token using API key"""

        try:
            payload = f"grant_type=apikey&key={api_key}"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            response = requests.post(
                self.token_url, headers=headers, data=payload, timeout=30
            )

            if response.status_code == 200:
                token_data = response.json()
                return token_data
            else:
                return None

        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            return None

    def _persist_key(self, key_data: Dict[str, Any]):
        """Store key information in Superdesk app_config collection"""
        api_config_service = superdesk.get_resource_service("app_config")

        try:
            # Prepare key info for storage
            key_info = {
                "key": "semaphore_api_key",
                "value": key_data["apikey"],
                "description": f"""Semaphore API key for autotagger.
                 Expiry: {key_data['expiryDate']}.
                 Last renewed: {datetime.now(timezone.utc).isoformat()}""",
                "category": "api_key",
                "is_active": True,
                "expiry_date": key_data["expiryDate"],
            }

            # Check if key already exists
            existing = api_config_service.find_one(req=None, key="semaphore_api_key")

            if existing:
                try:
                    # Try the update
                    api_config_service.update(
                        existing["_id"],  # id
                        key_info,  # updates
                        existing,  # original document
                    )

                    # Verify the update actually worked
                    updated = api_config_service.find_one(
                        req=None, key="semaphore_api_key"
                    )

                    if updated and updated.get("value") == key_data["apikey"]:
                        return
                    else:
                        raise RuntimeError(
                            "Update appeared to succeed but verification failed"
                        )

                except Exception as update_error:
                    logger.error(f"Update failed: {update_error}")
                    raise
            else:
                api_config_service.create([key_info])

        except Exception as e:
            logger.error(f"Could not store key info in app_config: {str(e)}")
            raise
