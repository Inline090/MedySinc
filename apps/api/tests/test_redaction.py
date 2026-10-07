from app.ai.redaction import redact


def test_a_phone_number_is_removed():
    """A number with enough digits to be a phone number does not survive."""
    assert "9876543210" not in redact("Contact +91 9876543210 for the report")
    assert "98765 43210" not in redact("Mobile 98765 43210")
    assert "[redacted]" in redact("Call 9876543210")


def test_clinical_numbers_are_left_alone():
    """The ten-digit floor is what protects doses, lab values and dates."""

    line = (
        "BP 118/76 mmHg, pulse 72, temp 98.6 F. "
        "Tab Dolo 650 mg, 1/2 tablet twice daily for 5 days. "
        "HbA1c 7.4 percent, fasting glucose 148 mg/dL. "
        "Follow up on 2026-03-14."
    )

    assert redact(line) == line


def test_an_email_is_removed():
    """Email addresses go, because they name a person directly."""
    cleaned = redact("Write to asha.rao+clinic@example.co.in about it")

    assert "asha.rao+clinic@example.co.in" not in cleaned
    assert "[redacted]" in cleaned


def test_a_registration_number_is_left_alone():
    """A council registration is not redacted."""

    line = "Dr Sample Physician, MBBS, MD Reg. No: MCI 12345"

    assert redact(line) == line


def test_names_and_addresses_are_not_touched():
    """The honest limit, written down as a test so nobody assumes otherwise."""

    line = "Dr Sample Physician, 123 Main road"

    assert redact(line) == line


def test_empty_text_is_returned_unchanged():
    """Nothing in, nothing out. No placeholder from an empty string."""
    assert redact("") == ""
