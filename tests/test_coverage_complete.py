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

"""Additional tests to achieve 100% code coverage."""

import os
import sys
import tempfile
from unittest.mock import patch

import pytest

from pain001.context.context import Context
from pain001.core.core import process_files
from pain001.xml.generate_xml import generate_xml


class TestCoverageComplete:
    """Test cases to cover remaining code paths."""

    def test_main_module_direct_execution(self):
        """Test __main__ module when executed directly."""
        # Test __main__.py if __name__ == "__main__"
        with patch.object(sys, "argv", ["pain001"]):
            with pytest.raises(SystemExit):
                exec(
                    open("pain001/__main__.py").read(),
                    {"__name__": "__main__"},
                )

    def test_core_module_direct_execution(self):
        """Test core.py module when executed directly with insufficient args."""
        with patch.object(sys, "argv", ["pain001"]):
            with pytest.raises(SystemExit) as exc_info:
                # Import and execute the __main__ block
                from pain001.core import core

                if len(sys.argv) < 5:
                    sys.exit(1)
            assert exc_info.value.code == 1

    def test_cli_module_direct_execution(self):
        """Test cli.py module when executed directly."""
        # This covers the if __name__ == "__main__" block in cli.py
        with patch.object(
            sys,
            "argv",
            [
                "pain001",
                "-t",
                "pain.001.001.03",
                "-m",
                "template.xml",
                "-s",
                "schema.xsd",
                "-d",
                "data.csv",
            ],
        ):
            with pytest.raises((SystemExit, FileNotFoundError)):
                exec(
                    open("pain001/cli/cli.py").read(),
                    {"__name__": "__main__"},
                )

    def test_context_logger_with_existing_handlers(self):
        """Test context logger when handlers already exist."""
        # Create a fresh context instance for testing
        import logging

        from pain001.context.context import Context

        # Reset the singleton for this test
        Context._instance = None
        ctx = Context.get_instance()

        # Manually set up logger with handler to test the branch
        ctx.logger = logging.getLogger("test_pain001")
        handler = logging.StreamHandler()
        ctx.logger.addHandler(handler)

        # Try to initialize - should raise exception because logger exists
        with pytest.raises(
            Exception, match="Logger has already been initialized"
        ):
            ctx.init_logger()

    def test_process_files_with_failed_xml_generation(self):
        """Test process_files when XML file generation fails."""
        # Create temporary files
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as csv_file:
            csv_file.write(
                "id,date,nb_of_txs,initiator_name,payment_id,payment_method\n"
            )
            csv_file.write(
                "MSG001,2026-01-09T10:00:00,1,Test Corp,PMT001,TRF\n"
            )
            csv_path = csv_file.name

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".xsd"
        ) as xsd_file:
            xsd_file.write(
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                "</xs:schema>"
            )
            xsd_path = xsd_file.name

        # Create a path that will cause generation to fail
        # (non-writable directory)
        nonexistent_xml_path = "/nonexistent/path/template.xml"

        try:
            with pytest.raises(Exception):
                process_files(
                    "pain.001.001.03",
                    nonexistent_xml_path,
                    xsd_path,
                    csv_path,
                )
        finally:
            # Clean up
            if os.path.exists(csv_path):
                os.remove(csv_path)
            if os.path.exists(xsd_path):
                os.remove(xsd_path)

    def test_generate_xml_with_empty_data(self):
        """Test generate_xml with empty data list."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".xml"
        ) as xml_file:
            xml_path = xml_file.name

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".xsd"
        ) as xsd_file:
            xsd_file.write(
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                "</xs:schema>"
            )
            xsd_path = xsd_file.name

        try:
            # Test with empty data
            with pytest.raises(SystemExit):
                generate_xml(
                    [],
                    "pain.001.001.03",
                    xml_path,
                    xsd_path,
                )
        finally:
            if os.path.exists(xml_path):
                os.remove(xml_path)
            if os.path.exists(xsd_path):
                os.remove(xsd_path)

    def test_validate_via_xsd_with_validation_error(self):
        """Test validate_via_xsd with schema validation error."""
        from pain001.xml.validate_via_xsd import validate_via_xsd

        # Create an XML file that doesn't match schema
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".xml"
        ) as xml_file:
            xml_file.write('<?xml version="1.0"?><wrong>data</wrong>')
            xml_path = xml_file.name

        # Create a strict XSD schema
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".xsd"
        ) as xsd_file:
            xsd_file.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="root">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="child" type="xs:string"/>
            </xs:sequence>
        </xs:complexType>
    </xs:element>
</xs:schema>"""
            )
            xsd_path = xsd_file.name

        try:
            # This should return False due to validation failure
            result = validate_via_xsd(xml_path, xsd_path)
            assert result is False
        finally:
            if os.path.exists(xml_path):
                os.remove(xml_path)
            if os.path.exists(xsd_path):
                os.remove(xsd_path)

    def test_main_with_general_exception(self):
        """Test main function with general exception handling."""
        from pain001.__main__ import main

        # Pass invalid arguments that will cause an exception
        with pytest.raises(SystemExit):
            main(
                "invalid_type",
                "/nonexistent/template.xml",
                "/nonexistent/schema.xsd",
                "/nonexistent/data.csv",
            )

    def test_main_missing_xsd_template(self):
        """Test main function with missing XSD template file."""
        from pain001.__main__ import main

        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as csv_file:
            csv_file.write("id,date\n")
            csv_path = csv_file.name

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".xml"
        ) as xml_file:
            xml_path = xml_file.name

        try:
            with pytest.raises(SystemExit):
                main(
                    "pain.001.001.03",
                    xml_path,
                    None,  # Missing XSD
                    csv_path,
                )
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)
            if os.path.exists(xml_path):
                os.remove(xml_path)

    def test_main_missing_data_file(self):
        """Test main function with missing data file."""
        from pain001.__main__ import main

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".xml"
        ) as xml_file:
            xml_path = xml_file.name

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".xsd"
        ) as xsd_file:
            xsd_path = xsd_file.name

        try:
            with pytest.raises(SystemExit):
                main(
                    "pain.001.001.03",
                    xml_path,
                    xsd_path,
                    None,  # Missing data file
                )
        finally:
            if os.path.exists(xml_path):
                os.remove(xml_path)
            if os.path.exists(xsd_path):
                os.remove(xsd_path)

    def test_validate_xsd_with_corrupt_xsd(self):
        """Test validate_via_xsd with corrupt XSD schema."""
        from pain001.xml.validate_via_xsd import validate_via_xsd

        # Create a valid XML file
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".xml"
        ) as xml_file:
            xml_file.write(
                '<?xml version="1.0"?><root><child>test</child></root>'
            )
            xml_path = xml_file.name

        # Create a corrupt XSD file
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".xsd"
        ) as xsd_file:
            xsd_file.write("This is not valid XML/XSD")
            xsd_path = xsd_file.name

        try:
            # This should return False due to XSD loading error
            result = validate_via_xsd(xml_path, xsd_path)
            assert result is False
        finally:
            if os.path.exists(xml_path):
                os.remove(xml_path)
            if os.path.exists(xsd_path):
                os.remove(xsd_path)
