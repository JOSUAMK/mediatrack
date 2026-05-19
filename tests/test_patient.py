"""
Tests for meditrack.patient
==============================
Covers patient record creation, retrieval, update, deletion,
search, and validation of all required fields.
"""

import pytest
from datetime import date, timedelta

from meditrack.patient import PatientRecord, PatientRepository
from meditrack.validation import ValidationError


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture()
def repo():
    """Return a fresh, empty :class:`PatientRepository` for each test."""
    return PatientRepository()


@pytest.fixture()
def valid_patient_data():
    """Return a valid patient data dictionary."""
    return {
        "patient_id": "PT-100001",
        "first_name": "Anna",
        "last_name": "Schneider",
        "date_of_birth": "1985-03-12",
        "gender": "Female",
        "blood_group": "A+",
        "diagnosis": "Hypertension",
        "treatment": "Lifestyle modification and medication",
        "contact_email": "anna.schneider@example.com",
    }


@pytest.fixture()
def populated_repo(repo, valid_patient_data):
    """Return a repository pre-loaded with one patient record."""
    repo.create_patient(valid_patient_data)
    return repo


# ── PatientRecord unit tests ─────────────────────────────────────────────────

class TestPatientRecord:
    def test_full_name_property(self):
        record = PatientRecord(
            patient_id="PT-000001",
            first_name="Max",
            last_name="Mustermann",
            date_of_birth="1990-01-01",
            gender="Male",
        )
        assert record.full_name == "Max Mustermann"

    def test_age_calculated_correctly(self):
        dob = date.today() - timedelta(days=365 * 30 + 8)  # ~30 years ago
        record = PatientRecord(
            patient_id="PT-000002",
            first_name="Test",
            last_name="User",
            date_of_birth=dob.isoformat(),
            gender="Other",
        )
        assert record.age == 30

    def test_to_dict_contains_expected_keys(self, valid_patient_data):
        record = PatientRecord(**{
            k: v for k, v in valid_patient_data.items()
        })
        d = record.to_dict()
        for key in ["patient_id", "full_name", "date_of_birth", "age", "gender", "blood_group"]:
            assert key in d

    def test_invalid_patient_id_raises(self):
        with pytest.raises(ValidationError):
            PatientRecord(
                patient_id="INVALID",
                first_name="Bad",
                last_name="Id",
                date_of_birth="1990-01-01",
                gender="Male",
            )

    def test_future_dob_raises(self):
        future = (date.today() + timedelta(days=10)).isoformat()
        with pytest.raises(ValidationError, match="cannot be in the future"):
            PatientRecord(
                patient_id="PT-000003",
                first_name="Future",
                last_name="Patient",
                date_of_birth=future,
                gender="Female",
            )

    def test_invalid_gender_raises(self):
        with pytest.raises(ValidationError, match="Invalid gender"):
            PatientRecord(
                patient_id="PT-000004",
                first_name="Test",
                last_name="Patient",
                date_of_birth="1990-01-01",
                gender="Unknown",
            )

    def test_optional_fields_default_to_none(self):
        record = PatientRecord(
            patient_id="PT-000005",
            first_name="Minimal",
            last_name="Record",
            date_of_birth="2000-06-15",
            gender="Other",
        )
        assert record.blood_group is None
        assert record.diagnosis is None
        assert record.treatment is None
        assert record.contact_email is None


# ── PatientRepository CRUD tests ─────────────────────────────────────────────

class TestPatientRepositoryCreate:
    def test_create_valid_patient(self, repo, valid_patient_data):
        record = repo.create_patient(valid_patient_data)
        assert record.patient_id == "PT-100001"
        assert repo.count() == 1

    def test_create_duplicate_id_raises(self, repo, valid_patient_data):
        repo.create_patient(valid_patient_data)
        with pytest.raises(ValueError, match="already exists"):
            repo.create_patient(valid_patient_data)

    def test_create_missing_first_name_raises(self, repo, valid_patient_data):
        del valid_patient_data["first_name"]
        with pytest.raises(ValidationError, match="'first_name'"):
            repo.create_patient(valid_patient_data)

    def test_create_missing_last_name_raises(self, repo, valid_patient_data):
        del valid_patient_data["last_name"]
        with pytest.raises(ValidationError):
            repo.create_patient(valid_patient_data)

    def test_create_missing_dob_raises(self, repo, valid_patient_data):
        del valid_patient_data["date_of_birth"]
        with pytest.raises(ValidationError):
            repo.create_patient(valid_patient_data)

    def test_create_missing_gender_raises(self, repo, valid_patient_data):
        del valid_patient_data["gender"]
        with pytest.raises(ValidationError):
            repo.create_patient(valid_patient_data)

    def test_create_invalid_dob_format_raises(self, repo, valid_patient_data):
        valid_patient_data["date_of_birth"] = "12/03/1985"
        with pytest.raises(ValidationError):
            repo.create_patient(valid_patient_data)

    def test_create_without_optional_fields(self, repo):
        data = {
            "patient_id": "PT-200001",
            "first_name": "Karl",
            "last_name": "Fischer",
            "date_of_birth": "1975-11-30",
            "gender": "Male",
        }
        record = repo.create_patient(data)
        assert record.blood_group is None
        assert record.diagnosis is None


