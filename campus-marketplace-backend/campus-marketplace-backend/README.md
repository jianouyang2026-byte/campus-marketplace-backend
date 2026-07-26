# Campus Marketplace Backend Component

This is the Milestone 2 backend component for the Campus Marketplace capstone project.

## Technology

- Python standard library HTTP server
- SQLite database for local testing and demonstration
- SQL schema designed so it can be moved to PostgreSQL with small syntax changes
- Flask + PostgreSQL version is also included for the professor's PostgreSQL-focused module

The original `server.py` version does not require external Python packages. The Flask/PostgreSQL version uses the packages in `requirements.txt`.

## PostgreSQL Setup

PostgreSQL was detected on this computer with this port:

```text
DB_PORT=7313
```

Create environment variables before running the PostgreSQL version:

```powershell
$env:DB_HOST="localhost"
$env:DB_PORT="7313"
$env:DB_NAME="campus_marketplace"
$env:DB_USER="postgres"
$env:DB_PASSWORD="your_postgres_password_here"
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Initialize PostgreSQL tables and seed data:

```bash
python init_postgres_db.py
```

Run the Flask/PostgreSQL API:

```bash
python app_postgres.py
```

## How to Run

```bash
python server.py
```

The API will run at:

```text
http://127.0.0.1:5000
```

The database file will be created automatically:

```text
campus_marketplace.db
```

## How to Test

```bash
python test_api.py
```

The tests start a temporary API server, call the REST APIs, and check the database after each operation.

## How to Demo Database Evidence

```bash
python demo_api_operations.py
```

This script is designed for the Milestone 2 video. It prints each REST API response and then prints the matching database rows after the operation.

## Main API Areas

- Authentication: register and login
- Listings: create, search, view, update, change status, and remove listings
- Inquiries: send a buyer message about a listing
- Admin: view dashboard metrics and users

## Suggested Video Demo

1. Start the API server.
2. Show the database file and tables.
3. Use the test script or API client to call each API.
4. After each create/update/delete operation, show the matching database row changed.
5. Walk through `server.py`, `schema.sql`, and `test_api.py`.
