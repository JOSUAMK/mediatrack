"""
MediTrack - Appointment Scheduling Module
==========================================
Manages the lifecycle of patient appointments including creation,
retrieval, cancellation, and enforcement of scheduling business rules
(no double-booking, future-only dates).
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional
from uuid import uuid4

from meditrack.validation import (
    ValidationError,
    validate_appointment_date,
    validate_patient_id,
    validate_required_fields,
)


# ── Enumerations ────────────────────────────────────────────────────────────

class AppointmentStatus(str, Enum):
    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    NO_SHOW = "No Show"


class AppointmentType(str, Enum):
    CONSULTATION = "Consultation"
    FOLLOW_UP = "Follow-Up"
    DIAGNOSTIC = "Diagnostic"
    PROCEDURE = "Procedure"
    EMERGENCY = "Emergency"


# ── Data model ──────────────────────────────────────────────────────────────

class Appointment:
    """Represents a single scheduled patient appointment."""

    REQUIRED_FIELDS = [
        "appointment_id",
        "patient_id",
        "appointment_date",
        "appointment_type",
        "doctor_name",
    ]

    def __init__(
        self,
        appointment_id: str,
        patient_id: str,
        appointment_date: str,
        appointment_type: str,
        doctor_name: str,
        notes: Optional[str] = None,
        status: AppointmentStatus = AppointmentStatus.SCHEDULED,
    ) -> None:
        if not appointment_id or not appointment_id.strip():
            raise ValidationError("appointment_id must not be empty.")
        self.appointment_id: str = appointment_id.strip()
        self.patient_id: str = validate_patient_id(patient_id)
        self.appointment_date: date = validate_appointment_date(appointment_date)
        self.appointment_type: AppointmentType = self._parse_type(appointment_type)
        self.doctor_name: str = doctor_name.strip()
        self.notes: Optional[str] = notes
        self.status: AppointmentStatus = status

    @staticmethod
    def _parse_type(value: str) -> AppointmentType:
        """Parse and validate appointment type."""
        try:
            return AppointmentType(value)
        except ValueError:
            valid = [t.value for t in AppointmentType]
            raise ValidationError(
                f"Invalid appointment type '{value}'. Valid values: {valid}."
            )

    # ── Serialisation ───────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Return a plain-dict representation of this appointment."""
        return {
            "appointment_id": self.appointment_id,
            "patient_id": self.patient_id,
            "appointment_date": self.appointment_date.isoformat(),
            "appointment_type": self.appointment_type.value,
            "doctor_name": self.doctor_name,
            "notes": self.notes,
            "status": self.status.value,
        }

    def __repr__(self) -> str:
        return (
            f"Appointment(id={self.appointment_id!r}, "
            f"patient={self.patient_id!r}, "
            f"date={self.appointment_date}, "
            f"status={self.status.value!r})"
        )


# ── Repository ──────────────────────────────────────────────────────────────

