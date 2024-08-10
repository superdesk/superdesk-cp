import logging
import requests
import xml.etree.ElementTree as ET
from superdesk.text_checkers.ai.base import AIServiceBase
import traceback
import superdesk
import json
from typing import (
    Dict,
    List,
    Literal,
    Mapping,
    Optional,
    TypedDict,
    Union,
    overload,
)
import datetime


logger = logging.getLogger(__name__)
session = requests.Session()

TIMEOUT = (5, 30)


def format_relevance(value: str) -> int:
    float_value = float(value)
    percentage = int(float_value * 100)
    return min(percentage, 100)


ResponseType = Mapping[str, Union[str, List[str]]]


class SearchData(TypedDict):
    searchString: str
    language: str


class Item(TypedDict):
    guid: str
    abstract: str
    body_html: str
    headline: str
    language: str
    slugline: str


class Tag(TypedDict):
    altids: Dict[str, str]
    description: str
    name: str
    original_source: str
    qcode: str
    scheme: str
    source: str
    relevance: int
    creator: str


class FeedbackData(TypedDict):
    item: Item
    tags: Dict[str, List[Tag]]


class Semaphore(AIServiceBase):
    """Semaphore autotagging service

    Environment variables SEMAPHORE_BASE_URL, SEMAPHORE_ANALYZE_URL,
    SEMAPHORE_SEARCH_URL, SEMAPHORE_GET_PARENT_URL, SEMAPHORE_CREATE_TAG_URL,
    SEMAPHORE_CREATE_TAG_TASK, SEMAPHORE_CREATE_TAG_QUERY, SEMAPHORE_API_KEY
    """

    name = "semaphore"
    label = "Semaphore autotagging service"

    def __init__(self, app):
        # SEMAPHORE_BASE_URL OR TOKEN_ENDPOINT Goes Here
        self.base_url = app.config.get("SEMAPHORE_BASE_URL")

        #  SEMAPHORE_ANALYZE_URL Goes Here
        self.analyze_url = app.config.get("SEMAPHORE_ANALYZE_URL")

        #  SEMAPHORE_API_KEY Goes Here
        self.api_key = app.config.get("SEMAPHORE_API_KEY")

        #  SEMAPHORE_SEARCH_URL Goes Here
        self.search_url = app.config.get("SEMAPHORE_SEARCH_URL")

        #  SEMAPHORE_GET_PARENT_URL Goes Here
        self.get_parent_url = app.config.get("SEMAPHORE_GET_PARENT_URL")

        #  SEMAPHORE_CREATE_TAG_URL Goes Here
        self.create_tag_url = app.config.get("SEMAPHORE_CREATE_TAG_URL")

        #  SEMAPHORE_CREATE_TAG_TASK Goes Here
        self.create_tag_task = app.config.get("SEMAPHORE_CREATE_TAG_TASK")

        #  SEMAPHORE_CREATE_TAG_QUERY Goes Here
        self.create_tag_query = app.config.get("SEMAPHORE_CREATE_TAG_QUERY")

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
            # Change language based on article language
            if article_language == "fr-CA":
                self.get_parent_url = self.get_parent_url.replace("/en/", "/fr/")
            elif article_language == "en-CA":
                self.get_parent_url = self.get_parent_url.replace("/fr/", "/en/")

            query = qcode
            parent_url = self.get_parent_url + query + frank

            response = session.get(parent_url, headers=headers)
            if response.status_code != 200:
                logging.error(
                    f"Error response: {response.status_code} - {response.text}"
                )
                return []
            response.raise_for_status()
            root = ET.fromstring(response.text)
            path = root.find(".//PATH[@TYPE='Narrower Term']")
            parent_info = []
            if path is not None:
                for field in path.findall("FIELD"):
                    if field.find("CLASS").get("NAME") == "Topic":
                        parent_info.append(
                            {
                                "name": field.get("NAME"),
                                "qcode": field.get("ID"),
                                "relevance": 47,
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
    def analyze_parent_info(self, data: SearchData) -> ResponseType:
        try:
            if not self.base_url or not self.api_key:
                logger.warning(
                    "Semaphore Search is not configured properly, can't \
                    analyze content"
                )
                return {}

            query = data["searchString"]

            article_language = data.get("language")

            if article_language == "fr-CA":
                self.search_url = self.search_url.replace("/en/", "/fr/")
            elif article_language == "en-CA":
                self.search_url = self.search_url.replace("/fr/", "/en/")

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
                    elif "People" in item["classes"]:
                        scheme_url = "http://cv.cp.org/People/"
                    elif "Event" in item["classes"]:
                        scheme_url = "http://cv.cp.org/Events/"
                    elif "Place" in item["classes"]:
                        scheme_url = "http://cv.cp.org/Places/"
                    else:
                        scheme_url = "http://cv.iptc.org/newscodes/mediatopic/"

                    entry = {
                        "name": item["name"],
                        "qcode": item["id"],
                        "source": "Semaphore",
                        "relevance": item.get("relevance", 47),
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
                                "relevance": 47,
                                "altids": {"source_name": "source_id"},
                                "original_source": "original_source_value",
                                "scheme": "http://cv.iptc.org/newscodes/mediatopic/",
                            }
                            result["broader"].append(broader_entry)

                return result


            def convert_to_desired_format(input_data):
                return {
                    "tags": {
                        "subject": [
                            capitalize_name_if_parent_none(tag)
                            for tag in input_data["subject"]
                        ],
                        "organisation": [
                            capitalize_name_if_parent_none(tag)
                            for tag in input_data["organisation"]
                        ],
                        "person": [
                            capitalize_name_if_parent_none(tag)
                            for tag in input_data["person"]
                        ],
                        "event": [
                            capitalize_name_if_parent_none(tag)
                            for tag in input_data["event"]
                        ],
                        "place": [
                            capitalize_name_if_parent_none(tag)
                            for tag in input_data["place"]
                        ],
                        "object": [],
                    },
                    "broader": {
                        "subject": [
                            capitalize_name_if_parent_none(tag)
                            for tag in input_data["broader"]
                        ]
                    },
                }

            root = json.loads(root)
            json_response = transform_xml_response(root, article_language)

            json_response = convert_to_desired_format(json_response)

            return json_response

        except requests.exceptions.RequestException as e:
            traceback.print_exc()
            logger.error(
                f"Semaphore Search request failed. \
                We are in analyze RequestError exception: {str(e)}"
            )
            return {}

    def create_tag_in_semaphore(self, data: FeedbackData) -> ResponseType:
        result_summary: Dict[str, List[str]] = {
            "created_tags": [],
            "failed_tags": [],
            "existing_tags": [],
        }
        try:
            if not self.create_tag_url or not self.api_key:
                logger.warning(
                    "Semaphore Create is not configured properly, \
                    can't analyze content"
                )
                return {}

            url = self.create_tag_url
            task = self.create_tag_task
            query_string = self.create_tag_query
            new_url = url + task + query_string

            headers = {
                "Authorization": f"bearer {self.get_access_token()}",
                "Content-Type": "application/ld+json",
            }

            manual_tags = extract_manual_tags(data)

            for item in manual_tags:
                concept_name = item["name"]
                scheme = item["scheme"]

                id_value = None
                if scheme == "subject":
                    id_value = "http://cv.cp.org/4916d989-2227-4f2d-8632-525cd462ab9f"
                elif scheme == "organisation":
                    id_value = "http://cv.cp.org/e2c332d3-05e0-4dcc-b358-9e4855e80e88"
                elif scheme == "places":
                    id_value = "http://cv.cp.org/c3b17bf6-7969-424d-92ae-966f4f707a95"
                elif scheme == "person":
                    id_value = "http://cv.cp.org/1630a532-329f-43fe-9606-b381330c35cf"
                elif scheme == "event":
                    id_value = "http://cv.cp.org/3c493189-023f-4d14-a2f4-fc7b79735ffc"

                if id_value is None:
                    print(f"Unsupported scheme: {scheme}")
                    result_summary["failed_tags"].append(concept_name)
                    continue

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
                            f"Tag already exists in KMM. Response is 409. The Tag is: {concept_name}"
                        )
                        result_summary["existing_tags"].append(concept_name)
                    else:
                        response.raise_for_status()
                        print(f"Tag Got Created is: {concept_name}")
                        result_summary["created_tags"].append(concept_name)
                except Exception as e:
                    print(f"Failed to create tag: {concept_name}, Error: {e}")
                    result_summary["failed_tags"].append(concept_name)

        except Exception as e:
            print(f"Semaphore Create Tag operation failed: {e}")
            return {"error": f"Create Tag operation failed: {e}"}

        return result_summary

    @overload
    def data_operation(  # noqa: E704
        self,
        verb: str,
        operation: Literal["feedback"],
        name: Optional[str],
        data: FeedbackData,
    ) -> ResponseType: ...

    @overload
    def data_operation(  # noqa: E704
        self,
        verb: str,
        operation: Literal["search"],
        name: Optional[str],
        data: SearchData,
    ) -> ResponseType: ...

    def data_operation(
        self,
        verb: str,
        operation: Literal["search", "feedback"],
        name: Optional[str],
        data,
    ) -> ResponseType:
        if operation == "feedback":
            return self.create_tag_in_semaphore(data)
        if operation == "search":
            return self.search(data)
        return {}

    def search(self, data: SearchData) -> ResponseType:
        try:
            self.output = self.analyze_parent_info(data)
            try:
                updated_output = replace_qcodes(self.output)
                return updated_output
            except Exception as e:
                print(
                    f"Error occurred in replace_qcodes \
                    while Analyzing Parent Info: {e}"
                )
                return self.output
        except Exception as e:
            print(e)
            pass
        return {}

    def analyze(self, item: Item, tags=None) -> ResponseType:
        def transform_xml_response(xml_data):
            response_dict = {
                "subject": [],
                "organisation": [],
                "person": [],
                "event": [],
                "place": [],
            }
            SCHEMES = {
                "Place": "http://cv.cp.org/Places/",
                "Organisation": "http://cv.cp.org/Organizations/",
                "Person": "http://cv.cp.org/Person/",
                "Event": "http://cv.cp.org/Events/",
            }
            media_topic_labels = {}
            media_topic_guids = {}
            processed_values = set()

            # Function to assign parents to the subjects
            def assign_parents(response_dict, media_topic_labels, media_topic_guids):
                label_to_guid_map = {}

                # Map each label path to its corresponding GUID path
                for guid_path in media_topic_guids.keys():
                    guid_parts = guid_path.split("/")
                    for label_path in media_topic_labels.keys():
                        label_parts = label_path.split("/")
                        if len(guid_parts) == len(label_parts):
                            last_guid_part = guid_parts[-1]
                            last_label_part = label_parts[-1]
                            if any(
                                subject["qcode"] == last_guid_part
                                and subject["name"] == last_label_part
                                for subject in response_dict["subject"]
                            ):
                                label_to_guid_map[label_path] = guid_path
                                break

                # Track the maximum relevance score for each parent tag
                max_relevance = {}

                # Iterate over the mapped label and GUID paths
                for label_path, guid_path in label_to_guid_map.items():
                    label_parts = label_path.split("/")
                    guid_parts = guid_path.split("/")
                    for i in range(len(label_parts)):
                        name = label_parts[i]
                        qcode = guid_parts[i]
                        parent_qcode = guid_parts[i - 1] if i > 0 else None
                        relevance = format_relevance(media_topic_labels[label_path])

                        if (
                            qcode not in max_relevance
                            or max_relevance[qcode] < relevance
                        ):
                            max_relevance[qcode] = relevance

                        if not any(
                            subject["qcode"] == qcode
                            for subject in response_dict["subject"]
                        ):
                            subject_data = {
                                "name": name,
                                "qcode": qcode,
                                "parent": parent_qcode if parent_qcode else None,
                                "source": "Semaphore",
                                "creator": "Machine",
                                "relevance": relevance,
                                "altids": {"source_name": "source_id"},
                                "original_source": "original_source_value",
                                "scheme": "http://cv.iptc.org/newscodes/mediatopic/",
                            }
                            add_to_dict("subject", subject_data)
                        else:
                            for subject in response_dict["subject"]:
                                if subject["qcode"] == qcode:
                                    subject["parent"] = parent_qcode
                                    break

                # Propagate the highest relevance score upwards
                for label_path, guid_path in label_to_guid_map.items():
                    guid_parts = guid_path.split("/")
                    for i in range(len(guid_parts) - 1, 0, -1):
                        child_qcode = guid_parts[i]
                        parent_qcode = guid_parts[i - 1]
                        child_relevance = max_relevance[child_qcode]
                        if parent_qcode in max_relevance:
                            if max_relevance[parent_qcode] < child_relevance:
                                max_relevance[parent_qcode] = child_relevance
                        else:
                            max_relevance[parent_qcode] = child_relevance

                # Update relevance scores in response_dict
                for subject in response_dict["subject"]:
                    if subject["qcode"] in max_relevance:
                        subject["relevance"] = max_relevance[subject["qcode"]]

            # Helper function to add data to the dictionary
            def add_to_dict(group, tag_data):
                if tag_data["qcode"] and tag_data not in response_dict[group]:
                    response_dict[group].append(tag_data)

            # Helper function to remove the first index from a string
            def remove_first_index(value: str) -> str:
                parts = value.split("/")
                return "/".join(parts[1:]) if parts else value

            def add_tag(name, value, id, score):
                for tag, scheme in SCHEMES.items():
                    if tag in name:
                        tag_data = {
                            "name": value,
                            "qcode": id if id else "",
                            "creator": "Machine",
                            "source": "Semaphore",
                            "relevance": format_relevance(score),
                            "altids": json.dumps({value: id}),
                            "original_source": "original_source_value",
                            "scheme": scheme,
                        }
                        add_to_dict(tag.lower(), tag_data)
                        break

            root = ET.fromstring(xml_data)
            article_elements = root.find("STRUCTUREDDOCUMENT/ARTICLE")
            system_elements = article_elements.findall("SYSTEM")
            for system_element in system_elements:
                article_elements.remove(system_element)

            for elem in article_elements:
                name = elem.get("name")
                value = elem.get("value")
                score = elem.get("score", 0)
                id = elem.get("id")

                if name in ["Organisation", "Person", "Place", "Event"]:
                    add_tag(name, value, id, score)
                elif name == "Media Topic":
                    qcode = elem.get("id")
                    tag_data = {
                        "name": value,
                        "qcode": qcode,
                        "parent": "",
                        "source": "Semaphore",
                        "creator": "Machine",
                        "relevance": format_relevance(score),
                        "altids": {"source_name": "source_id"},
                        "original_source": "original_source_value",
                        "scheme": "http://cv.iptc.org/newscodes/mediatopic/",
                    }
                    add_to_dict("subject", tag_data)
                elif name == "Media Topic_PATH_LABEL":
                    phrases = value.split("/")
                    # Added check to avoid duplicate CP vocabulary values
                    if phrases[0] == "CP vocabulary":
                        pass
                    else:
                        value = remove_first_index(value)
                        media_topic_labels[value] = score
                elif name == "Media Topic_PATH_GUID":
                    value = remove_first_index(value)
                    last_value = value.split("/")[-1]
                    # Added check to avoid duplicate CP vocabulary values
                    if last_value not in processed_values:
                        media_topic_guids[value] = score
                        processed_values.add(last_value)

            assign_parents(response_dict, media_topic_labels, media_topic_guids)

            return response_dict

        try:
            if not self.base_url or not self.api_key:
                logger.warning(
                    "Semaphore is not configured properly, \
                    can't analyze content"
                )
                return {}

            xml_payload = self.html_to_xml(item)
            payload = {"XML_INPUT": xml_payload}

            headers = {"Authorization": f"bearer {self.get_access_token()}"}

            try:
                response = session.post(self.analyze_url, headers=headers, data=payload)
                response.raise_for_status()
            except Exception as e:
                traceback.print_exc()
                logger.error(f"An error occurred while making the request: {str(e)}")

            root = response.text
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
                f"Semaphore request failed. \
                We are in analyze RequestError exception: {str(e)}"
            )
            return {}

        except Exception as e:
            traceback.print_exc()
            logger.error(f"An error occurred. We are in analyze exception: {str(e)}")
            return {}

    def html_to_xml(self, html_content: Item) -> str:
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
        headline_extended = (
            html_content["abstract"] if "abstract" in html_content else ""
        )
        slugline = html_content["slugline"]
        guid = html_content["guid"]
        env = self.api_key[-4:]
        dateTime = datetime.datetime.now().isoformat()

        # Embed the 'body_html' into the XML template
        xml_output = xml_template.format(
            headline,
            headline_extended,
            body_html,
            slugline,
            guid,
            env,
            dateTime,
        )
        xml_output = clean_html_content(xml_output)

        return xml_output


def extract_manual_tags(data):
    manual_tags: List[Tag] = []

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