class TestPatientRepositoryRead:
    def test_get_existing_patient(self, populated_repo):
        record = populated_repo.get_patient("PT-100001")
        assert record.last_name == "Schneider"

    def test_get_nonexistent_patient_raises(self, repo):
        with pytest.raises(KeyError):
            repo.get_patient("PT-999999")

    def test_list_patients_returns_all(self, repo, valid_patient_data):
        repo.create_patient(valid_patient_data)
        second = dict(valid_patient_data, patient_id="PT-100002", first_name="Bruno")
        repo.create_patient(second)
        patients = repo.list_patients()
        assert len(patients) == 2

    def test_list_patients_sorted_by_id(self, repo, valid_patient_data):
        repo.create_patient(dict(valid_patient_data, patient_id="PT-100003"))
        repo.create_patient(dict(valid_patient_data, patient_id="PT-100001"))
        repo.create_patient(dict(valid_patient_data, patient_id="PT-100002"))
        ids = [r.patient_id for r in repo.list_patients()]
        assert ids == sorted(ids)

    def test_search_by_name_partial_match(self, repo, valid_patient_data):
        repo.create_patient(valid_patient_data)
        results = repo.search_by_name("Schnei")
        assert len(results) == 1
        assert results[0].patient_id == "PT-100001"

    def test_search_by_name_case_insensitive(self, repo, valid_patient_data):
        repo.create_patient(valid_patient_data)
        results = repo.search_by_name("ANNA")
        assert len(results) == 1

    def test_search_by_name_no_match(self, repo, valid_patient_data):
        repo.create_patient(valid_patient_data)
        results = repo.search_by_name("Nobody")
        assert results == []

    def test_empty_repository_returns_empty_list(self, repo):
        assert repo.list_patients() == []


class TestPatientRepositoryUpdate:
    def test_update_diagnosis(self, populated_repo):
        record = populated_repo.update_patient(
            "PT-100001", {"diagnosis": "Diabetes Type 2"}
        )
        assert record.diagnosis == "Diabetes Type 2"

    def test_update_treatment(self, populated_repo):
        record = populated_repo.update_patient(
            "PT-100001", {"treatment": "Insulin therapy"}
        )
        assert record.treatment == "Insulin therapy"

    def test_update_gender(self, populated_repo):
        record = populated_repo.update_patient(
            "PT-100001", {"gender": "Other"}
        )
        assert record.gender == "Other"

    def test_cannot_update_patient_id_raises(self, populated_repo):
        with pytest.raises(ValueError, match="cannot be changed"):
            populated_repo.update_patient("PT-100001", {"patient_id": "PT-999999"})

    def test_update_nonexistent_patient_raises(self, repo):
        with pytest.raises(KeyError):
            repo.update_patient("PT-999999", {"diagnosis": "Test"})

    def test_update_invalid_field_raises(self, populated_repo):
        with pytest.raises(ValidationError):
            populated_repo.update_patient("PT-100001", {"nonexistent_field": "value"})


class TestPatientRepositoryDelete:
    def test_delete_existing_patient(self, populated_repo):
        populated_repo.delete_patient("PT-100001")
        assert populated_repo.count() == 0

    def test_delete_nonexistent_patient_raises(self, repo):
        with pytest.raises(KeyError):
            repo.delete_patient("PT-999999")

    def test_deleted_patient_not_retrievable(self, populated_repo):
        populated_repo.delete_patient("PT-100001")
        with pytest.raises(KeyError):
            populated_repo.get_patient("PT-100001")

    def test_clear_removes_all_records(self, repo, valid_patient_data):
        repo.create_patient(valid_patient_data)
        repo.clear()
        assert repo.count() == 0
