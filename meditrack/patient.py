"""
MediTrack - Patient Record Management Module
=============================================
Handles creation, retrieval, update, and deletion of simulated
patient records. All data is held in memory (no real patient
data is stored or transmitted).
"""

from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import uuid4

from meditrack.validation import (
    ValidationError,
    validate_blood_group,
    validate_date_of_birth,
    validate_gender,
    validate_patient_id,
    validate_required_fields,
)


# ── Data model ──────────────────────────────────────────────────────────────

class PatientRecord:
    """Represents a single simulated patient record."""

    REQUIRED_FIELDS = [
        "patient_id",
        "first_name",
        "last_name",
        "date_of_birth",
        "gender",
    ]

    def __init__(
        self,
        patient_id: str,
        first_name: str,
        last_name: str,
        date_of_birth: str,
        gender: str,
        blood_group: Optional[str] = None,
        diagnosis: Optional[str] = None,
        treatment: Optional[str] = None,
        contact_email: Optional[str] = None,
    ) -> None:
        self.patient_id: str = validate_patient_id(patient_id)
        self.first_name: str = first_name.strip()
        self.last_name: str = last_name.strip()
        self.date_of_birth: date = validate_date_of_birth(date_of_birth)
        self.gender: str = validate_gender(gender)
        self.blood_group: Optional[str] = (
            validate_blood_group(blood_group) if blood_group else None
        )
        self.diagnosis: Optional[str] = diagnosis
        self.treatment: Optional[str] = treatment
        self.contact_email: Optional[str] = contact_email
        self._record_uid: str = str(uuid4())

    # ── Properties ──────────────────────────────────────────────────────

    @property
    def full_name(self) -> str:
        """Return the patient's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self) -> int:
        """Return the patient's current age in whole years."""
        today = date.today()
        years = today.year - self.date_of_birth.year
        # Adjust if birthday hasn't occurred yet this year
        if (today.month, today.day) < (
            self.date_of_birth.month,
            self.date_of_birth.day,
        ):
            years -= 1
        return years

    # ── Serialisation ───────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Return a plain-dict representation of this record."""
        return {
            "patient_id": self.patient_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "date_of_birth": self.date_of_birth.isoformat(),
            "age": self.age,
            "gender": self.gender,
            "blood_group": self.blood_group,
            "diagnosis": self.diagnosis,
            "treatment": self.treatment,
            "contact_email": self.contact_email,
        }

    def __repr__(self) -> str:
        return (
            f"PatientRecord(patient_id={self.patient_id!r}, "
            f"name={self.full_name!r}, dob={self.date_of_birth})"
        )


# ── Repository ──────────────────────────────────────────────────────────────

class PatientRepository:
    """
    In-memory store for :class:`PatientRecord` objects.

    Provides CRUD operations and simple query methods.
    """

    def __init__(self) -> None:
        self._records: dict[str, PatientRecord] = {}

    # ── Create ───────────────────────────────────────────────────────────

    def create_patient(self, data: dict) -> PatientRecord:
        """
        Validate *data* and create a new :class:`PatientRecord`.

        Args:
            data: Dictionary containing at minimum the required fields
                  defined in :attr:`PatientRecord.REQUIRED_FIELDS`.

        Returns:
            The newly created :class:`PatientRecord`.

        Raises:
            ValidationError: If required fields are missing/invalid.
            ValueError: If a patient with the same ID already exists.
        """
        validate_required_fields(data, PatientRecord.REQUIRED_FIELDS)

        patient_id = validate_patient_id(data["patient_id"])
        if patient_id in self._records:
            raise ValueError(
                f"A patient with ID '{patient_id}' already exists."
            )

        record = PatientRecord(
            patient_id=data["patient_id"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            date_of_birth=data["date_of_birth"],
            gender=data["gender"],
            blood_group=data.get("blood_group"),
            diagnosis=data.get("diagnosis"),
            treatment=data.get("treatment"),
            contact_email=data.get("contact_email"),
        )
        self._records[record.patient_id] = record
        return record

    # ── Read ─────────────────────────────────────────────────────────────

    def get_patient(self, patient_id: str) -> PatientRecord:
        """
        Retrieve a patient record by ID.

        Args:
            patient_id: The patient identifier.

        Returns:
            The matching :class:`PatientRecord`.

        Raises:
            KeyError: If no record with the given ID exists.
        """
        pid = validate_patient_id(patient_id)
        if pid not in self._records:
            raise KeyError(f"No patient record found for ID '{pid}'.")
        return self._records[pid]

    def list_patients(self) -> list[PatientRecord]:
        """Return all stored patient records sorted by patient ID."""
        return sorted(self._records.values(), key=lambda r: r.patient_id)

    def search_by_name(self, name_fragment: str) -> list[PatientRecord]:
        """
        Return records whose full name contains *name_fragment*
        (case-insensitive).

        Args:
            name_fragment: Substring to search for.

        Returns:
            List of matching :class:`PatientRecord` objects.
        """
        fragment = name_fragment.strip().lower()
        return [
            r
            for r in self._records.values()
            if fragment in r.full_name.lower()
        ]

    # ── Update ────────────────────────────────────────────────────────────

    def update_patient(self, patient_id: str, updates: dict) -> PatientRecord:
        """
        Apply *updates* to an existing patient record.

        Only the fields present in *updates* are changed; immutable
        fields (``patient_id``) cannot be updated.

        Args:
            patient_id: The patient to update.
            updates: Dictionary of field names and new values.

        Returns:
            The updated :class:`PatientRecord`.

        Raises:
            KeyError: If the patient does not exist.
            ValidationError: If any updated field fails validation.
            ValueError: If an attempt is made to change ``patient_id``.
        """
        if "patient_id" in updates:
            raise ValueError("The 'patient_id' field cannot be changed after creation.")

        record = self.get_patient(patient_id)
        mutable = {
            "first_name", "last_name", "date_of_birth",
            "gender", "blood_group", "diagnosis",
            "treatment", "contact_email",
        }

        for field, value in updates.items():
            if field not in mutable:
                raise ValidationError(f"Field '{field}' is not a valid updatable field.")
            if field == "date_of_birth":
                from meditrack.validation import validate_date_of_birth
                value = validate_date_of_birth(value).isoformat()
                setattr(record, field, validate_date_of_birth(value))
            elif field == "gender":
                setattr(record, field, validate_gender(value))
            elif field == "blood_group":
                setattr(record, field, validate_blood_group(value) if value else None)
            else:
                setattr(record, field, value)
        return record

    # ── Delete ────────────────────────────────────────────────────────────

    def delete_patient(self, patient_id: str) -> None:
        """
        Remove a patient record from the repository.

        Args:
            patient_id: The patient to remove.

        Raises:
            KeyError: If the patient does not exist.
        """
        pid = validate_patient_id(patient_id)
        if pid not in self._records:
            raise KeyError(f"No patient record found for ID '{pid}'.")
        del self._records[pid]

    # ── Helpers ───────────────────────────────────────────────────────────

    def count(self) -> int:
        """Return the total number of stored records."""
        return len(self._records)

    def clear(self) -> None:
        """Remove all records (useful for test teardown)."""
        self._records.clear()
