# Database Design

The backend uses a relational database design for Campus Marketplace.

## Tables

## users

Stores student and admin accounts.

| Column | Type | Purpose |
|---|---|---|
| user_id | integer primary key | Unique user id |
| name | text | User full name |
| email | text unique | Login email |
| password_hash | text | Hashed password |
| role | text | student or admin |
| status | text | active or disabled |
| created_at | timestamp | Account creation time |

## categories

Stores listing categories.

| Column | Type | Purpose |
|---|---|---|
| category_id | integer primary key | Unique category id |
| category_name | text unique | Category display name |

## listings

Stores marketplace items.

| Column | Type | Purpose |
|---|---|---|
| listing_id | integer primary key | Unique listing id |
| title | text | Item title |
| description | text | Item details |
| category_id | integer foreign key | Links to categories |
| price | decimal | Item price |
| condition | text | Like New, Good, or Fair |
| status | text | Available, Pending, Sold, or Removed |
| seller_id | integer foreign key | Links to users |
| image_url | text | Optional listing image |
| created_at | timestamp | Creation time |
| updated_at | timestamp | Last update time |

## inquiries

Stores buyer messages.

| Column | Type | Purpose |
|---|---|---|
| inquiry_id | integer primary key | Unique inquiry id |
| listing_id | integer foreign key | Listing being requested |
| buyer_id | integer foreign key | Buyer user id |
| message | text | Buyer message |
| created_at | timestamp | Inquiry time |

## admin_actions

Stores admin moderation history.

| Column | Type | Purpose |
|---|---|---|
| action_id | integer primary key | Unique admin action id |
| admin_id | integer foreign key | Admin user id |
| action_type | text | remove, approve, disable_user, etc. |
| target_type | text | listing or user |
| target_id | integer | Target record id |
| notes | text | Optional notes |
| created_at | timestamp | Action time |

## Relationships

- One user can create many listings.
- One category can contain many listings.
- One listing can receive many inquiries.
- One user can create many inquiries as a buyer.
- One admin user can create many admin action records.

## PostgreSQL Notes

For PostgreSQL, change `INTEGER PRIMARY KEY AUTOINCREMENT` to `SERIAL PRIMARY KEY`, use `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`, and use `NUMERIC(10,2)` for price.
