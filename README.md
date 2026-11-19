# DigiNote REST API — Django Backend

A modular, production-ready REST API for **DigiNote** built with **Django REST Framework (DRF)**, **SimpleJWT**, and **MongoDB (PyMongo)**, designed to connect directly to the same MongoDB Atlas database as the Express backend.

---

## 🏗️ Architecture & Features

- **Framework**: Django 4.2+ & Django REST Framework (DRF)
- **Database**: MongoDB Atlas via `pymongo` (Full interoperability with Express backend)
- **Authentication**: JWT-based authentication compatible with SimpleJWT and Express tokens
- **Role-Based Access Control (RBAC)**:
  - `User`: Manage own notes (create, read, update, delete, paginated list)
  - `Admin`: Full user management + view all users' notes
- **Aggregation Pipelines (MongoDB Native)**:
  - Scenario 1: Group users by interests (`$match`, `$unwind`, `$group`, `$sort`)
  - Scenario 2: Retrieve user posts with `$lookup`
- **Modular Settings Pattern**:
  - `config/settings/base.py`: Shared base configurations
  - `config/settings/development.py`: Development specific settings (`DEBUG=True`)
  - `config/settings/production.py`: Hardened security settings for production
- **Clean App Separation (`apps/` folder)**:
  - `apps/authentication`: User registration, login, profile, admin user management
  - `apps/notes`: User notes CRUD & Admin global notes inspector
  - `apps/posts`: Public posts feed & creation
  - `apps/aggregations`: MongoDB aggregation tasks
- **Docker Ready**: `Dockerfile`, `docker-compose.yml`, and `docker-compose.prod.yml` included.

---

## 🚀 Running with Docker (Recommended)

1. Ensure `.env` is configured (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

2. Start development container with hot-reloading:
   ```bash
   docker compose up --build
   # API runs on http://localhost:8000/api
   ```

3. To run in production mode with Gunicorn:
   ```bash
   docker compose -f docker-compose.prod.yml up --build -d
   ```

---

## 🐍 Running Locally with Python

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run development server:
   ```bash
   python manage.py runserver 8000
   ```

---

## 📑 API Endpoints Reference

All endpoints mirror the Express backend API specification:

### Authentication & Users (`/api/`)
- `POST /api/auth/register/` - Register user (bcrypt hashed password)
- `POST /api/auth/login/` - Login and get JWT token
- `GET /api/auth/me/` - Authenticated user profile
- `GET /api/users/` - Admin list users with pagination
- `POST /api/users/` - Admin create user
- `GET, PUT, DELETE /api/users/<id>/` - User detail / management

### Notes (`/api/`)
- `GET /api/notes/` - User's own notes (paginated)
- `POST /api/notes/` - Create a note
- `GET /api/notes/all/` - Admin view all notes (paginated)
- `GET, PUT, DELETE /api/notes/<id>/` - Single note detail (owner or admin)

### Public Posts (`/api/`)
- `GET /api/posts/` - Public post feed with pagination
- `POST /api/posts/` - Create public post

### MongoDB Aggregation Tasks (`/api/`)
- `GET /api/aggregations/users-by-interest/` - Scenario 1 aggregation
- `GET /api/aggregations/user-posts/<userId>/` - Scenario 2 aggregation with `$lookup`
