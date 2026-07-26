import hashlib
import os
from decimal import Decimal

import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request
from flask_cors import CORS

from config import load_env_file


STATUSES = {"Available", "Pending", "Sold", "Removed"}
load_env_file()


def create_app():
    app = Flask(__name__)
    CORS(app)

    @app.get("/api/health")
    def health():
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT CURRENT_DATABASE() AS database_name")
                row = cur.fetchone()
        return jsonify({"status": "ok", "database": row["database_name"], "engine": "PostgreSQL"})

    @app.post("/api/auth/register")
    def register():
        data = request.get_json(force=True)
        required = ["name", "email", "password"]
        if any(not data.get(field) for field in required):
            return jsonify({"error": "name, email, and password are required"}), 400

        with get_db() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        """
                        INSERT INTO users (name, email, password_hash, role)
                        VALUES (%s, %s, %s, %s)
                        RETURNING user_id, name, email, role, status, created_at
                        """,
                        (
                            data["name"],
                            data["email"],
                            hash_password(data["password"]),
                            data.get("role", "student"),
                        ),
                    )
                    user = cur.fetchone()
                except psycopg2.errors.UniqueViolation:
                    conn.rollback()
                    return jsonify({"error": "Email already exists"}), 409
        return jsonify({"user": clean_row(user)}), 201

    @app.post("/api/auth/login")
    def login():
        data = request.get_json(force=True)
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT user_id, name, email, role, status
                    FROM users
                    WHERE email = %s AND password_hash = %s
                    """,
                    (data.get("email"), hash_password(data.get("password", ""))),
                )
                user = cur.fetchone()
        if not user:
            return jsonify({"error": "Invalid email or password"}), 401
        return jsonify({"user": clean_row(user), "token": f"demo-token-{user['user_id']}"})

    @app.get("/api/categories")
    def categories():
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT category_id, category_name FROM categories ORDER BY category_name")
                rows = cur.fetchall()
        return jsonify({"categories": clean_rows(rows)})

    @app.get("/api/listings")
    def listings():
        clauses = []
        params = []
        keyword = request.args.get("keyword", "").strip().lower()
        category_id = request.args.get("category_id")
        status = request.args.get("status")
        max_price = request.args.get("max_price")

        if keyword:
            clauses.append("(LOWER(l.title) LIKE %s OR LOWER(l.description) LIKE %s)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if category_id:
            clauses.append("l.category_id = %s")
            params.append(category_id)
        if status:
            clauses.append("l.status = %s")
            params.append(status)
        if max_price:
            clauses.append("l.price <= %s")
            params.append(max_price)

        where_clause = "WHERE " + " AND ".join(clauses) if clauses else ""
        return jsonify({"listings": get_listings(where_clause, params)})

    @app.get("/api/listings/<int:listing_id>")
    def get_listing(listing_id):
        rows = get_listings("WHERE l.listing_id = %s", [listing_id])
        if not rows:
            return jsonify({"error": "Listing not found"}), 404
        return jsonify({"listing": rows[0]})

    @app.post("/api/listings")
    def create_listing():
        data = request.get_json(force=True)
        required = ["title", "description", "category_id", "price", "condition", "seller_id"]
        if any(data.get(field) in (None, "") for field in required):
            return jsonify({"error": "Missing required listing fields"}), 400

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO listings
                      (title, description, category_id, price, condition, status, seller_id, image_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING listing_id
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
                listing_id = cur.fetchone()["listing_id"]
        return jsonify({"listing": get_listings("WHERE l.listing_id = %s", [listing_id])[0]}), 201

    @app.put("/api/listings/<int:listing_id>")
    def update_listing(listing_id):
        data = request.get_json(force=True)
        allowed = ["title", "description", "category_id", "price", "condition", "image_url"]
        updates = [(field, data[field]) for field in allowed if field in data]
        if not updates:
            return jsonify({"error": "No valid fields to update"}), 400

        set_clause = ", ".join([f"{field} = %s" for field, _ in updates])
        params = [value for _, value in updates] + [listing_id]
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE listings SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE listing_id = %s",
                    params,
                )
                if cur.rowcount == 0:
                    return jsonify({"error": "Listing not found"}), 404
        return jsonify({"listing": get_listings("WHERE l.listing_id = %s", [listing_id])[0]})

    @app.patch("/api/listings/<int:listing_id>/status")
    def update_status(listing_id):
        data = request.get_json(force=True)
        status = data.get("status")
        if status not in STATUSES:
            return jsonify({"error": "Invalid status"}), 400

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE listings SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE listing_id = %s",
                    (status, listing_id),
                )
                if cur.rowcount == 0:
                    return jsonify({"error": "Listing not found"}), 404
        return jsonify({"listing": get_listings("WHERE l.listing_id = %s", [listing_id])[0]})

    @app.delete("/api/listings/<int:listing_id>")
    def remove_listing(listing_id):
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE listings SET status = 'Removed', updated_at = CURRENT_TIMESTAMP WHERE listing_id = %s",
                    (listing_id,),
                )
                if cur.rowcount == 0:
                    return jsonify({"error": "Listing not found"}), 404
        return jsonify({"message": "Listing removed", "listing_id": listing_id})

    @app.post("/api/inquiries")
    def create_inquiry():
        data = request.get_json(force=True)
        required = ["listing_id", "buyer_id", "message"]
        if any(data.get(field) in (None, "") for field in required):
            return jsonify({"error": "listing_id, buyer_id, and message are required"}), 400
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO inquiries (listing_id, buyer_id, message)
                    VALUES (%s, %s, %s)
                    RETURNING inquiry_id, listing_id, buyer_id, message, created_at
                    """,
                    (data["listing_id"], data["buyer_id"], data["message"]),
                )
                inquiry = cur.fetchone()
        return jsonify({"inquiry": clean_row(inquiry)}), 201

    @app.get("/api/admin/dashboard")
    def admin_dashboard():
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                      (SELECT COUNT(*) FROM users) AS total_users,
                      (SELECT COUNT(*) FROM listings WHERE status NOT IN ('Sold', 'Removed')) AS active_listings,
                      (SELECT COUNT(*) FROM listings WHERE status = 'Sold') AS sold_listings,
                      (SELECT COUNT(*) FROM listings WHERE status = 'Pending') AS pending_review
                    """
                )
                metrics = cur.fetchone()
                cur.execute(
                    """
                    SELECT c.category_name AS category, COUNT(l.listing_id) AS listing_count
                    FROM categories c
                    LEFT JOIN listings l ON l.category_id = c.category_id
                    GROUP BY c.category_id, c.category_name
                    ORDER BY c.category_name
                    """
                )
                category_rows = cur.fetchall()
        return jsonify({"metrics": clean_row(metrics), "listings_by_category": clean_rows(category_rows)})

    @app.get("/api/admin/users")
    def admin_users():
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT user_id, name, email, role, status, created_at FROM users ORDER BY user_id")
                rows = cur.fetchall()
        return jsonify({"users": clean_rows(rows)})

    return app


def get_db():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "7313")),
        dbname=os.environ.get("DB_NAME", "campus_marketplace"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", ""),
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def clean_value(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def clean_row(row):
    return {key: clean_value(value) for key, value in dict(row).items()}


def clean_rows(rows):
    return [clean_row(row) for row in rows]


def get_listings(where_clause="", params=None):
    params = params or []
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
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return clean_rows(cur.fetchall())


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)
