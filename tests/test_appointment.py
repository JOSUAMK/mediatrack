"""
Tests for meditrack.appointment
==================================
Covers appointment scheduling, double-booking prevention,
past-date rejection, cancellation, completion, and retrieval.
"""

import pytest
from datetime import date, timedelta

from meditrack.appointment import (
    Appointment,
    AppointmentRepository,
    AppointmentStatus,
    AppointmentType,
)
from meditrack.validation import ValidationError


# ── Helpers ──────────────────────────────────────────────────────────────────

def future(days: int = 7) -> str:
    """Return a date string *days* in the future."""
    return (date.today() + timedelta(days=days)).isoformat()


def past(days: int = 1) -> str:
    """Return a date string *days* in the past."""
    return (date.today() - timedelta(days=days)).isoformat()


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def repo():
    """Return a fresh, empty :class:`AppointmentRepository`."""
    return AppointmentRepository()


@pytest.fixture()
def valid_appt_data():
    """Return a valid appointment data dictionary."""
    return {
        "appointment_id": "APPT-00000001",
        "patient_id": "PT-100001",
        "appointment_date": future(7),
        "appointment_type": "Consultation",
        "doctor_name": "Dr. Meier",
        "notes": "Initial consultation for hypertension management",
    }


@pytest.fixture()
def booked_repo(repo, valid_appt_data):
    """Return a repository with one scheduled appointment."""
    repo.schedule_appointment(valid_appt_data)
    return repo


# ── Appointment unit tests ────────────────────────────────────────────────────

class TestAppointmentModel:
    def test_valid_appointment_creation(self, valid_appt_data):
        appt = Appointment(**valid_appt_data)
        assert appt.patient_id == "PT-100001"
        assert appt.status == AppointmentStatus.SCHEDULED

    def test_to_dict_contains_expected_keys(self, valid_appt_data):
        appt = Appointment(**valid_appt_data)
        d = appt.to_dict()
        for key in ["appointment_id", "patient_id", "appointment_date",
                    "appointment_type", "doctor_name", "status"]:
            assert key in d

    def test_default_status_is_scheduled(self, valid_appt_data):
        appt = Appointment(**valid_appt_data)
        assert appt.status == AppointmentStatus.SCHEDULED

    def test_invalid_appointment_type_raises(self, valid_appt_data):
        valid_appt_data["appointment_type"] = "Vacation"
        with pytest.raises(ValidationError, match="Invalid appointment type"):
            Appointment(**valid_appt_data)

    def test_empty_appointment_id_raises(self, valid_appt_data):
        valid_appt_data["appointment_id"] = "  "
        with pytest.raises(ValidationError):
            Appointment(**valid_appt_data)

    def test_past_appointment_date_raises(self, valid_appt_data):
        valid_appt_data["appointment_date"] = past(3)
        with pytest.raises(ValidationError, match="cannot be in the past"):
            Appointment(**valid_appt_data)

    def test_invalid_patient_id_raises(self, valid_appt_data):
        valid_appt_data["patient_id"] = "BADID"
        with pytest.raises(ValidationError):
            Appointment(**valid_appt_data)

    @pytest.mark.parametrize("appt_type", [t.value for t in AppointmentType])
    def test_all_appointment_types_valid(self, valid_appt_data, appt_type):
        valid_appt_data["appointment_type"] = appt_type
        appt = Appointment(**valid_appt_data)
        assert appt.appointment_type.value == appt_type


# ── AppointmentRepository scheduling tests ────────────────────────────────────

class TestScheduleAppointment:
    def test_schedule_valid_appointment(self, repo, valid_appt_data):
        appt = repo.schedule_appointment(valid_appt_data)
        assert appt.appointment_id == "APPT-00000001"
        assert repo.count() == 1

    def test_auto_generated_id_when_not_provided(self, repo, valid_appt_data):
        del valid_appt_data["appointment_id"]
        appt = repo.schedule_appointment(valid_appt_data)
        assert appt.appointment_id.startswith("APPT-")
        assert len(appt.appointment_id) > 5

    def test_double_booking_same_patient_same_date_raises(self, repo, valid_appt_data):
        repo.schedule_appointment(valid_appt_data)
        second = dict(valid_appt_data, appointment_id="APPT-00000002")
        with pytest.raises(ValidationError, match="Double-booking is not permitted"):
            repo.schedule_appointment(second)

    def test_same_patient_different_dates_allowed(self, repo, valid_appt_data):
        repo.schedule_appointment(valid_appt_data)
        second = dict(
            valid_appt_data,
            appointment_id="APPT-00000002",
            appointment_date=future(14),
        )
        appt2 = repo.schedule_appointment(second)
        assert repo.count() == 2
        assert appt2.appointment_id == "APPT-00000002"

    def test_different_patients_same_date_allowed(self, repo, valid_appt_data):
        repo.schedule_appointment(valid_appt_data)
        second = dict(
            valid_appt_data,
            appointment_id="APPT-00000002",
            patient_id="PT-200001",
        )
        repo.schedule_appointment(second)
        assert repo.count() == 2

    def test_missing_patient_id_raises(self, repo, valid_appt_data):
        del valid_appt_data["patient_id"]
        with pytest.raises(ValidationError, match="'patient_id'"):
            repo.schedule_appointment(valid_appt_data)

    def test_missing_appointment_date_raises(self, repo, valid_appt_data):
        del valid_appt_data["appointment_date"]
        with pytest.raises(ValidationError):
            repo.schedule_appointment(valid_appt_data)

    def test_missing_doctor_name_raises(self, repo, valid_appt_data):
        del valid_appt_data["doctor_name"]
        with pytest.raises(ValidationError):
            repo.schedule_appointment(valid_appt_data)

    def test_past_date_raises(self, repo, valid_appt_data):
        valid_appt_data["appointment_date"] = past(5)
        with pytest.raises(ValidationError, match="cannot be in the past"):
            repo.schedule_appointment(valid_appt_data)


