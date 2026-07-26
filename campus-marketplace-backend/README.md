# Campus Marketplace Backend

This repository is for my Capstone Project Milestone 2 backend component.

My project is called **Campus Marketplace**. The purpose of this application is to help university students buy and sell used items on campus, such as textbooks, furniture, electronics, kitchen supplies, and bikes.

For Milestone 2, I focused on the backend API, database design, API testing, and showing that each API operation updates the database correctly.

## Project Overview

Campus Marketplace solves a common student-life problem. Students often use group chats, social media, flyers, or word of mouth to buy and sell used items. These methods are not very organized and can be hard to search or manage.

This backend supports the main features needed for the application:

- Student registration and login
- Listing creation and search
- Listing detail updates
- Listing status updates
- Buyer inquiries
- Admin dashboard metrics
- User and listing data stored in a database

## Technologies Used

- Python
- Flask
- PostgreSQL
- psycopg2
- Flask-CORS
- pytest

I also included a simple SQLite version for local backup testing, but the main backend version for this milestone is the Flask + PostgreSQL version.

## Main Files

| File | Description |
|---|---|
| `app_postgres.py` | Main Flask backend connected to PostgreSQL |
| `schema_postgresql.sql` | PostgreSQL database table design |
| `init_postgres_db.py` | Creates database tables and adds sample data |
| `test_postgres_api.py` | Automated API tests using PostgreSQL |
| `demo_postgres_operations.py` | Demo script showing API responses and database updates |
| `API_DOCUMENTATION.md` | List of APIs with sample JSON input and output |
| `DATABASE_DESIGN.md` | Database tables and relationships |
| `TEST_CASES_RESULTS.md` | Test cases and test results |
| `POSTGRES_TEST_RUN_OUTPUT.txt` | Saved PostgreSQL test output |
| `POSTGRES_DEMO_OUTPUT.txt` | Saved demo output showing database evidence |
| `requirements.txt` | Python dependencies |

## Database Design

The PostgreSQL database includes these main tables:

- `users`
- `categories`
- `listings`
- `inquiries`
- `admin_actions`

The main relationship is that one user can create many listings, one category can have many listings, and one listing can receive many inquiries.

More details are included in `DATABASE_DESIGN.md`.

## API Documentation

The API documentation is in:

```text
API_DOCUMENTATION.md
```

It includes the expected input and output for each API, with sample JSON.

The main APIs include:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/categories`
- `GET /api/listings`
- `GET /api/listings/{listing_id}`
- `POST /api/listings`
- `PUT /api/listings/{listing_id}`
- `PATCH /api/listings/{listing_id}/status`
- `DELETE /api/listings/{listing_id}`
- `POST /api/inquiries`
- `GET /api/admin/dashboard`
- `GET /api/admin/users`

## How to Run

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Set the PostgreSQL environment variables:

```powershell
$env:DB_HOST="localhost"
$env:DB_PORT="7313"
$env:DB_NAME="campus_marketplace"
$env:DB_USER="postgres"
$env:DB_PASSWORD="your_password_here"
```

Initialize the database:

```bash
python init_postgres_db.py
```

Run the backend:

```bash
python app_postgres.py
```

The API runs at:

```text
http://127.0.0.1:5000
```

## How to Test

Run the PostgreSQL API tests:

```bash
python test_postgres_api.py
```

The test result was:

```text
PASS - Register user in PostgreSQL
PASS - Create listing in PostgreSQL
PASS - Search listings from PostgreSQL
PASS - Update listing status in PostgreSQL
PASS - Create inquiry in PostgreSQL
PASS - Remove listing in PostgreSQL
PASS - Admin dashboard from PostgreSQL
Result: 7/7 PostgreSQL API tests passed
```

## Demo Evidence

For the video demo, I used:

```bash
python demo_postgres_operations.py
```

This script shows each REST API operation and then prints the related PostgreSQL table rows after the operation.

This helps prove that each API request updates the database object as expected.

## Issues and Resolutions

One issue I encountered was connecting to PostgreSQL because my local PostgreSQL server was not using the default port `5432`. I found that my PostgreSQL service was running on port `7313`, so I updated the database connection settings.

Another issue was making sure that each API operation actually changed the database. I solved this by creating API test scripts that check the database after each create, update, inquiry, and delete operation.

I also had to separate the demo version from the PostgreSQL version. The SQLite version is useful for simple local testing, but the PostgreSQL version is the main backend component for this milestone.

## Future Improvements

In a future version, I would like to add:

- Real password authentication with stronger security
- Frontend integration with the backend APIs
- Image upload support
- Better admin moderation tools
- More detailed reports for marketplace activity

## Author

Jian Ouyang

Capstone Project Milestone 2 Backend Component
