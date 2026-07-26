import json
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


def db_rows(sql, params=()):
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]


def print_section(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def print_json(label, value):
    print(label)
    print(json.dumps(value, indent=2, default=str))


def main():
    app = create_app()
    client = app.test_client()
    suffix = int(time.time())

    print_section("PostgreSQL Database Tables")
    print_json(
        "Tables in campus_marketplace:",
        db_rows(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
            """
        ),
    )

    print_section("1. Register User")
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Video PostgreSQL Student",
            "email": f"video.postgres.{suffix}@example.edu",
            "password": "Password123",
        },
    )
    body = response.get_json()
    user_id = body["user"]["user_id"]
    print_json(f"API status {response.status_code} response:", body)
    print_json(
        "Database evidence from users table:",
        db_rows("SELECT user_id, name, email, role, status FROM users WHERE user_id = %s", (user_id,)),
    )

    print_section("2. Create Listing")
    response = client.post(
        "/api/listings",
        json={
            "title": "PostgreSQL Video Monitor",
            "description": "Created through Flask API for the video demo.",
            "category_id": 3,
            "price": 85,
            "condition": "Good",
            "seller_id": user_id,
        },
    )
    body = response.get_json()
    listing_id = body["listing"]["listing_id"]
    print_json(f"API status {response.status_code} response:", body)
    print_json(
        "Database evidence from listings table:",
        db_rows("SELECT listing_id, title, price, status, seller_id FROM listings WHERE listing_id = %s", (listing_id,)),
    )

    print_section("3. Search Listing")
    response = client.get("/api/listings?keyword=video")
    print_json(f"API status {response.status_code} response:", response.get_json())
    print_json(
        "Database evidence: matching row exists:",
        db_rows("SELECT listing_id, title, status FROM listings WHERE title ILIKE %s", ("%Video%",)),
    )

    print_section("4. Update Listing Status")
    response = client.patch(f"/api/listings/{listing_id}/status", json={"status": "Pending"})
    print_json(f"API status {response.status_code} response:", response.get_json())
    print_json(
        "Database evidence from listings table:",
        db_rows("SELECT listing_id, title, status FROM listings WHERE listing_id = %s", (listing_id,)),
    )

    print_section("5. Create Inquiry")
    response = client.post(
        "/api/inquiries",
        json={"listing_id": listing_id, "buyer_id": 1, "message": "Is this still available?"},
    )
    body = response.get_json()
    inquiry_id = body["inquiry"]["inquiry_id"]
    print_json(f"API status {response.status_code} response:", body)
    print_json(
        "Database evidence from inquiries table:",
        db_rows("SELECT inquiry_id, listing_id, buyer_id, message FROM inquiries WHERE inquiry_id = %s", (inquiry_id,)),
    )

    print_section("6. Remove Listing")
    response = client.delete(f"/api/listings/{listing_id}")
    print_json(f"API status {response.status_code} response:", response.get_json())
    print_json(
        "Database evidence from listings table:",
        db_rows("SELECT listing_id, title, status FROM listings WHERE listing_id = %s", (listing_id,)),
    )

    print_section("7. Admin Dashboard")
    response = client.get("/api/admin/dashboard")
    print_json(f"API status {response.status_code} response:", response.get_json())
    print_json(
        "Database evidence grouped by status:",
        db_rows("SELECT status, COUNT(*) AS count FROM listings GROUP BY status ORDER BY status"),
    )


if __name__ == "__main__":
    main()
