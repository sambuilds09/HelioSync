# HelioSync

HelioSync is a Streamlit-based solar service management application. It connects customers, technicians, and administrators in one workflow for reporting issues, assigning work, tracking maintenance, and collecting feedback.

## Highlights

- Role-based registration and login for users, technicians, and administrators
- Ticket submission with priority and village-based technician assignment
- Technician job, history, earnings, bonus, maintenance, and training views
- Administrative dashboards for users, tickets, analytics, feedback, maintenance, and shared technician locations
- Optional preference for a female technician and safety-focused location sharing/SOS alerts
- SQLite database created automatically on first run

## Requirements

- Python 3.9 or later
- `streamlit`
- `bcrypt`
- `pandas`
- `streamlit-geolocation`

Install the dependencies:

```bash
pip install streamlit bcrypt pandas streamlit-geolocation
```

## Run locally

From the project directory, start the application with:

```bash
streamlit run app.py
```

Then open the local address shown by Streamlit in your browser. HelioSync creates `heliosync.db` automatically if it does not already exist.

## Project structure

```text
app.py                 Main Streamlit application and dashboards
database.py            SQLite connection and schema setup
features/maintenance.py  Maintenance-panel helper
heliosync.db           Local application data (generated at runtime)
```

## Roles

| Role | Main capabilities |
| --- | --- |
| User | Register, submit solar-service tickets, request a female technician, and rate completed work. |
| Technician | View and complete assigned jobs, manage maintenance visits, track earnings, submit feedback, and access training resources. |
| Admin | Manage users and tickets, review analytics and feedback, generate maintenance schedules, and monitor shared safety locations. |

## Data and privacy note

The app stores data in a local SQLite database. Location sharing is intended for technician safety and should only be used with informed consent and appropriate access controls in a production deployment.