# ── AppointmentRepository retrieval tests ─────────────────────────────────────

class TestAppointmentRetrieval:
    def test_get_existing_appointment(self, booked_repo):
        appt = booked_repo.get_appointment("APPT-00000001")
        assert appt.doctor_name == "Dr. Meier"

    def test_get_nonexistent_appointment_raises(self, repo):
        with pytest.raises(KeyError):
            repo.get_appointment("APPT-NONEXISTENT")

    def test_get_appointments_for_patient(self, repo, valid_appt_data):
        repo.schedule_appointment(valid_appt_data)
        second = dict(
            valid_appt_data,
            appointment_id="APPT-00000002",
            appointment_date=future(14),
        )
        repo.schedule_appointment(second)
        results = repo.get_appointments_for_patient("PT-100001")
        assert len(results) == 2

    def test_get_appointments_for_patient_sorted_by_date(self, repo, valid_appt_data):
        repo.schedule_appointment(dict(valid_appt_data, appointment_date=future(14), appointment_id="APPT-00000002"))
        repo.schedule_appointment(dict(valid_appt_data, appointment_date=future(7), appointment_id="APPT-00000001"))
        results = repo.get_appointments_for_patient("PT-100001")
        dates = [a.appointment_date for a in results]
        assert dates == sorted(dates)

    def test_get_appointments_for_unknown_patient_returns_empty(self, booked_repo):
        results = booked_repo.get_appointments_for_patient("PT-999999")
        assert results == []

    def test_list_all_appointments(self, booked_repo, valid_appt_data):
        second = dict(
            valid_appt_data,
            appointment_id="APPT-00000002",
            patient_id="PT-200001",
            appointment_date=future(3),
        )
        booked_repo.schedule_appointment(second)
        assert len(booked_repo.list_appointments()) == 2

    def test_list_appointments_filtered_by_status(self, booked_repo):
        scheduled = booked_repo.list_appointments(status=AppointmentStatus.SCHEDULED)
        assert len(scheduled) == 1
        cancelled = booked_repo.list_appointments(status=AppointmentStatus.CANCELLED)
        assert len(cancelled) == 0


# ── Cancellation and completion ───────────────────────────────────────────────

class TestCancelAppointment:
    def test_cancel_scheduled_appointment(self, booked_repo):
        appt = booked_repo.cancel_appointment("APPT-00000001")
        assert appt.status == AppointmentStatus.CANCELLED

    def test_cancelled_appointment_not_counted_for_double_booking(
        self, repo, valid_appt_data
    ):
        repo.schedule_appointment(valid_appt_data)
        repo.cancel_appointment("APPT-00000001")
        # Now same patient, same date should be bookable again
        second = dict(valid_appt_data, appointment_id="APPT-00000002")
        appt2 = repo.schedule_appointment(second)
        assert appt2.status == AppointmentStatus.SCHEDULED

    def test_cancel_already_cancelled_raises(self, booked_repo):
        booked_repo.cancel_appointment("APPT-00000001")
        with pytest.raises(ValidationError, match="Cancelled"):
            booked_repo.cancel_appointment("APPT-00000001")

    def test_cancel_nonexistent_raises(self, repo):
        with pytest.raises(KeyError):
            repo.cancel_appointment("APPT-NONEXISTENT")


class TestCompleteAppointment:
    def test_complete_scheduled_appointment(self, booked_repo):
        appt = booked_repo.complete_appointment("APPT-00000001")
        assert appt.status == AppointmentStatus.COMPLETED

    def test_complete_already_completed_raises(self, booked_repo):
        booked_repo.complete_appointment("APPT-00000001")
        with pytest.raises(ValidationError, match="Scheduled"):
            booked_repo.complete_appointment("APPT-00000001")

    def test_complete_cancelled_appointment_raises(self, booked_repo):
        booked_repo.cancel_appointment("APPT-00000001")
        with pytest.raises(ValidationError):
            booked_repo.complete_appointment("APPT-00000001")

    def test_complete_nonexistent_raises(self, repo):
        with pytest.raises(KeyError):
            repo.complete_appointment("APPT-NONEXISTENT")


# ── Repository helpers ────────────────────────────────────────────────────────

class TestRepositoryHelpers:
    def test_count_increments_on_schedule(self, repo, valid_appt_data):
        assert repo.count() == 0
        repo.schedule_appointment(valid_appt_data)
        assert repo.count() == 1

    def test_clear_removes_all(self, booked_repo):
        booked_repo.clear()
        assert booked_repo.count() == 0
