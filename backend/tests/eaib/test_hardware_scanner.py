"""Tests for HardwareScanner."""
from __future__ import annotations

from deerflow.eaib.body.hardware_scanner import HardwareScanner


def test_scan_returns_dict() -> None:
    scanner = HardwareScanner()
    result = scanner.scan_summary()
    assert isinstance(result, dict)


def test_scan_has_expected_keys() -> None:
    scanner = HardwareScanner()
    result = scanner.scan_summary()
    # Must include at least these top-level keys
    for key in ("os", "cameras", "serial_ports"):
        assert key in result, f"Missing key '{key}' in scan_summary()"


def test_scan_is_repeatable() -> None:
    scanner = HardwareScanner()
    r1 = scanner.scan_summary()
    r2 = scanner.scan_summary()
    assert r1.get("os") == r2.get("os")
