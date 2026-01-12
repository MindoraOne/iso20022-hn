"""Tests for enforce_slos.py script."""

from unittest.mock import patch

from scripts.enforce_slos import (
    main,
    read_coverage_xml,
    validate_coverage,
    validate_slo,
)


class TestReadCoverageXml:
    """Test read_coverage_xml function."""

    def test_read_coverage_xml_nonexistent_file(self, tmp_path):
        """Test read_coverage_xml with non-existent file."""
        coverage_file = tmp_path / "nonexistent.xml"
        total_cov, module_cov = read_coverage_xml(coverage_file)
        assert total_cov == 0.0
        assert not module_cov

    def test_read_coverage_xml_invalid_file(self, tmp_path):
        """Test read_coverage_xml with invalid XML."""
        coverage_file = tmp_path / "coverage.xml"
        coverage_file.write_text("invalid xml")
        total_cov, module_cov = read_coverage_xml(coverage_file)
        assert total_cov == 0.0
        assert not module_cov

    def test_read_coverage_xml_valid_file(self, tmp_path):
        """Test read_coverage_xml with valid XML."""
        coverage_file = tmp_path / "coverage.xml"
        xml_content = """<?xml version="1.0" ?>
<coverage line-rate="0.9765" branch-rate="0.9428">
    <package name="pain001" line-rate="0.95" branch-rate="0.94"/>
</coverage>"""
        coverage_file.write_text(xml_content)
        total_cov, module_cov = read_coverage_xml(coverage_file)
        assert total_cov == 97.65
        assert "pain001" in module_cov
        assert module_cov["pain001"] == 95.0


class TestValidateCoverage:
    """Test validate_coverage function."""

    def test_validate_coverage_meets_floor(self, capsys):
        """Test validate_coverage when meets floor."""
        result = validate_coverage(96.0, 95.0)
        assert result is True
        captured = capsys.readouterr()
        assert "PASS" in captured.out

    def test_validate_coverage_below_floor(self, capsys):
        """Test validate_coverage when below floor."""
        result = validate_coverage(94.0, 95.0)
        assert result is False
        captured = capsys.readouterr()
        assert "FAIL" in captured.out

    def test_validate_coverage_exact_floor(self, capsys):
        """Test validate_coverage at exact floor."""
        result = validate_coverage(95.0, 95.0)
        assert result is True
        captured = capsys.readouterr()
        assert "PASS" in captured.out


class TestValidateSlo:
    """Test validate_slo function."""

    def test_validate_slo_met(self, capsys):
        """Test validate_slo when met."""
        result = validate_slo("Linting", 10.0, 15.0)
        assert result is True
        captured = capsys.readouterr()
        assert "PASS" in captured.out

    def test_validate_slo_exceeded(self, capsys):
        """Test validate_slo when exceeded."""
        result = validate_slo("Linting", 20.0, 15.0)
        assert result is False
        captured = capsys.readouterr()
        assert "FAIL" in captured.out

    def test_validate_slo_exact_threshold(self, capsys):
        """Test validate_slo at exact threshold."""
        result = validate_slo("Linting", 15.0, 15.0)
        assert result is True
        captured = capsys.readouterr()
        assert "PASS" in captured.out


class TestMain:
    """Test main function."""

    @patch("scripts.enforce_slos.read_coverage_xml")
    def test_main_all_pass(self, mock_read_cov, capsys):
        """Test main when all checks pass."""
        mock_read_cov.return_value = (97.0, {"pain001": 97.0})
        with patch("pathlib.Path.exists", return_value=False):
            result = main()
        assert result == 0
        captured = capsys.readouterr()
        assert "Integrity Verified" in captured.out

    @patch("scripts.enforce_slos.read_coverage_xml")
    def test_main_coverage_fails(self, mock_read_cov, capsys):
        """Test main when coverage fails."""
        mock_read_cov.return_value = (90.0, {"pain001": 90.0})
        with patch("pathlib.Path.exists", return_value=False):
            result = main()
        assert result == 1
        captured = capsys.readouterr()
        assert "FAIL" in captured.out or "violation" in captured.out.lower()
