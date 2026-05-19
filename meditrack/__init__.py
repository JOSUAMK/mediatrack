"""
MediTrack - Patient Management System
======================================
A lightweight, simulated healthcare patient management system
developed as a CI/CD and Agile methodology demonstration project.

All patient data used in this system is simulated.
No real patient information is stored or transmitted.
"""

__version__ = "1.0.0"
__author__ = "Lucas Mayer"

from meditrack.appointment import Appointment, AppointmentRepository, AppointmentStatus, AppointmentType
from meditrack.patient import PatientRecord, PatientRepository
from meditrack.validation import ValidationError

__all__ = [
    "PatientRecord",
    "PatientRepository",
    "Appointment",
    "AppointmentRepository",
    "AppointmentStatus",
    "AppointmentType",
    "ValidationError",
]
