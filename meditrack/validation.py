"""
MediTrack - Shared Data Validation Module
==========================================
Provides reusable validation utilities for patient records and
appointment data across the MediTrack Patient Management System.
"""

import re
from datetime import date, datetime


# ── Constants ──────────────────────────────────────────────────────────────

PATIENT_ID_PATTERN = re.compile(r"^PT-\d{6}$")
DATE_FORMAT = "%Y-%m-%d"
VALID_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
VALID_GENDERS = {"Male", "Female", "Other", "Prefer not to say"}
MIN_PATIENT_AGE_YEARS = 0
MAX_PATIENT_AGE_YEARS = 130


# ── Exceptions ──────────────────────────────────────────────────────────────

class ValidationError(ValueError):
    """Raised when a validation rule is violated."""


# ── Field-level validators ─────────────────────────────────────────────────

def validate_required_fields(data: dict, required: list[str]) -> None:
    """
    Ensure all required keys are present and non-empty in *data*.

    Args:
        data: Dictionary of field names to values.
        required: List of field names that must be present and non-empty.

    Raises:
        ValidationError: If any required field is missing or blank.
    """
    for field in required:
        if field not in data:
            raise ValidationError(f"Required field '{field}' is missing.")
        value = data[field]
        if value is None or (isinstance(value, str) and value.strip() == ""):
            raise ValidationError(f"Required field '{field}' must not be empty.")


def validate_patient_id(patient_id: str) -> str:
    """
    Validate that *patient_id* matches the format PT-XXXXXX (six digits).

    Args:
        patient_id: The patient identifier string to validate.

    Returns:
        The validated patient ID (stripped).

    Raises:
        ValidationError: If the format is invalid.
    """
    if not isinstance(patient_id, str):
        raise ValidationError("Patient ID must be a string.")
    pid = patient_id.strip()
    if not PATIENT_ID_PATTERN.match(pid):
        raise ValidationError(
            f"Invalid patient ID '{pid}'. Expected format: PT-XXXXXX (six digits)."
        )
    return pid


def validate_date_string(date_str: str, field_name: str = "date") -> date:
    """
    Parse and validate a date string in YYYY-MM-DD format.

    Args:
        date_str: Date string to parse.
        field_name: Name of the field (used in error messages).

    Returns:
        A :class:`datetime.date` object.

    Raises:
        ValidationError: If the string cannot be parsed.
    """
    if not isinstance(date_str, str):
        raise ValidationError(f"Field '{field_name}' must be a string in YYYY-MM-DD format.")
    try:
        return datetime.strptime(date_str.strip(), DATE_FORMAT).date()
    except ValueError:
        raise ValidationError(
            f"Field '{field_name}' has invalid date format '{date_str}'. "
            "Expected YYYY-MM-DD."
        )


def validate_date_of_birth(dob_str: str) -> date:
    """
    Validate a date-of-birth string: must be in the past and within
    plausible human lifespan bounds.

    Args:
        dob_str: Date-of-birth string (YYYY-MM-DD).

    Returns:
        A :class:`datetime.date` object.

    Raises:
        ValidationError: If the date is invalid, in the future, or
            outside the plausible age range.
    """
    dob = validate_date_string(dob_str, "date_of_birth")
    today = date.today()

    if dob > today:
        raise ValidationError("Date of birth cannot be in the future.")

    age_years = (today - dob).days / 365.25
    if age_years > MAX_PATIENT_AGE_YEARS:
        raise ValidationError(
            f"Date of birth implies an age exceeding {MAX_PATIENT_AGE_YEARS} years."
        )
    return dob


def validate_blood_group(blood_group: str) -> str:
    """
    Validate that *blood_group* is one of the recognised ABO/Rh types.

    Args:
        blood_group: Blood group string (e.g. 'A+', 'O-').

    Returns:
        The validated blood group (stripped and upper-cased).

    Raises:
        ValidationError: If the value is not a recognised blood group.
    """
    if not isinstance(blood_group, str):
        raise ValidationError("Blood group must be a string.")
    bg = blood_group.strip().upper()
    if bg not in VALID_BLOOD_GROUPS:
        raise ValidationError(
            f"Invalid blood group '{bg}'. "
            f"Valid values: {sorted(VALID_BLOOD_GROUPS)}."
        )
    return bg


def validate_gender(gender: str) -> str:
    """
    Validate gender field against the accepted vocabulary.

    Args:
        gender: Gender string to validate.

    Returns:
        The validated gender (stripped).

    Raises:
        ValidationError: If the value is not in the accepted vocabulary.
    """
    if not isinstance(gender, str):
        raise ValidationError("Gender must be a string.")
    g = gender.strip()
    if g not in VALID_GENDERS:
        raise ValidationError(
            f"Invalid gender '{g}'. Valid values: {sorted(VALID_GENDERS)}."
        )
    return g


def validate_appointment_date(appointment_date_str: str) -> date:
    """
    Validate that an appointment date is not in the past.

    Args:
        appointment_date_str: Appointment date string (YYYY-MM-DD).

    Returns:
        A :class:`datetime.date` object.

    Raises:
        ValidationError: If the date is invalid or in the past.
    """
    appt_date = validate_date_string(appointment_date_str, "appointment_date")
    if appt_date < date.today():
        raise ValidationError(
            f"Appointment date '{appointment_date_str}' cannot be in the past."
        )
    return appt_date
