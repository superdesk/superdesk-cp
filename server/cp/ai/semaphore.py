import os
import logging
import requests
import xml.etree.ElementTree as ET
from superdesk.text_checkers.ai.base import AIServiceBase
import traceback
import superdesk
import json
from typing import Any, Dict, List, Mapping, Optional, TypedDict, Union


logger = logging.getLogger(__name__)
session = requests.Session()

TIMEOUT = (5, 30)


ResponseType = Mapping[str, Union[str, List[str]]]


class RequestType(TypedDict, total=False):
    searchString: str
    data: Any


class OperationRequest(TypedDict):
    item: RequestType


class Semaphore(AIServiceBase):
    """Semaphore autotagging service

    Environment variables SEMAPHORE_BASE_URL, SEMAPHORE_ANALYZE_URL, SEMAPHORE_SEARCH_URL, SEMAPHORE_GET_PARENT_URL,
    SEMAPHORE_CREATE_TAG_URL, SEMAPHORE_CREATE_TAG_TASK, SEMAPHORE_CREATE_TAG_QUERY, SEMAPHORE_API_KEY.
    """

    name = "semaphore"
    label = "Semaphore autotagging service"

    def __init__(self, data):
        # SEMAPHORE_BASE_URL OR TOKEN_ENDPOINT Goes Here
        self.base_url = os.getenv("SEMAPHORE_BASE_URL")

        #  SEMAPHORE_ANALYZE_URL Goes Here
        self.analyze_url = os.getenv("SEMAPHORE_ANALYZE_URL")

        #  SEMAPHORE_API_KEY Goes Here
        self.api_key = os.getenv("SEMAPHORE_API_KEY")

        #  SEMAPHORE_SEARCH_URL Goes Here
        self.search_url = os.getenv("SEMAPHORE_SEARCH_URL")

        #  SEMAPHORE_GET_PARENT_URL Goes Here
        self.get_parent_url = os.getenv("SEMAPHORE_GET_PARENT_URL")

        #  SEMAPHORE_CREATE_TAG_URL Goes Here
        self.create_tag_url = os.getenv("SEMAPHORE_CREATE_TAG_URL")

        #  SEMAPHORE_CREATE_TAG_TASK Goes Here
        self.create_tag_task = os.getenv("SEMAPHORE_CREATE_TAG_TASK")

        #  SEMAPHORE_CREATE_TAG_QUERY Goes Here
        self.create_tag_query = os.getenv("SEMAPHORE_CREATE_TAG_QUERY")

        self.output = self.analyze(data)

    def convert_to_desired_format(input_data):
        result = {
            "result": {
                "tags": {
                    "subject": input_data["subject"],
                    "organisation": input_data["organisation"],
                    "person": input_data["person"],
                    "event": input_data["event"],
                    "place": input_data["place"],
                    "object": [],  # Assuming no data for 'object'
                },
                "broader": {"subject": input_data["broader"]},
            }
        }

        return result

    def get_access_token(self):
        """Get access token for Semaphore."""
        url = self.base_url

        payload = f"grant_type=apikey&key={self.api_key}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = session.post(url, headers=headers, data=payload, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json().get("access_token")

    def fetch_parent_info(self, qcode, article_language):
        headers = {"Authorization": f"Bearer {self.get_access_token()}"}
        try:
            frank = "?relationshipType=has%20broader"

            query = qcode
            parent_url = self.get_parent_url + query + frank
            logger.warning("parent_url: %s", parent_url)

            response = session.get(parent_url, headers=headers)
            response.raise_for_status()
            root = ET.fromstring(response.text)
            path = root.find(".//PATH[@TYPE='Narrower Term']")
            parent_info = []
            if path is not None:
                for field in path.findall("FIELD"):
                    if field.find("CLASS").get("NAME") == "Topic":
                        score = field.get("score", "0.47")
                        parent_info.append(
                            {
                                "name": field.get("NAME"),
                                "qcode": field.get("ID"),
                                "relevance": score,
                                "creator": "Human",
                                "parent": None,  # Set to None initially
                            }
                        )
            return parent_info, parent_info[::-1]
            # return parent_info[::-1]  # Reverse to get ancestors in order
        except Exception as e:
            logger.error(f"Error fetching parent info: {str(e)}")
            return []

    # Analyze2 changed name to analyze_parent_info
    def analyze_parent_info(self, html_content: RequestType) -> ResponseType:
        try:
            if not self.base_url or not self.api_key:
                logger.warning(
                    "Semaphore Search is not configured properly, can't analyze content"
                )
                return {}

            query = html_content["searchString"]

            # Extract the language from the html_content dictionary, default to "en_CA" if not present
            article_language = html_content.get("language")

            # If the language is French (fr-CA), replace "en" in the search_url and get_parent_url with "fr"
            if article_language == "fr-CA":
                self.search_url = self.search_url.replace("/en/", "/fr/")
                self.get_parent_url = self.get_parent_url.replace("/en/", "/fr/")
            elif article_language == "en-CA":
                self.search_url = self.search_url.replace("/fr/", "/en/")
                self.get_parent_url = self.get_parent_url.replace("/en/", "/fr/")

            new_url = self.search_url + query + ".json"

            # Make a POST request using XML payload
            headers = {"Authorization": f"bearer {self.get_access_token()}"}

            try:
                response = session.get(new_url, headers=headers)

                response.raise_for_status()
            except Exception as e:
                traceback.print_exc()
                logger.error(f"An error occurred while making the request: {str(e)}")

            root = response.text

            # def transform_xml_response(xml_data):
            def transform_xml_response(api_response, article_language):
                result = {
                    "subject": [],
                    "organisation": [],
                    "person": [],
                    "event": [],
                    "place": [],
                    "broader": [],
                }

                # Process each termHint item in the API response
                for item in api_response["termHints"]:
                    scheme_url = "http://cv.cp.org/"

                    if "Organization" in item["classes"]:
                        scheme_url = "http://cv.cp.org/Organizations/"
                        category = "organisation"
                    elif "People" in item["classes"]:
                        scheme_url = "http://cv.cp.org/People/"
                        category = "person"
                    elif "Event" in item["classes"]:
                        scheme_url = "http://cv.cp.org/Events/"
                        category = "event"
                    elif "Place" in item["classes"]:
                        scheme_url = "http://cv.cp.org/Places/"
                        category = "place"
                    else:
                        # For 'subject', a different scheme might be used
                        category = "subject"
                        scheme_url = "http://cv.iptc.org/newscodes/mediatopic/"

                    entry = {
                        "name": item["name"],
                        "qcode": item["id"],
                        "source": "Semaphore",
                        "relevance": item.get("relevance", "0.47"),
                        "creator": "Human",
                        "altids": {"source_name": "source_id"},
                        "original_source": "original_source_value",
                        "scheme": scheme_url,
                        "parent": None,  # Initial parent assignment
                    }

                    # Assign to correct category based on class
                    if "Organization" in item["classes"]:
                        result["organisation"].append(entry)
                    elif "People" in item["classes"]:
                        result["person"].append(entry)
                    elif "Event" in item["classes"]:
                        result["event"].append(entry)
                    elif "Place" in item["classes"]:
                        result["place"].append(entry)
                    else:
                        # Fetch parent info for each subject item
                        parent_info, reversed_parent_info = self.fetch_parent_info(
                            item["id"], article_language
                        )

                        # Assign the immediate parent to the subject item
                        if parent_info:
                            entry["parent"] = reversed_parent_info[0][
                                "qcode"
                            ]  # Immediate parent is the first in the list
                            entry["scheme"] = "http://cv.iptc.org/newscodes/mediatopic/"

                        result["subject"].append(entry)

                        # Process broader items using reversed_parent_info
                        for i in range(len(reversed_parent_info)):
                            broader_entry = {
                                "name": reversed_parent_info[i]["name"],
                                "qcode": reversed_parent_info[i]["qcode"],
                                "parent": (
                                    reversed_parent_info[i + 1]["qcode"]
                                    if i + 1 < len(reversed_parent_info)
                                    else None
                                ),
                                "creator": "Human",
                                "source": "Semaphore",
                                "relevance": "0.47",
                                "altids": {"source_name": "source_id"},
                                "original_source": "original_source_value",
                                "scheme": "http://cv.iptc.org/newscodes/mediatopic/",
                            }
                            result["broader"].append(broader_entry)

                return result

            def convert_to_desired_format(input_data):
                return {
                    "tags": {
                        "subject": input_data["subject"],
                        "organisation": input_data["organisation"],
                        "person": input_data["person"],
                        "event": input_data["event"],
                        "place": input_data["place"],
                        "object": [],  # Assuming no data for 'object'
                    },
                    "broader": {"subject": input_data["broader"]},
                }

            root = json.loads(root)
            json_response = transform_xml_response(root, article_language)

            json_response = convert_to_desired_format(json_response)

            return json_response

        except requests.exceptions.RequestException as e:
            traceback.print_exc()
            logger.error(
                f"Semaphore Search request failed. We are in analyze RequestError exception: {str(e)}"
            )
            return {}

    def create_tag_in_semaphore(self, html_content: RequestType) -> ResponseType:
        result_summary: Dict[str, List[str]] = {
            "created_tags": [],
            "failed_tags": [],
            "existing_tags": [],
        }
        try:
            if not self.create_tag_url or not self.api_key:
                logger.warning(
                    "Semaphore Create is not configured properly, can't analyze content"
                )
                return {}

            url = self.create_tag_url

            task = self.create_tag_task

            query_string = self.create_tag_query

            new_url = url + task + query_string

            # Make a POST request using XML payload
            headers = {
                "Authorization": f"bearer {self.get_access_token()}",
                "Content-Type": "application/ld+json",
            }

            manual_tags = extract_manual_tags(html_content["data"])

            for item in manual_tags:
                # print(item)

                concept_name = item["name"]
                scheme = item["scheme"]

                if scheme == "subject":
                    id_value = "http://cv.cp.org/4916d989-2227-4f2d-8632-525cd462ab9f"

                elif scheme == "organization":
                    id_value = "http://cv.cp.org/e2c332d3-05e0-4dcc-b358-9e4855e80e88"

                elif scheme == "places":
                    id_value = "http://cv.cp.org/c3b17bf6-7969-424d-92ae-966f4f707a95"

                elif scheme == "person":
                    id_value = "http://cv.cp.org/1630a532-329f-43fe-9606-b381330c35cf"

                elif scheme == "event":
                    id_value = "http://cv.cp.org/3c493189-023f-4d14-a2f4-fc7b79735ffc"

                payload = json.dumps(
                    {
                        "@type": ["skos:Concept"],
                        "rdfs:label": "ConceptNameForUriGeneration",
                        "skos:topConceptOf": {"@id": id_value},
                        "skosxl:prefLabel": [
                            {
                                "@type": ["skosxl:Label"],
                                "skosxl:literalForm": [
                                    {"@value": concept_name, "@language": "en"}
                                ],
                            }
                        ],
                    }
                )

                try:
                    response = session.post(new_url, headers=headers, data=payload)

                    if response.status_code == 409:
                        print(
                            "Tag already exists in KMM. Response is 409 . The Tag is: "
                            + concept_name
                        )
                        result_summary["existing_tags"].append(concept_name)

                    else:
                        response.raise_for_status()
                        print("Tag Got Created is: " + concept_name)
                        result_summary["created_tags"].append(concept_name)
                except Exception as e:
                    print(f"Failed to create tag: {concept_name}, Error: {e}")
                    result_summary["failed_tags"].append(concept_name)

        except Exception as e:
            print(f"Semaphore Create Tag operation failed: {e}")
            return {"error": f"Create Tag operation failed: {e}"}

        return result_summary

    def data_operation(
        self,
        verb: str,
        operation: str,
        name: Optional[str],
        data: OperationRequest,
    ) -> ResponseType:
        if operation == "feedback":
            return self.analyze(data["item"])
        if operation == "search":
            return self.search(data)
        return {}

    def search(self, data) -> ResponseType:
        try:
            print(
                "----------------------------------------------------------------------"
            )
            print(
                "----------------------------------------------------------------------"
            )
            print("Running for Search")

            self.output = self.analyze_parent_info(data)

            try:
                updated_output = replace_qcodes(self.output)
                return updated_output
            except Exception as e:
                print(
                    f"Error occurred in replace_qcodes while Analyzing Parent Info: {e}"
                )
                return self.output
        except Exception as e:
            print(e)
            pass
        return {}

    def analyze(self, html_content: RequestType, tags=None) -> ResponseType:
        try:
            if not self.base_url or not self.api_key:
                logger.warning(
                    "Semaphore is not configured properly, can't analyze content"
                )
                return {}

            # Convert HTML to XML
            xml_payload = self.html_to_xml(html_content)

            payload = {"XML_INPUT": xml_payload}

            # Make a POST request using XML payload
            headers = {"Authorization": f"bearer {self.get_access_token()}"}

            try:
                response = session.post(self.analyze_url, headers=headers, data=payload)

                response.raise_for_status()
            except Exception as e:
                traceback.print_exc()
                logger.error(f"An error occurred while making the request: {str(e)}")

            root = response.text

            def transform_xml_response(xml_data):
                # Parse the XML data
                root = ET.fromstring(xml_data)

                # Find the ARTICLE element
                article_elements = root.find("STRUCTUREDDOCUMENT/ARTICLE")

                # Find all 'SYSTEM' child elements under 'ARTICLE'
                system_elements = article_elements.findall("SYSTEM")

                # Remove each 'SYSTEM' element
                for system_element in system_elements:
                    article_elements.remove(system_element)

                # Initialize a dictionary to hold the transformed data
                response_dict = {
                    "subject": [],
                    "organisation": [],
                    "person": [],
                    "event": [],
                    "place": [],
                }

                # Temporary storage for path labels and GUIDs
                path_labels = {}
                path_guids = {}

                # Helper function to add data to the dictionary if it's not a duplicate and has a qcode
                def add_to_dict(group, tag_data):
                    if tag_data["qcode"] and tag_data not in response_dict[group]:
                        response_dict[group].append(tag_data)

                # Function to adjust score to avoid duplicate score entries for different items
                def adjust_score(score, existing_scores):
                    original_score = float(score)
                    while score in existing_scores:
                        original_score += (
                            0.001  # Increment by the smallest possible amount
                        )
                        score = "{:.3f}".format(
                            original_score
                        )  # Keep score to three decimal places
                    return score

                # Iterate through the XML elements and populate the dictionary
                for element in article_elements.iter():
                    if element.tag == "META":
                        meta_name = element.get("name")
                        meta_value = element.get("value")
                        meta_score = element.get("score", "0")
                        meta_id = element.get("id")
                        logger.warning(f"FXA meta_score {meta_score}")

                        # Adjust score if necessary to avoid duplicates
                        if meta_name in [
                            "Media Topic_PATH_LABEL",
                            "Media Topic_PATH_GUID",
                        ]:
                            meta_score = adjust_score(
                                meta_score,
                                (
                                    path_labels.keys()
                                    if meta_name == "Media Topic_PATH_LABEL"
                                    else path_guids.keys()
                                ),
                            )

                        # Split and process path labels or GUIDs
                        if meta_name == "Media Topic_PATH_LABEL":
                            path_labels[meta_score] = meta_value.split("/")[1:]
                        elif meta_name == "Media Topic_PATH_GUID":
                            path_guids[meta_score] = meta_value.split("/")[1:]

                        # Process 'Media Topic_PATH_LABEL' and 'Media Topic_PATH_GUID'

                        # Process other categories
                        else:
                            group = None
                            if "Organization" in meta_name:
                                group = "organisation"
                                scheme_url = "http://cv.cp.org/Organizations/"
                            elif "Person" in meta_name:
                                group = "person"
                                scheme_url = "http://cv.cp.org/People/"
                            elif "Event" in meta_name:
                                group = "event"
                                scheme_url = "http://cv.cp.org/Events/"
                            elif "Place" in meta_name:
                                group = "place"
                                scheme_url = "http://cv.cp.org/Places/"

                            if group:
                                tag_data = {
                                    "name": meta_value,
                                    "qcode": meta_id if meta_id else "",
                                    "creator": "Machine",
                                    "source": "Semaphore",
                                    "relevance": meta_score,
                                    "altids": f'{{"{meta_value}": "{meta_id}"}}',
                                    "original_source": "original_source_value",
                                    "scheme": scheme_url,
                                }
                                logger.warning(f"FXA tag_data {tag_data}")
                                add_to_dict(group, tag_data)

                # Match path labels with path GUIDs based on scores
                for relevance, labels in path_labels.items():
                    guids = path_guids.get(relevance, [])
                    if len(labels) != len(guids):
                        continue  # Skip if there's a mismatch in the number of labels and GUIDs

                    parent_qcode = None  # Track the parent qcode
                    for label, guid in zip(labels, guids):
                        tag_data = {
                            "name": label,
                            "qcode": guid,
                            "parent": parent_qcode,
                            "source": "Semaphore",
                            "creator": "Machine",
                            "relevance": relevance,
                            "altids": {"source_name": "source_id"},
                            "original_source": "original_source_value",
                            "scheme": "http://cv.iptc.org/newscodes/mediatopic/",
                        }
                        logger.warning(f"FXA tag_data subject {tag_data}")
                        add_to_dict("subject", tag_data)
                        parent_qcode = (
                            guid  # Update the parent qcode for the next iteration
                        )

                return response_dict

            json_response = transform_xml_response(root)

            json_response = capitalize_name_if_parent_none_for_analyze(json_response)

            try:
                updated_output = replace_qcodes(json_response)

                return updated_output

            except Exception as e:
                print(f"Error occurred in replace_qcodes: {e}")
                return json_response

        except requests.exceptions.RequestException as e:
            traceback.print_exc()
            logger.error(
                f"Semaphore request failed. We are in analyze RequestError exception: {str(e)}"
            )
            return {}

        except Exception as e:
            traceback.print_exc()
            logger.error(f"An error occurred. We are in analyze exception: {str(e)}")
            return {}

    def html_to_xml(self, html_content) -> str:
        def clean_html_content(input_str):
            # Remove full HTML tags using regular expressions
            your_string = input_str.replace("<p>", "")
            your_string = your_string.replace("</p>", "")
            your_string = your_string.replace("<br>", "")
            your_string = your_string.replace("&nbsp;", "")
            your_string = your_string.replace("&amp;", "")
            your_string = your_string.replace("&lt;&gt;", "")

            return your_string

        xml_template = """<?xml version="1.0" ?>
                <request op="CLASSIFY">
                <document>
                    <body>&lt;?xml version=&quot;1.0&quot; encoding=&quot;UTF-8&quot;?&gt;
                &lt;story&gt;
                    &lt;headline&gt;{}&lt;/headline&gt;
                    &lt;headline_extended&gt;{}&lt;/headline_extended&gt;
                    &lt;body_html&gt;{}&lt;/body_html&gt;
                    &lt;slugline&gt;{}&lt;/slugline&gt;
                    &lt;guid&gt;{}&lt;/guid&gt;
                    &lt;env&gt;{}&lt;/env&gt;
                    &lt;dateTime&gt;{}&lt;/dateTime&gt;
                &lt;/story&gt;
                </body>
                </document>
                </request>
                """

        body_html = html_content["body_html"]
        headline = html_content["headline"]
        headline_extended = html_content["headline_extended"]
        slugline = html_content["slugline"]
        guid = html_content["guid"]
        env = self.api_key[-4:]
        dateTime = datetime.datetime.now().isoformat()

        # Embed the 'body_html' into the XML template
        xml_output = xml_template.format(
            headline, headline_extended, body_html, slugline, guid, env, dateTime
        )
        xml_output = clean_html_content(xml_output)

        return xml_output


