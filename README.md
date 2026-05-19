# MediTrack — Patient Management System

![CI Pipeline](https://github.com/<your-username>/meditrack/actions/workflows/ci.yml/badge.svg)

A lightweight, simulated **Patient Management System** built in Python, developed as the project placeholder for the research paper:

> **Implementing CI/CD Pipelines and Agile Practices in a Healthcare Patient Management System**
> Lucas Mayer — THD HI-7 — Management and IT-Consulting in Health Service (SS 2026)

> ⚠️ **All patient data in this system is simulated. No real patient information is stored or transmitted.**

---

## Project Structure

```
meditrack/
├── meditrack/
│   ├── __init__.py          # Package exports
│   ├── validation.py        # Shared data validation utilities
│   ├── patient.py           # Patient record management
│   └── appointment.py       # Appointment scheduling logic
├── tests/
│   ├── __init__.py
│   ├── test_validation.py   # Validation module tests
│   ├── test_patient.py      # Patient module tests
│   └── test_appointment.py  # Appointment module tests
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI/CD pipeline
├── requirements.txt
└── README.md
```

---

## CI/CD Pipeline

Every push to `main` and every pull request triggers the five-stage pipeline:

| Stage | Tool | Purpose |
|-------|------|---------|
| 1. Checkout | `actions/checkout` | Fetch latest source code |
| 2. Python setup | `actions/setup-python` | Reproducible Python 3.11 runtime |
| 3. Dependency install | `pip` | Install pytest and ruff |
| 4. Static analysis | `ruff` | Enforce coding standards |
| 5. Unit tests | `pytest` | Validate functional correctness |

---

## Local Setup

```bash
# Clone the repository
git clone https://github.com/<your-username>/meditrack.git
cd meditrack

# Install dependencies
pip install -r requirements.txt

# Run static analysis
ruff check .

# Run all tests
pytest tests/ -v --tb=short
```

---

## Technologies

- **Python 3.11** — Core language
- **pytest** — Automated unit testing
- **ruff** — Static code analysis / linting
- **GitHub Actions** — CI/CD pipeline execution

---

## Academic Context

This project was developed for the *Management and IT-Consulting in Health Service* course at Technische Hochschule Deggendorf (THD). Its purpose is to demonstrate the design and implementation of a CI/CD pipeline and Agile development workflow in a healthcare software context.
