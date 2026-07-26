import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "demo_campus_marketplace.db"
BASE_URL = "http://127.0.0.1:5060"


def api(method, path, payload=None):
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        BASE_URL + path,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def db_rows(sql, params=()):
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute(sql, params).fetchall()]


def print_section(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def print_json(label, value):
    print(label)
    print(json.dumps(value, indent=2))


def wait_for_api():
    for _ in range(30):
        try:
            api("GET", "/api/health")
            return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError("API server did not start")


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()

    env = os.environ.copy()
    env["CAMPUS_MARKET_DB"] = str(DB_PATH)
    env["PORT"] = "5060"
    server = subprocess.Popen(
        [sys.executable, str(BASE_DIR / "server.py")],
        cwd=BASE_DIR,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        wait_for_api()
        print_section("Database Tables")
        print_json(
            "Tables created in SQLite database:",
            db_rows("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"),
        )

        print_section("1. Register User")
        status, response = api(
            "POST",
            "/api/auth/register",
            {"name": "Video Demo Student", "email": "video.demo@example.edu", "password": "Password123"},
        )
        user_id = response["user"]["user_id"]
        print_json(f"API status {status} response:", response)
        print_json("Database evidence from users table:", db_rows("SELECT user_id, name, email, role, status FROM users WHERE user_id = ?", (user_id,)))

        print_section("2. Create Listing")
        status, response = api(
            "POST",
            "/api/listings",
            {
                "title": "Used Monitor",
                "description": "Good monitor for dorm study desk.",
                "category_id": 3,
                "price": 60,
                "condition": "Good",
                "seller_id": user_id,
            },
        )
        listing_id = response["listing"]["listing_id"]
        print_json(f"API status {status} response:", response)
        print_json("Database evidence from listings table:", db_rows("SELECT listing_id, title, price, status, seller_id FROM listings WHERE listing_id = ?", (listing_id,)))

        print_section("3. Search Listing")
        status, response = api("GET", "/api/listings?keyword=monitor")
        print_json(f"API status {status} response:", response)
        print_json("Database evidence: matching row still exists:", db_rows("SELECT listing_id, title, status FROM listings WHERE title LIKE '%Monitor%'"))

        print_section("4. Update Listing Status")
        status, response = api("PATCH", f"/api/listings/{listing_id}/status", {"status": "Pending"})
        print_json(f"API status {status} response:", response)
        print_json("Database evidence from listings table:", db_rows("SELECT listing_id, title, status FROM listings WHERE listing_id = ?", (listing_id,)))

        print_section("5. Create Inquiry")
        status, response = api(
            "POST",
            "/api/inquiries",
            {"listing_id": listing_id, "buyer_id": 1, "message": "Is this still available?"},
        )
        inquiry_id = response["inquiry"]["inquiry_id"]
        print_json(f"API status {status} response:", response)
        print_json("Database evidence from inquiries table:", db_rows("SELECT inquiry_id, listing_id, buyer_id, message FROM inquiries WHERE inquiry_id = ?", (inquiry_id,)))

        print_section("6. Remove Listing")
        status, response = api("DELETE", f"/api/listings/{listing_id}")
        print_json(f"API status {status} response:", response)
        print_json("Database evidence from listings table:", db_rows("SELECT listing_id, title, status FROM listings WHERE listing_id = ?", (listing_id,)))

        print_section("7. Admin Dashboard")
        status, response = api("GET", "/api/admin/dashboard")
        print_json(f"API status {status} response:", response)
        print_json("Database evidence from listings grouped by status:", db_rows("SELECT status, COUNT(*) AS count FROM listings GROUP BY status ORDER BY status"))

    finally:
        server.terminate()
        server.wait(timeout=5)


if __name__ == "__main__":
    main()
