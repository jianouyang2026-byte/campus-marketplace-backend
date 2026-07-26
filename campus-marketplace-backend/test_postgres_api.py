import os
import time

import psycopg2
import psycopg2.extras

from app_postgres import create_app


def connect_db():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "7313")),
        dbname=os.environ.get("DB_NAME", "campus_marketplace"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", ""),
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def db_row(sql, params=()):
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def main():
    app = create_app()
    client = app.test_client()
    suffix = int(time.time())

    results = []

    response = client.post(
        "/api/auth/register",
        json={
            "name": "PostgreSQL Test Student",
            "email": f"postgres.test.{suffix}@example.edu",
            "password": "Password123",
        },
    )
    user = response.get_json()["user"]
    user_id = user["user_id"]
    saved_user = db_row("SELECT email FROM users WHERE user_id = %s", (user_id,))
    results.append(("Register user in PostgreSQL", response.status_code == 201 and saved_user["email"] == user["email"]))

    response = client.post(
        "/api/listings",
        json={
            "title": "PostgreSQL Demo Monitor",
            "description": "Monitor created during PostgreSQL API test.",
            "category_id": 3,
            "price": 75,
            "condition": "Good",
            "seller_id": user_id,
        },
    )
    listing = response.get_json()["listing"]
    listing_id = listing["listing_id"]
    saved_listing = db_row("SELECT title, status FROM listings WHERE listing_id = %s", (listing_id,))
    results.append(("Create listing in PostgreSQL", response.status_code == 201 and saved_listing["title"] == "PostgreSQL Demo Monitor"))

    response = client.get("/api/listings?keyword=postgresql")
    listings = response.get_json()["listings"]
    results.append(("Search listings from PostgreSQL", response.status_code == 200 and len(listings) >= 1))

    response = client.patch(f"/api/listings/{listing_id}/status", json={"status": "Pending"})
    saved_status = db_row("SELECT status FROM listings WHERE listing_id = %s", (listing_id,))
    results.append(("Update listing status in PostgreSQL", response.status_code == 200 and saved_status["status"] == "Pending"))

    response = client.post(
        "/api/inquiries",
        json={"listing_id": listing_id, "buyer_id": 1, "message": "Is this monitor still available?"},
    )
    inquiry = response.get_json()["inquiry"]
    saved_inquiry = db_row("SELECT message FROM inquiries WHERE inquiry_id = %s", (inquiry["inquiry_id"],))
    results.append(("Create inquiry in PostgreSQL", response.status_code == 201 and "monitor" in saved_inquiry["message"]))

    response = client.delete(f"/api/listings/{listing_id}")
    removed_listing = db_row("SELECT status FROM listings WHERE listing_id = %s", (listing_id,))
    results.append(("Remove listing in PostgreSQL", response.status_code == 200 and removed_listing["status"] == "Removed"))

    response = client.get("/api/admin/dashboard")
    dashboard = response.get_json()
    results.append(("Admin dashboard from PostgreSQL", response.status_code == 200 and "metrics" in dashboard))

    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"{'PASS' if ok else 'FAIL'} - {name}")
    print(f"Result: {passed}/{len(results)} PostgreSQL API tests passed")

    if passed != len(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
