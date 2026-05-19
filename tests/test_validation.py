"""
Tests for meditrack.validation
================================
Covers field presence validation, date format validation,
patient ID format validation, and boundary condition handling.
"""

import pytest
from datetime import date, timedelta

from meditrack.validation import (
    ValidationError,
    validate_appointment_date,
    validate_blood_group,
    validate_date_of_birth,
    validate_date_string,
    validate_gender,
    validate_patient_id,
    validate_required_fields,
)


# ── validate_required_fields ────────────────────────────────────────────────

class TestValidateRequiredFields:
    def test_all_fields_present_passes(self):
        data = {"name": "Alice", "dob": "2000-01-01", "id": "PT-000001"}
        validate_required_fields(data, ["name", "dob", "id"])  # no exception

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError, match="'dob' is missing"):
            validate_required_fields({"name": "Alice"}, ["name", "dob"])

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            validate_required_fields({"name": "  "}, ["name"])

    def test_none_value_raises(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            validate_required_fields({"name": None}, ["name"])

    def test_zero_is_valid_non_empty_value(self):
        # Numeric zero should not be treated as missing
        validate_required_fields({"count": 0}, ["count"])

    def test_empty_required_list_always_passes(self):
        validate_required_fields({}, [])


# ── validate_patient_id ─────────────────────────────────────────────────────

class TestValidatePatientId:
    def test_valid_id(self):
        assert validate_patient_id("PT-123456") == "PT-123456"

    def test_valid_id_with_leading_whitespace(self):
        assert validate_patient_id("  PT-000001  ") == "PT-000001"

    def test_lowercase_prefix_invalid(self):
        with pytest.raises(ValidationError, match="Invalid patient ID"):
            validate_patient_id("pt-123456")

    def test_too_few_digits_invalid(self):
        with pytest.raises(ValidationError):
            validate_patient_id("PT-12345")

    def test_too_many_digits_invalid(self):
        with pytest.raises(ValidationError):
            validate_patient_id("PT-1234567")

    def test_no_hyphen_invalid(self):
        with pytest.raises(ValidationError):
            validate_patient_id("PT123456")

    def test_non_string_raises(self):
        with pytest.raises(ValidationError):
            validate_patient_id(123456)

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError):
            validate_patient_id("")

    def test_all_zeros_valid(self):
        assert validate_patient_id("PT-000000") == "PT-000000"

    def test_all_nines_valid(self):
        assert validate_patient_id("PT-999999") == "PT-999999"


# ── validate_date_string ─────────────────────────────────────────────────────

class TestValidateDateString:
    def test_valid_date(self):
        result = validate_date_string("2024-06-15")
        assert result == date(2024, 6, 15)

    def test_invalid_format_raises(self):
        with pytest.raises(ValidationError, match="invalid date format"):
            validate_date_string("15-06-2024", "test_field")

    def test_slash_format_raises(self):
        with pytest.raises(ValidationError):
            validate_date_string("2024/06/15")

    def test_impossible_date_raises(self):
        with pytest.raises(ValidationError):
            validate_date_string("2024-13-01")  # month 13

    def test_non_string_raises(self):
        with pytest.raises(ValidationError):
            validate_date_string(20240615)

    def test_field_name_in_error_message(self):
        with pytest.raises(ValidationError, match="my_special_field"):
            validate_date_string("bad", "my_special_field")


# ── validate_date_of_birth ──────────────────────────────────────────────────

class TestValidateDateOfBirth:
    def test_valid_past_date(self):
        dob = validate_date_of_birth("1990-05-20")
        assert dob == date(1990, 5, 20)

    def test_future_date_raises(self):
        future = (date.today() + timedelta(days=1)).isoformat()
        with pytest.raises(ValidationError, match="cannot be in the future"):
            validate_date_of_birth(future)

    def test_today_is_valid(self):
        today_str = date.today().isoformat()
        result = validate_date_of_birth(today_str)
        assert result == date.today()

    def test_age_beyond_130_raises(self):
        ancient = "1850-01-01"
        with pytest.raises(ValidationError, match="exceeding 130 years"):
            validate_date_of_birth(ancient)

    def test_invalid_format_raises(self):
        with pytest.raises(ValidationError):
            validate_date_of_birth("01/01/1990")


# ── validate_blood_group ─────────────────────────────────────────────────────

class TestValidateBloodGroup:
    @pytest.mark.parametrize("bg", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
    def test_all_valid_blood_groups(self, bg):
        assert validate_blood_group(bg) == bg

    def test_lowercase_normalised(self):
        assert validate_blood_group("a+") == "A+"

    def test_invalid_type_raises(self):
        with pytest.raises(ValidationError, match="Invalid blood group"):
            validate_blood_group("C+")

    def test_non_string_raises(self):
        with pytest.raises(ValidationError):
            validate_blood_group(None)


# ── validate_gender ──────────────────────────────────────────────────────────

class TestValidateGender:
    @pytest.mark.parametrize("g", ["Male", "Female", "Other", "Prefer not to say"])
    def test_valid_genders(self, g):
        assert validate_gender(g) == g

    def test_invalid_gender_raises(self):
        with pytest.raises(ValidationError, match="Invalid gender"):
            validate_gender("Unknown")

    def test_non_string_raises(self):
        with pytest.raises(ValidationError):
            validate_gender(42)


# ── validate_appointment_date ────────────────────────────────────────────────

class TestValidateAppointmentDate:
    def test_future_date_valid(self):
        future = (date.today() + timedelta(days=7)).isoformat()
        result = validate_appointment_date(future)
        assert result > date.today()

    def test_today_is_valid(self):
        today_str = date.today().isoformat()
        result = validate_appointment_date(today_str)
        assert result == date.today()

    def test_past_date_raises(self):
        past = (date.today() - timedelta(days=1)).isoformat()
        with pytest.raises(ValidationError, match="cannot be in the past"):
            validate_appointment_date(past)

    def test_invalid_format_raises(self):
        with pytest.raises(ValidationError):
            validate_appointment_date("next Monday")
