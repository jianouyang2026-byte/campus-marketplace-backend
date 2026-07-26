import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "test_campus_marketplace.db"
BASE_URL = "http://127.0.0.1:5055"


def request(method, path, payload=None):
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE_URL + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def wait_for_server():
    for _ in range(30):
        try:
            status, _ = request("GET", "/api/health")
            if status == 200:
                return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError("API server did not start")


def db_value(sql, params=()):
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(sql, params).fetchone()
        return dict(row) if row else None


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()

    env = os.environ.copy()
    env["CAMPUS_MARKET_DB"] = str(DB_PATH)
    env["PORT"] = "5055"
    server = subprocess.Popen(
        [sys.executable, str(BASE_DIR / "server.py")],
        cwd=BASE_DIR,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    results = []
    created_listing_id = None
    try:
        wait_for_server()

        status, body = request(
            "POST",
            "/api/auth/register",
            {"name": "Test Student", "email": "test.student@example.edu", "password": "Password123"},
        )
        user_id = body["user"]["user_id"]
        db_user = db_value("SELECT email FROM users WHERE user_id = ?", (user_id,))
        results.append(("Register user", status == 201 and db_user["email"] == "test.student@example.edu"))

        status, body = request(
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
        created_listing_id = body["listing"]["listing_id"]
        db_listing = db_value("SELECT title, price FROM listings WHERE listing_id = ?", (created_listing_id,))
        results.append(("Create listing", status == 201 and db_listing["title"] == "Used Monitor"))

        status, body = request("GET", "/api/listings?keyword=monitor")
        results.append(("Search listings", status == 200 and len(body["listings"]) >= 1))

        status, body = request("PATCH", f"/api/listings/{created_listing_id}/status", {"status": "Pending"})
        db_status = db_value("SELECT status FROM listings WHERE listing_id = ?", (created_listing_id,))
        results.append(("Update listing status", status == 200 and db_status["status"] == "Pending"))

        status, body = request(
            "POST",
            "/api/inquiries",
            {"listing_id": created_listing_id, "buyer_id": 1, "message": "Is this still available?"},
        )
        inquiry_id = body["inquiry"]["inquiry_id"]
        db_inquiry = db_value("SELECT message FROM inquiries WHERE inquiry_id = ?", (inquiry_id,))
        results.append(("Create inquiry", status == 201 and "available" in db_inquiry["message"]))

        status, body = request("DELETE", f"/api/listings/{created_listing_id}")
        db_removed = db_value("SELECT status FROM listings WHERE listing_id = ?", (created_listing_id,))
        results.append(("Remove listing", status == 200 and db_removed["status"] == "Removed"))

        status, body = request("GET", "/api/admin/dashboard")
        results.append(("Admin dashboard", status == 200 and "metrics" in body))

    finally:
        server.terminate()
        server.wait(timeout=5)

    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"{'PASS' if ok else 'FAIL'} - {name}")
    print(f"Result: {passed}/{len(results)} tests passed")

    if passed != len(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
