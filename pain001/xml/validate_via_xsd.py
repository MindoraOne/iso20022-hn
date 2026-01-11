import xmlschema
from defusedxml import ElementTree as defused_et
from defusedxml.ElementTree import ParseError

# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


def validate_via_xsd(xml_file_path: str, xsd_file_path: str) -> bool:
    """
    Validates an XML file against an XSD schema.

    Args:
        xml_file_path (str): Path to the XML file to validate.
        xsd_file_path (str): Path to the XSD schema file.

    Returns:
        bool: True if the XML file is valid, False otherwise.
    """

    # TODO: cache parsed schemas for repeated calls in a single run to avoid reload cost.
    # Load XML file into an ElementTree object using defusedxml for security.
    try:
        xml_tree = defused_et.parse(xml_file_path)
    except (ParseError, OSError) as e:
        print(f"Error parsing XML file: {e}")
        return False

    # Load XSD schema into an XMLSchema object.
    try:
        xsd = xmlschema.XMLSchema(xsd_file_path)
    except (xmlschema.XMLSchemaException, ParseError, OSError) as e:
        print(f"Error loading XSD schema: {e}")
        return False

    # Validate XML file against XSD schema.
    try:
        is_valid = xsd.is_valid(xml_tree)
    except xmlschema.XMLSchemaException as e:
        print(f"Error validating XML: {e}")
        return False

    # Return True if XML file is valid, False otherwise.
    return is_valid
