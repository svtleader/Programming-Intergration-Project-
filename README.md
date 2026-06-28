# Bookstore Management System

A full-stack web application for managing a bookstore's customer orders — built with data engineering principles in mind, focusing on optimized search, filtering, and pagination over large datasets through database indexing.

> Course project for **CO3127 — Programming Integration Project: Data Engineering**, Faculty of Computer Science and Engineering, Ho Chi Minh City University of Technology (HCMUT).

## Overview

The system provides a centralized platform for bookstore staff and admins to manage customer orders — covering book/author/edition storage, order tracking, and role-based access control, with an emphasis on fast, indexed search across large order datasets.

### User Roles

- **Admin** — full system access; search/view orders; modify order details (update quantities, remove items)
- **Staff** — search and view orders (read-only)

### Core Features

- **Authentication** — session-based login/logout with automatic session expiry
- **Order Management** — paginated order list, detailed order view, and order modification (admin only)
- **Search & Filtering** — search orders by Order ID, Book title, or Author name; filter by single date or date range
- **Optimized Querying** — server-side filtering, searching, and pagination backed by database indexes for fast response times on large datasets

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python (Flask), SQLAlchemy |
| Frontend | React, Axios, Tailwind CSS |
| Database | MySQL |
| Auth | JWT (jsonwebtoken), bcrypt |

## Database Design

The schema is built around five core entities: **Account** (Admin/Staff), **Order**, **Order Detail**, **Book**, **Edition**, and **Author** — connected through relationships such as an order containing multiple book editions, and a book being written by one or more authors.

### Indexing Strategy

To keep search and filtering fast at scale, the database uses targeted indexes:

- **Full-text index** on `OrderID` for efficient text-based order search
- **Date indexes** — single-column on `SaleDate`, plus a composite `(SaleDate, OrderID)` index for combined date + ordering queries
- **Case-insensitive indexes** on `Book.Title` and `Author.LastName` for title/author search regardless of capitalization
- **Foreign key indexes** on `OrderDetails(OrderID, ISBN)` for fast joins between orders and book editions

All filtering, searching, and pagination are handled server-side — only the requested page of data is transferred to the client, and queries are ordered using the composite index before pagination is applied, keeping memory usage and response times consistent regardless of dataset size.

## Getting Started

### Prerequisites

- Node.js and npm
- Python 3.x
- MySQL Server

### Backend Setup

```bash
cd "Programming Intergration Project/bookstore-api"

# Install Node dependencies (used for initial project tooling)
npm install express dotenv jsonwebtoken bcryptjs mysql2 sequelize

# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
# Create a .env file with your MySQL connection settings

# Initialize the database
python init_db.py
python import_data.py
python seed_users.py

# Start the backend server
python app.py
```

### Frontend Setup

```bash
cd "Programming Intergration Project/bookstore-frontend"

# Install dependencies
npm install axios react-router-dom tailwindcss

# Start the development server
npm start
```

## Project Structure

```
Programming Intergration Project/
├── bookstore-api/
│   ├── models/
│   ├── routes/
│   ├── utils/
│   ├── app.py              ← Flask application entry point
│   ├── config.py           ← Database configuration
│   ├── init_db.py          ← Database/schema initialization
│   ├── import_data.py      ← Imports book/order data from Excel
│   ├── seed_users.py       ← Generates login credentials
│   ├── Mysql_Database.sql
│   └── requirements.txt
└── bookstore-frontend/
    └── (React application)
```

## System Evaluation

**Pros**
- Role-based access for multiple user types
- Encrypted passwords for security
- Indexed search and pagination for fast response times on large datasets
- Graceful error handling for invalid inputs and failed requests
- Persistent login sessions

**Cons**
- Basic, minimally-styled UI

## Author

**Lê Dũng** — 2252131
Instructor: Dr. Lê Thị Bảo Thu

## References

- [ReactJS Tutorial](https://www.tutorialspoint.com/reactjs/index.htm)
- [React Context for Beginners](https://www.freecodecamp.org/news/react-context-for-beginners/)
- [Getting Started with npm Workspaces](https://www.geeksforgeeks.org/getting-started-with-npm-workspaces/)
- [JSON Web Tokens](https://jwt.io/)
- [MySQL CREATE INDEX Statement](https://dev.mysql.com/doc/refman/8.4/en/create-index.html)
