import logging
import json
from typing import Dict, List, Literal, Mapping, Optional, TypedDict, Union, overload
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import requests
from superdesk.text_checkers.ai.base import AIServiceBase
import os
from dotenv import load_dotenv
import html

load_dotenv()

logger = logging.getLogger(__name__)
ResponseType = Mapping[str, Union[str, List[str]]]


class TranslateData(TypedDict):
    guid: str
    source_language: str
    target_language: str
    translation_type: str
    payload: Dict[str, str]


class Translate(AIServiceBase):
    name = "translate"
    label = "Translation service"

    TRANSLATION_TYPE_BASIC = "basic"
    TRANSLATION_TYPE_ADVANCED_NMT = "advanced_nmt"
    TRANSLATION_TYPE_ADVANCED_LLM = "advanced_llm"
    TRANSLATION_TYPE_ADAPTIVE = "adaptive"
    TRANSLATION_TYPE_DEEPL = "deepl"

    def __init__(self, app):
        # Define constant variables using environment variables
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        self.GOOGLE_API_URL = os.getenv("GOOGLE_API_URL")
        self.GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
        self.GOOGLE_PROJECT_LOCATION = os.getenv("GOOGLE_PROJECT_LOCATION")
        self.DEEPL_AUTH_KEY = os.getenv("DEEPL_AUTH_KEY")
        self.DEEPL_API_URL = os.getenv("DEEPL_API_URL")

        self.credentials = {}
        credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_json:
            try:
                info = json.loads(credentials_json)
                self.credentials = (
                    service_account.Credentials.from_service_account_info(
                        info,
                        scopes=["https://www.googleapis.com/auth/cloud-platform"],
                    )
                )
            except Exception as e:
                logger.error(f"Error loading Google credentials: {str(e)}")

        self.parent = f"projects/{self.GOOGLE_PROJECT_ID}/locations/{self.GOOGLE_PROJECT_LOCATION}"
        self.model_path = f"{self.parent}/models/general"

    def translate(self, item: TranslateData, *args) -> ResponseType:
        try:
            self.validate_request_data(item)
            translation_type = item.get("translation_type", "basic")
            translator = self.get_translator(translation_type)
            return translator(item)
        except Exception as e:
            self.handle_error(e, "Translation")

    def analyze(self, item: TranslateData, *args) -> ResponseType:
        try:
            self.validate_request_data(item)
            translation_type = item.get("translation_type", "basic")
            translator = self.get_translator(translation_type)
            result = translator(item)
            return result
        except Exception as e:
            return self.handle_error(e, "Translation")

    def get_translator(self, translation_type):
        if translation_type == self.TRANSLATION_TYPE_BASIC:
            return self.translate_basic
        elif translation_type in {
            self.TRANSLATION_TYPE_ADVANCED_NMT,
            self.TRANSLATION_TYPE_ADVANCED_LLM,
        }:
            return self.translate_advanced
        elif translation_type == self.TRANSLATION_TYPE_ADAPTIVE:
            return self.translate_adaptive
        elif translation_type == self.TRANSLATION_TYPE_DEEPL:
            return self.translate_deepl
        else:
            return self.translate_basic

    def translate_basic(self, item: TranslateData) -> ResponseType:
        try:
            texts, self.paths = self._extract_texts_to_translate(item)

            sanitized_texts = []
            for text in texts:
                if not isinstance(text, str):
                    logger.warning(
                        f"Non-string text found: {text}, converting to string"
                    )
                    text = str(text)
                sanitized_texts.append(text)

            if not sanitized_texts:
                return {"translated_payload": item["payload"], **item}

            if self.credentials.expired or self.credentials.token is None:
                self.credentials.refresh(Request())

            url = f"{self.GOOGLE_API_URL}/v2"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.credentials.token}",
                "x-goog-user-project": self.GOOGLE_PROJECT_ID,
            }
            payload = {
                "q": sanitized_texts,
                "target": item["target_language"],
                "source": item["source_language"],
                "format": (
                    "html" if any("<" in text for text in sanitized_texts) else "text"
                ),
            }

            response = requests.post(url, headers=headers, json=payload)

            if not response.ok:
                logger.error(
                    f"Translation API error: Status {response.status_code}, Response: {response.text}"
                )
            response.raise_for_status()

            response_data = response.json()

            return self._prepare_translated_payload(
                item,
                response_data["data"]["translations"],
                translation_key="translatedText",
            )
        except Exception as e:
            logger.error(f"Translation error details: {str(e)}", exc_info=True)
            return self.handle_error(e, "Basic translation")

    def translate_advanced(self, item: TranslateData) -> ResponseType:
        try:
            texts, self.paths = self._extract_texts_to_translate(item)
            if self.credentials.expired or self.credentials.token is None:
                self.credentials.refresh(Request())

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.credentials.token}",
            }
            payload = {
                "contents": texts,
                "targetLanguageCode": item["target_language"],
                "sourceLanguageCode": item["source_language"],
                "model": self._get_model_path(item["translation_type"]),
            }

            url = f"https://translate.googleapis.com/v3/{self.parent}:translateText"

            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            translations = response.json().get("translations", [])
            return self._prepare_translated_payload(
                item, translations, translation_key="translatedText"
            )
        except Exception as e:
            self.handle_error(e, "Advanced translation")

    def translate_adaptive(self, item: TranslateData) -> ResponseType:
        return "Not implemented"

    def translate_deepl(self, item: TranslateData) -> ResponseType:
        texts, self.paths = self._extract_texts_to_translate(item)

        if not texts:
            logger.warning("No texts to translate")
            return {"translated_payload": item["payload"], **item}

        try:

            separator = "|||||"
            joined_texts = separator.join(texts)

            headers = {
                "Authorization": f"DeepL-Auth-Key {self.DEEPL_AUTH_KEY}",
                "Content-Type": "application/json",
                "User-Agent": "YourApp/1.2.3",
            }

            payload = {
                "text": [joined_texts],
                "target_lang": item["target_language"],
                "source_lang": item["source_language"],
            }

            response = requests.post(self.DEEPL_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            return self._prepare_translated_payload_deepl(item, response_data)

        except Exception as e:
            logger.error(f"DeepL translation failed: {str(e)}", exc_info=True)
            raise Exception(f"DeepL translation failed: {str(e)}")

    def handle_error(self, e: Exception, context: str):
        logger.error(f"{context} failed: {str(e)}")
        return f"{context} failed: {str(e)}"

    def _prepare_translated_payload_deepl(self, data, result):
        try:
            separator = "|||||"
            translations = result["translations"][0]["text"]
            translations = translations.split(separator)
            result = {}

            def build_nested_dict(path_parts, value, target_dict):
                current = target_dict
                for i, part in enumerate(path_parts[:-1]):
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[path_parts[-1]] = value

            for path, translation in zip(self.paths, translations):
                build_nested_dict(path, translation, result)

            return {"translated_payload": result, **data}
        except Exception as e:
            raise Exception(f"Error preparing translated payload: {str(e)}")

    def _prepare_translated_payload(
        self, data, translations, translation_key="translatedText"
    ):
        result = {}

        def build_nested_dict(path_parts, value, target_dict):
            current = target_dict
            for i, part in enumerate(path_parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[path_parts[-1]] = value

        for path, translation in zip(self.paths, translations):
            translated_text = html.unescape(
                getattr(translation, translation_key)
                if hasattr(translation, translation_key)
                else translation[translation_key]
            )
            build_nested_dict(path, translated_text, result)

        return {"translated_payload": result, **data}

    def _get_model_path(self, translation_type):
        if translation_type == "advanced_nmt":
            return self.model_path + "/nmt"
        elif translation_type == "advanced_llm":
            return self.model_path + "/translation-llm"
        else:
            raise ValueError("Invalid translation type for advanced translation")

    @overload
    def data_operation(
        self,
        verb: str,
        operation: Literal["translate"],
        name: Optional[str],
        data: TranslateData,
    ) -> ResponseType:
        ...

    def data_operation(
        self,
        verb: str,
        operation: Literal["translate"],
        name: Optional[str],
        data: TranslateData,
    ) -> ResponseType:
        if operation == "translate":
            return self.translate(data)

    def validate_request_data(self, data):
        if not data:
            raise Exception("No data provided")

        required_fields = [
            "translation_type",
            "source_language",
            "target_language",
            "payload",
        ]
        for field in required_fields:
            if field not in data:
                raise Exception(f"Missing required field: {field}")

        valid_translation_types = [
            "basic",
            "advanced_nmt",
            "advanced_llm",
            "adaptive",
            "deepl",
        ]

        if data["translation_type"] not in valid_translation_types:
            raise Exception("Translation Type not valid")
        translate_fields = [k for k in data["payload"].keys()]
        if not translate_fields:
            raise Exception("No fields to translate inside payload")

    def _extract_texts_to_translate(self, item: TranslateData) -> List[str]:
        texts = []
        paths = []

        def extract_strings(obj, current_path=[]):
            if isinstance(obj, str):
                if obj.strip():  # Only include non-empty strings
                    texts.append(obj)
                    paths.append(current_path)
            elif isinstance(obj, dict):
                for key, value in obj.items():
                    extract_strings(value, current_path + [key])
            elif isinstance(obj, list):
                for i, value in enumerate(value):
                    extract_strings(value, current_path + [str(i)])

        extract_strings(item["payload"])
        return texts, paths

    def deepl_create_glossary(
        self, name: str, source_lang: str, target_lang: str, entries: List[str]
    ) -> dict:
        url = f"{self.DEEPL_API_URL}/v2/glossaries"
        headers = {
            "Authorization": f"DeepL-Auth-Key {self.DEEPL_AUTH_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "name": name,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "entries": "\n".join(
                entries
            ),  # Assuming entries are in "source\ttarget" format
            "entries_format": "tsv",
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.handle_error(e, "Creating glossary")

    def deepl_list_glossaries(self) -> List[dict]:
        url = f"{self.DEEPL_API_URL}/v2/glossaries"
        headers = {
            "Authorization": f"DeepL-Auth-Key {self.DEEPL_AUTH_KEY}",
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get("glossaries", [])
        except Exception as e:
            self.handle_error(e, "Listing glossaries")

    def deepl_retrieve_glossary(self, glossary_id: str) -> dict:
        url = f"{self.DEEPL_API_URL}/v2/glossaries/{glossary_id}"
        headers = {
            "Authorization": f"DeepL-Auth-Key {self.DEEPL_AUTH_KEY}",
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.handle_error(e, "Retrieving glossary details")

    def deepl_retrieve_glossary_entries_by_name(self, glossary_name: str) -> List[str]:
        try:
            glossaries = self.deepl_list_glossaries()
            existing_glossary = next(
                (g for g in glossaries if g["name"] == glossary_name), None
            )

            if not existing_glossary:
                raise Exception(f"Glossary '{glossary_name}' not found")

            glossary_id = existing_glossary["glossary_id"]
            url = f"{self.DEEPL_API_URL}/v2/glossaries/{glossary_id}/entries"
            headers = {
                "Authorization": f"DeepL-Auth-Key {self.DEEPL_AUTH_KEY}",
                "Accept": "text/tab-separated-values",
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.text.splitlines()  # Assuming TSV format
        except Exception as e:
            self.handle_error(e, "Retrieving glossary entries")

    def deepl_delete_glossary(self, glossary_id: str) -> dict:
        """Delete a specific glossary."""
        url = f"{self.DEEPL_API_URL}/v2/glossaries/{glossary_id}"
        headers = {
            "Authorization": f"DeepL-Auth-Key {self.DEEPL_AUTH_KEY}",
        }
        try:
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            return {"message": "Glossary deleted successfully"}
        except Exception as e:
            self.handle_error(e, "Deleting glossary")

    def deepl_add_entries_to_glossary(self, name: str, new_entries: List[str]) -> dict:
        try:
            glossaries = self.deepl_list_glossaries()
            existing_glossary = next((g for g in glossaries if g["name"] == name), None)

            if not existing_glossary:
                raise Exception(f"Glossary '{name}' not found")

            current_entries = self.deepl_retrieve_glossary_entries_by_name(name)

            updated_entries = current_entries + new_entries

            return self.deepl_update_glossary(
                name,
                existing_glossary["source_lang"],
                existing_glossary["target_lang"],
                updated_entries,
            )

        except Exception as e:
            return self.handle_error(e, "Adding entries to glossary")

    def deepl_update_glossary(
        self, name: str, source_lang: str, target_lang: str, new_entries: List[str]
    ) -> dict:
        try:
            glossaries = self.deepl_list_glossaries()

            existing_glossary = next((g for g in glossaries if g["name"] == name), None)

            if existing_glossary:
                self.deepl_delete_glossary(existing_glossary["glossary_id"])

            return self.deepl_create_glossary(
                name, source_lang, target_lang, new_entries
            )

        except Exception as e:
            return self.handle_error(e, "Updating glossary")


def init_app(app):
    return Translate(app)
