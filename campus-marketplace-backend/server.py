import hashlib
import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("CAMPUS_MARKET_DB", BASE_DIR / "campus_marketplace.db"))
STATUSES = {"Available", "Pending", "Sold", "Removed"}


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def connect_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def row_to_dict(row):
    return dict(row) if row else None


def send_json(handler, status_code, payload):
    body = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,PATCH,DELETE,OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    if length == 0:
        return {}
    raw = handler.rfile.read(length).decode("utf-8")
    return json.loads(raw)


def init_db(seed=True):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect_db() as db:
        schema = (BASE_DIR / "schema.sql").read_text(encoding="utf-8")
        db.executescript(schema)

        if not seed:
            return

        for category in ["Textbooks", "Furniture", "Electronics", "Kitchen", "Transportation"]:
            db.execute(
                "INSERT OR IGNORE INTO categories (category_name) VALUES (?)",
                (category,),
            )

        users = [
            ("Jian Ouyang", "jian@example.edu", "student"),
            ("Maya Chen", "maya@example.edu", "student"),
            ("Campus Admin", "admin@example.edu", "admin"),
        ]
        for name, email, role in users:
            db.execute(
                """
                INSERT OR IGNORE INTO users (name, email, password_hash, role)
                VALUES (?, ?, ?, ?)
                """,
                (name, email, hash_password("Password123"), role),
            )

        listing_count = db.execute("SELECT COUNT(*) AS count FROM listings").fetchone()["count"]
        if listing_count == 0:
            db.executescript(
                """
                INSERT INTO listings
                  (title, description, category_id, price, condition, status, seller_id, image_url)
                VALUES
                  ('Calculus Textbook, 9th Edition', 'Used for one semester with notes.', 1, 38, 'Good', 'Available', 1, NULL),
                  ('Compact Study Desk', 'Small desk that fits well in a dorm room.', 2, 55, 'Good', 'Available', 2, NULL),
                  ('Noise-Canceling Headphones', 'Great for studying in the library.', 3, 95, 'Like New', 'Pending', 2, NULL),
                  ('Dorm Kitchen Starter Set', 'Includes pan, pot, cutting board, and utensils.', 4, 26, 'Good', 'Sold', 1, NULL);
                """
            )


def listing_query(where_clause="", params=()):
    sql = f"""
        SELECT
          l.listing_id,
          l.title,
          l.description,
          c.category_id,
          c.category_name AS category,
          l.price,
          l.condition,
          l.status,
          l.seller_id,
          u.name AS seller_name,
          l.image_url,
          l.created_at,
          l.updated_at
        FROM listings l
        JOIN categories c ON c.category_id = l.category_id
        JOIN users u ON u.user_id = l.seller_id
        {where_clause}
        ORDER BY l.created_at DESC, l.listing_id DESC
    """
    with connect_db() as db:
        return [row_to_dict(row) for row in db.execute(sql, params).fetchall()]


class CampusMarketplaceHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_OPTIONS(self):
        send_json(self, 200, {"message": "ok"})

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/health":
            return send_json(self, 200, {"status": "ok", "database": str(DB_PATH)})

        if path == "/api/categories":
            with connect_db() as db:
                rows = db.execute("SELECT * FROM categories ORDER BY category_name").fetchall()
            return send_json(self, 200, {"categories": [row_to_dict(row) for row in rows]})

        if path == "/api/listings":
            clauses = []
            params = []
            keyword = query.get("keyword", [""])[0].strip()
            category_id = query.get("category_id", [""])[0]
            status = query.get("status", [""])[0]
            max_price = query.get("max_price", [""])[0]

            if keyword:
                clauses.append("(LOWER(l.title) LIKE ? OR LOWER(l.description) LIKE ?)")
                params.extend([f"%{keyword.lower()}%", f"%{keyword.lower()}%"])
            if category_id:
                clauses.append("l.category_id = ?")
                params.append(category_id)
            if status:
                clauses.append("l.status = ?")
                params.append(status)
            if max_price:
                clauses.append("l.price <= ?")
                params.append(max_price)

            where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            return send_json(self, 200, {"listings": listing_query(where, params)})

        if path.startswith("/api/listings/"):
            listing_id = path.split("/")[-1]
            rows = listing_query("WHERE l.listing_id = ?", (listing_id,))
            if not rows:
                return send_json(self, 404, {"error": "Listing not found"})
            return send_json(self, 200, {"listing": rows[0]})

        if path == "/api/admin/dashboard":
            with connect_db() as db:
                totals = db.execute(
                    """
                    SELECT
                      (SELECT COUNT(*) FROM users) AS total_users,
                      (SELECT COUNT(*) FROM listings WHERE status != 'Sold' AND status != 'Removed') AS active_listings,
                      (SELECT COUNT(*) FROM listings WHERE status = 'Sold') AS sold_listings,
                      (SELECT COUNT(*) FROM listings WHERE status = 'Pending') AS pending_review
                    """
                ).fetchone()
                categories = db.execute(
                    """
                    SELECT c.category_name AS category, COUNT(l.listing_id) AS listing_count
                    FROM categories c
                    LEFT JOIN listings l ON l.category_id = c.category_id
                    GROUP BY c.category_id
                    ORDER BY c.category_name
                    """
                ).fetchall()
            return send_json(
                self,
                200,
                {
                    "metrics": row_to_dict(totals),
                    "listings_by_category": [row_to_dict(row) for row in categories],
                },
            )

        if path == "/api/admin/users":
            with connect_db() as db:
                rows = db.execute(
                    "SELECT user_id, name, email, role, status, created_at FROM users ORDER BY user_id"
                ).fetchall()
            return send_json(self, 200, {"users": [row_to_dict(row) for row in rows]})

        return send_json(self, 404, {"error": "Endpoint not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            data = read_json(self)
        except json.JSONDecodeError:
            return send_json(self, 400, {"error": "Invalid JSON"})

        if path == "/api/auth/register":
            required = ["name", "email", "password"]
            if any(not data.get(field) for field in required):
                return send_json(self, 400, {"error": "name, email, and password are required"})
            with connect_db() as db:
                try:
                    cursor = db.execute(
                        """
                        INSERT INTO users (name, email, password_hash, role)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            data["name"],
                            data["email"],
                            hash_password(data["password"]),
                            data.get("role", "student"),
                        ),
                    )
                except sqlite3.IntegrityError:
                    return send_json(self, 409, {"error": "Email already exists"})
                user = db.execute(
                    "SELECT user_id, name, email, role, status, created_at FROM users WHERE user_id = ?",
                    (cursor.lastrowid,),
                ).fetchone()
            return send_json(self, 201, {"user": row_to_dict(user)})

        if path == "/api/auth/login":
            with connect_db() as db:
                user = db.execute(
                    """
                    SELECT user_id, name, email, role, status
                    FROM users
                    WHERE email = ? AND password_hash = ?
                    """,
                    (data.get("email"), hash_password(data.get("password", ""))),
                ).fetchone()
            if not user:
                return send_json(self, 401, {"error": "Invalid email or password"})
            return send_json(self, 200, {"user": row_to_dict(user), "token": f"demo-token-{user['user_id']}"})

        if path == "/api/listings":
            required = ["title", "description", "category_id", "price", "condition", "seller_id"]
            if any(data.get(field) in (None, "") for field in required):
                return send_json(self, 400, {"error": "Missing required listing fields"})
            with connect_db() as db:
                cursor = db.execute(
                    """
                    INSERT INTO listings
                      (title, description, category_id, price, condition, status, seller_id, image_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data["title"],
                        data["description"],
                        data["category_id"],
                        data["price"],
                        data["condition"],
                        data.get("status", "Available"),
                        data["seller_id"],
                        data.get("image_url"),
                    ),
                )
            listing = listing_query("WHERE l.listing_id = ?", (cursor.lastrowid,))[0]
            return send_json(self, 201, {"listing": listing})

        if path == "/api/inquiries":
            required = ["listing_id", "buyer_id", "message"]
            if any(data.get(field) in (None, "") for field in required):
                return send_json(self, 400, {"error": "listing_id, buyer_id, and message are required"})
            with connect_db() as db:
                cursor = db.execute(
                    "INSERT INTO inquiries (listing_id, buyer_id, message) VALUES (?, ?, ?)",
                    (data["listing_id"], data["buyer_id"], data["message"]),
                )
                inquiry = db.execute(
                    "SELECT * FROM inquiries WHERE inquiry_id = ?",
                    (cursor.lastrowid,),
                ).fetchone()
            return send_json(self, 201, {"inquiry": row_to_dict(inquiry)})

        return send_json(self, 404, {"error": "Endpoint not found"})

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if not path.startswith("/api/listings/"):
            return send_json(self, 404, {"error": "Endpoint not found"})

        listing_id = path.split("/")[-1]
        data = read_json(self)
        allowed = ["title", "description", "category_id", "price", "condition", "image_url"]
        updates = [(field, data[field]) for field in allowed if field in data]
        if not updates:
            return send_json(self, 400, {"error": "No valid fields to update"})

        set_clause = ", ".join([f"{field} = ?" for field, _ in updates]) + ", updated_at = CURRENT_TIMESTAMP"
        params = [value for _, value in updates] + [listing_id]
        with connect_db() as db:
            db.execute(f"UPDATE listings SET {set_clause} WHERE listing_id = ?", params)
            changed = db.execute("SELECT changes() AS changed").fetchone()["changed"]
        if changed == 0:
            return send_json(self, 404, {"error": "Listing not found"})
        return send_json(self, 200, {"listing": listing_query("WHERE l.listing_id = ?", (listing_id,))[0]})

    def do_PATCH(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if not (path.startswith("/api/listings/") and path.endswith("/status")):
            return send_json(self, 404, {"error": "Endpoint not found"})

        listing_id = path.split("/")[-2]
        data = read_json(self)
        status = data.get("status")
        if status not in STATUSES:
            return send_json(self, 400, {"error": "Invalid status"})

        with connect_db() as db:
            db.execute(
                "UPDATE listings SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE listing_id = ?",
                (status, listing_id),
            )
            changed = db.execute("SELECT changes() AS changed").fetchone()["changed"]
        if changed == 0:
            return send_json(self, 404, {"error": "Listing not found"})
        return send_json(self, 200, {"listing": listing_query("WHERE l.listing_id = ?", (listing_id,))[0]})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if not path.startswith("/api/listings/"):
            return send_json(self, 404, {"error": "Endpoint not found"})

        listing_id = path.split("/")[-1]
        with connect_db() as db:
            db.execute(
                "UPDATE listings SET status = 'Removed', updated_at = CURRENT_TIMESTAMP WHERE listing_id = ?",
                (listing_id,),
            )
            changed = db.execute("SELECT changes() AS changed").fetchone()["changed"]
        if changed == 0:
            return send_json(self, 404, {"error": "Listing not found"})
        return send_json(self, 200, {"message": "Listing removed", "listing_id": int(listing_id)})


def run(host="127.0.0.1", port=5000):
    init_db(seed=True)
    server = ThreadingHTTPServer((host, port), CampusMarketplaceHandler)
    print(f"Campus Marketplace API running at http://{host}:{port}")
    print(f"Database file: {DB_PATH}")
    server.serve_forever()


if __name__ == "__main__":
    run(port=int(os.environ.get("PORT", "5000")))