def extract_manual_tags(data):
    manual_tags = []

    if "tags" in data:
        # Loop through each tag type (like 'subject', 'person', etc.)
        for category, tags in data["tags"].items():
            # Loop through each tag in the tag type

            for tag in tags:
                # Check if the source is 'manual'
                if tag.get("source") == "manual":
                    manual_tags.append(tag)

    return manual_tags


def capitalize_name_if_parent_none(tag):
    # Check if 'parent' is None and capitalize the first letter of 'name' if so
    if tag.get("parent") is None:
        tag["name"] = tag["name"].title()
    return tag


def capitalize_name_if_parent_none_for_analyze(response):
    for category in ["subject", "organisation", "person", "event", "place"]:
        for item in response.get(category, []):
            item = capitalize_name_if_parent_none(item)
    return response


def replace_qcodes(output_data):
    cv = superdesk.get_resource_service("vocabularies").find_one(
        req=None, _id="subject_custom"
    )

    # Create a mapping from semaphore_id to qcode
    semaphore_to_qcode = {item["semaphore_id"]: item["qcode"] for item in cv["items"]}

    # Define a function to replace qcodes in a given list
    def replace_in_list(data_list):
        for item in data_list:
            if item["qcode"] in semaphore_to_qcode:
                item["qcode"] = semaphore_to_qcode[item["qcode"]]
            if item.get("parent") and item["parent"] in semaphore_to_qcode:
                item["parent"] = semaphore_to_qcode[item["parent"]]

    # Iterate over different categories and apply the replacement

    category_data = output_data.get("tags", {}).get("subject", [])

    broader_data = output_data.get("broader", {}).get("subject", [])

    for category in ["subject"]:
        if category in output_data:
            replace_in_list(output_data[category])

        elif category_data:
            replace_in_list(category_data)
            replace_in_list(broader_data)

    return output_data


def init_app(app):
    Semaphore(app)