class AppointmentRepository:
    """
    In-memory store for :class:`Appointment` objects.

    Enforces scheduling business rules:
    - Appointments must be on a present or future date.
    - A patient cannot have two appointments on the same date
      (double-booking prevention).
    """

    def __init__(self) -> None:
        self._appointments: dict[str, Appointment] = {}

    # ── Helpers ───────────────────────────────────────────────────────────

    def _generate_id(self) -> str:
        """Generate a unique appointment ID."""
        return f"APPT-{uuid4().hex[:8].upper()}"

    def _check_double_booking(
        self,
        patient_id: str,
        appointment_date: date,
        exclude_id: Optional[str] = None,
    ) -> None:
        """
        Raise :class:`ValidationError` if *patient_id* already has an
        active appointment on *appointment_date*.

        Args:
            patient_id: Patient to check.
            appointment_date: Proposed appointment date.
            exclude_id: Appointment ID to skip (used during updates).
        """
        for appt in self._appointments.values():
            if appt.appointment_id == exclude_id:
                continue
            if (
                appt.patient_id == patient_id
                and appt.appointment_date == appointment_date
                and appt.status == AppointmentStatus.SCHEDULED
            ):
                raise ValidationError(
                    f"Patient '{patient_id}' already has a scheduled appointment "
                    f"on {appointment_date}. Double-booking is not permitted."
                )

    # ── Create ────────────────────────────────────────────────────────────

    def schedule_appointment(self, data: dict) -> Appointment:
        """
        Validate *data* and schedule a new appointment.

        If ``appointment_id`` is not provided, one is auto-generated.

        Args:
            data: Dictionary containing appointment fields.

        Returns:
            The newly created :class:`Appointment`.

        Raises:
            ValidationError: If required fields are invalid or a
                double-booking would result.
        """
        required = [
            "patient_id",
            "appointment_date",
            "appointment_type",
            "doctor_name",
        ]
        validate_required_fields(data, required)

        appointment_id = data.get("appointment_id") or self._generate_id()
        patient_id = validate_patient_id(data["patient_id"])
        appointment_date = validate_appointment_date(data["appointment_date"])

        self._check_double_booking(patient_id, appointment_date)

        appt = Appointment(
            appointment_id=appointment_id,
            patient_id=patient_id,
            appointment_date=data["appointment_date"],
            appointment_type=data["appointment_type"],
            doctor_name=data["doctor_name"],
            notes=data.get("notes"),
        )
        self._appointments[appt.appointment_id] = appt
        return appt

    # ── Read ──────────────────────────────────────────────────────────────

    def get_appointment(self, appointment_id: str) -> Appointment:
        """
        Retrieve an appointment by ID.

        Raises:
            KeyError: If no appointment with the given ID exists.
        """
        if appointment_id not in self._appointments:
            raise KeyError(
                f"No appointment found with ID '{appointment_id}'."
            )
        return self._appointments[appointment_id]

    def get_appointments_for_patient(
        self, patient_id: str
    ) -> list[Appointment]:
        """
        Return all appointments for *patient_id*, sorted by date.

        Args:
            patient_id: Patient identifier to filter by.

        Returns:
            List of :class:`Appointment` objects.
        """
        pid = validate_patient_id(patient_id)
        return sorted(
            [a for a in self._appointments.values() if a.patient_id == pid],
            key=lambda a: a.appointment_date,
        )

    def list_appointments(
        self, status: Optional[AppointmentStatus] = None
    ) -> list[Appointment]:
        """
        Return all appointments, optionally filtered by *status*.

        Args:
            status: If provided, only appointments with this status
                are returned.

        Returns:
            List of :class:`Appointment` objects sorted by date.
        """
        results = list(self._appointments.values())
        if status is not None:
            results = [a for a in results if a.status == status]
        return sorted(results, key=lambda a: a.appointment_date)

    # ── Update ────────────────────────────────────────────────────────────

    def cancel_appointment(self, appointment_id: str) -> Appointment:
        """
        Mark an appointment as cancelled.

        Args:
            appointment_id: The appointment to cancel.

        Returns:
            The updated :class:`Appointment`.

        Raises:
            KeyError: If the appointment does not exist.
            ValidationError: If the appointment is already cancelled
                or completed.
        """
        appt = self.get_appointment(appointment_id)
        if appt.status in (
            AppointmentStatus.CANCELLED,
            AppointmentStatus.COMPLETED,
        ):
            raise ValidationError(
                f"Appointment '{appointment_id}' has status "
                f"'{appt.status.value}' and cannot be cancelled."
            )
        appt.status = AppointmentStatus.CANCELLED
        return appt

    def complete_appointment(self, appointment_id: str) -> Appointment:
        """
        Mark an appointment as completed.

        Args:
            appointment_id: The appointment to complete.

        Returns:
            The updated :class:`Appointment`.

        Raises:
            KeyError: If the appointment does not exist.
            ValidationError: If the appointment is not in Scheduled status.
        """
        appt = self.get_appointment(appointment_id)
        if appt.status != AppointmentStatus.SCHEDULED:
            raise ValidationError(
                f"Only 'Scheduled' appointments can be completed. "
                f"Current status: '{appt.status.value}'."
            )
        appt.status = AppointmentStatus.COMPLETED
        return appt

    # ── Helpers ───────────────────────────────────────────────────────────

    def count(self) -> int:
        """Return the total number of stored appointments."""
        return len(self._appointments)

    def clear(self) -> None:
        """Remove all appointments (useful for test teardown)."""
        self._appointments.clear()
