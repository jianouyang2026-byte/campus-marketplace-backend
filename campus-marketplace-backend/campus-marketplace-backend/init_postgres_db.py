import os
from pathlib import Path

import psycopg2

from app_postgres import hash_password


BASE_DIR = Path(__file__).resolve().parent


def connect(database=None):
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "7313")),
        dbname=database or os.environ.get("DB_NAME", "campus_marketplace"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", ""),
    )


def ensure_database():
    db_name = os.environ.get("DB_NAME", "campus_marketplace")
    try:
        with connect(db_name):
            return
    except psycopg2.OperationalError:
        pass

    with connect("postgres") as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if cur.fetchone() is None:
                cur.execute(f'CREATE DATABASE "{db_name}"')


def initialize_schema_and_seed_data():
    ensure_database()
    schema = (BASE_DIR / "schema_postgresql.sql").read_text(encoding="utf-8")
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(schema)
            for category in ["Textbooks", "Furniture", "Electronics", "Kitchen", "Transportation"]:
                cur.execute(
                    "INSERT INTO categories (category_name) VALUES (%s) ON CONFLICT (category_name) DO NOTHING",
                    (category,),
                )

            users = [
                ("Jian Ouyang", "jian@example.edu", "student"),
                ("Maya Chen", "maya@example.edu", "student"),
                ("Campus Admin", "admin@example.edu", "admin"),
            ]
            for name, email, role in users:
                cur.execute(
                    """
                    INSERT INTO users (name, email, password_hash, role)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (email) DO NOTHING
                    """,
                    (name, email, hash_password("Password123"), role),
                )

            cur.execute("SELECT COUNT(*) FROM listings")
            if cur.fetchone()[0] == 0:
                cur.execute(
                    """
                    INSERT INTO listings
                      (title, description, category_id, price, condition, status, seller_id, image_url)
                    VALUES
                      ('Calculus Textbook, 9th Edition', 'Used for one semester with notes.', 1, 38, 'Good', 'Available', 1, NULL),
                      ('Compact Study Desk', 'Small desk that fits well in a dorm room.', 2, 55, 'Good', 'Available', 2, NULL),
                      ('Noise-Canceling Headphones', 'Great for studying in the library.', 3, 95, 'Like New', 'Pending', 2, NULL),
                      ('Dorm Kitchen Starter Set', 'Includes pan, pot, cutting board, and utensils.', 4, 26, 'Good', 'Sold', 1, NULL)
                    """
                )


if __name__ == "__main__":
    initialize_schema_and_seed_data()
    print("PostgreSQL database initialized successfully.")
