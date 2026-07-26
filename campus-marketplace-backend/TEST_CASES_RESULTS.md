# API Test Cases and Results

The test script is:

```text
test_api.py
```

It starts a temporary backend server, sends REST API requests, and verifies database changes after each operation.

## Test Cases

| # | API Operation | Test Input | Expected Database Result | Status |
|---|---|---|---|---|
| 1 | POST /api/auth/register | New student JSON | New row in users table | PASS |
| 2 | POST /api/listings | New listing JSON | New row in listings table | PASS |
| 3 | GET /api/listings?keyword=monitor | Search query | Matching listing returned | PASS |
| 4 | PATCH /api/listings/{id}/status | status = Pending | listings.status changes to Pending | PASS |
| 5 | POST /api/inquiries | Buyer message JSON | New row in inquiries table | PASS |
| 6 | DELETE /api/listings/{id} | Listing id | listings.status changes to Removed | PASS |
| 7 | GET /api/admin/dashboard | No body | Metrics returned from database | PASS |

## Test Result Output

```text
PASS - Register user
PASS - Create listing
PASS - Search listings
PASS - Update listing status
PASS - Create inquiry
PASS - Remove listing
PASS - Admin dashboard
Result: 7/7 tests passed
```

## PostgreSQL Test Result Output

The Flask backend was also tested against the local PostgreSQL database.

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

## Evidence Requirement

For the video demo, show the database row after each write operation:

- After register: show the new user in `users`.
- After create listing: show the new item in `listings`.
- After status update: show the listing status changed to `Pending`.
- After inquiry: show the new message in `inquiries`.
- After delete/remove: show the listing status changed to `Removed`.

For PostgreSQL video evidence, use:

```text
demo_postgres_operations.py
```

The saved output file is:

```text
POSTGRES_DEMO_OUTPUT.txt
```
