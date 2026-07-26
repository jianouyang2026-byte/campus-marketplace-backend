# API Documentation

Base URL:

```text
http://127.0.0.1:5000
```

## GET /api/health

Checks that the backend and database are available.

Sample output:

```json
{
  "status": "ok",
  "database": "campus_marketplace.db"
}
```

## POST /api/auth/register

Creates a new user.

Sample input:

```json
{
  "name": "Test Student",
  "email": "test.student@example.edu",
  "password": "Password123",
  "role": "student"
}
```

Sample output:

```json
{
  "user": {
    "user_id": 4,
    "name": "Test Student",
    "email": "test.student@example.edu",
    "role": "student",
    "status": "active",
    "created_at": "2026-07-20 10:00:00"
  }
}
```

## POST /api/auth/login

Validates a user login.

Sample input:

```json
{
  "email": "jian@example.edu",
  "password": "Password123"
}
```

Sample output:

```json
{
  "user": {
    "user_id": 1,
    "name": "Jian Ouyang",
    "email": "jian@example.edu",
    "role": "student",
    "status": "active"
  },
  "token": "demo-token-1"
}
```

## GET /api/categories

Returns listing categories.

Sample output:

```json
{
  "categories": [
    {
      "category_id": 3,
      "category_name": "Electronics"
    }
  ]
}
```

## GET /api/listings

Searches listings. Optional query parameters: `keyword`, `category_id`, `status`, and `max_price`.

Example:

```text
GET /api/listings?keyword=desk&max_price=100
```

Sample output:

```json
{
  "listings": [
    {
      "listing_id": 2,
      "title": "Compact Study Desk",
      "description": "Small desk that fits well in a dorm room.",
      "category_id": 2,
      "category": "Furniture",
      "price": 55,
      "condition": "Good",
      "status": "Available",
      "seller_id": 2,
      "seller_name": "Maya Chen"
    }
  ]
}
```

## GET /api/listings/{listing_id}

Returns one listing by id.

Sample output:

```json
{
  "listing": {
    "listing_id": 1,
    "title": "Calculus Textbook, 9th Edition",
    "category": "Textbooks",
    "price": 38,
    "status": "Available"
  }
}
```

## POST /api/listings

Creates a listing.

Sample input:

```json
{
  "title": "Used Monitor",
  "description": "Good monitor for dorm study desk.",
  "category_id": 3,
  "price": 60,
  "condition": "Good",
  "seller_id": 1,
  "image_url": null
}
```

Sample output:

```json
{
  "listing": {
    "listing_id": 5,
    "title": "Used Monitor",
    "category": "Electronics",
    "price": 60,
    "condition": "Good",
    "status": "Available",
    "seller_id": 1,
    "seller_name": "Jian Ouyang"
  }
}
```

## PUT /api/listings/{listing_id}

Updates listing details.

Sample input:

```json
{
  "price": 50,
  "description": "Updated price. Good monitor for dorm study desk."
}
```

Sample output:

```json
{
  "listing": {
    "listing_id": 5,
    "title": "Used Monitor",
    "price": 50,
    "description": "Updated price. Good monitor for dorm study desk."
  }
}
```

## PATCH /api/listings/{listing_id}/status

Updates listing status.

Sample input:

```json
{
  "status": "Pending"
}
```

Sample output:

```json
{
  "listing": {
    "listing_id": 5,
    "title": "Used Monitor",
    "status": "Pending"
  }
}
```

## DELETE /api/listings/{listing_id}

Marks a listing as removed.

Sample output:

```json
{
  "message": "Listing removed",
  "listing_id": 5
}
```

## POST /api/inquiries

Creates a buyer inquiry.

Sample input:

```json
{
  "listing_id": 5,
  "buyer_id": 2,
  "message": "Is this still available?"
}
```

Sample output:

```json
{
  "inquiry": {
    "inquiry_id": 1,
    "listing_id": 5,
    "buyer_id": 2,
    "message": "Is this still available?"
  }
}
```

## GET /api/admin/dashboard

Returns admin metrics.

Sample output:

```json
{
  "metrics": {
    "total_users": 4,
    "active_listings": 4,
    "sold_listings": 1,
    "pending_review": 1
  },
  "listings_by_category": [
    {
      "category": "Electronics",
      "listing_count": 2
    }
  ]
}
```

## GET /api/admin/users

Returns users for admin review.

Sample output:

```json
{
  "users": [
    {
      "user_id": 1,
      "name": "Jian Ouyang",
      "email": "jian@example.edu",
      "role": "student",
      "status": "active"
    }
  ]
}
```
