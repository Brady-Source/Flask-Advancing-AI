# Advancing-AI
Flask forum app

# Flask Advancing AI

A full-stack web application built with Flask, with role-based access control, Google OAuth authentication, secure password hashing+salt, and a RESTful API. Developed as part of a B.S. in Artificial Intelligence curriculum to demonstrate web application programming learning and practical application.

***

## Features

- **Google OAuth 2.0 Authentication** — Users sign in via Google; no password required for OAuth users
- **Role-Based Access Control** — Five roles: `User`, `Editor`, `Moderator`, `Admin`, and `Applicant User`, each with granular permissions (`FOLLOW`, `COMMENT`, `WRITE`, `MODERATE`, `ADMIN`)
- **Custom Password Hashing** — Manual salt generation and SHA-256 hashing via `Werkzeug` and `hashlib`
- **Token-Based Email Flows** — Signed, expiring tokens for account confirmation, password reset, and email change using `itsdangerous`
- **Follow System** — Users can follow/unfollow each other; followed posts surface in a personalized feed
- **Rich Post Editor** — Posts support plain text, HTML, and Markdown formats with `bleach` sanitization
- **Paginated REST API** — JSON endpoints for users, posts, and comments with `Flask-HTTPAuth` token authentication
- **HTTPS Enforcement** — `Flask-Talisman` enforces HTTPS and sets security headers in production
- **Gravatar Avatars** — Auto-generated from the user's email hash
- **Slow Query Detection** — SQLAlchemy query logging with configurable slow-query threshold

***

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Flask |
| Database ORM | Flask-SQLAlchemy, Flask-Migrate |
| Authentication | Flask-Login, Authlib, Google OAuth 2.0 |
| Forms | Flask-WTF |
| Frontend | Bootstrap-Flask, Flask-PageDown, Flask-Moment |
| Email | Flask-Mail (Gmail Service Account via OAuth) |
| Security | Flask-Talisman, Werkzeug, `hashlib` SHA-256 |
| API Auth | Flask-HTTPAuth |
| Server (Prod) | Waitress / Gunicorn |
| Testing | Python `unittest`, Faker |

***

## Project Structure

```
Flask-Advancing-AI/
├── app/
│   ├── __init__.py         # App factory, extension initialization
│   ├── models.py           # SQLAlchemy models: User, Role, Post, Comment, Follow
│   ├── auth/               # Authentication blueprint (Google OAuth, login/logout)
│   ├── main/               # Main blueprint (index, user profiles, posts)
│   ├── api/                # REST API blueprint
│   └── templates/          # Jinja2 HTML templates
├── tests/
│   └── tests.py            # Unit tests: token expiration, password hashing, user roles
├── config.py               # Development, Production, and Testing configurations
├── flasky.py               # App entry point and CLI commands
├── requirements.txt        # Python dependencies
└── Dockerfile              # Container definition
```

***

## Getting Started

### Prerequisites

- Python 3.10+
- pip
- A Google Cloud project with OAuth 2.0 credentials configured ((Optional) For email verification, and Google API login)
    - Clone and create your own db then add yourself manually as a user, making sure your user column "confirmed" = 1

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Brady-Source/Flask-Advancing-AI.git
   cd Flask-Advancing-AI
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate        # Linux/macOS
   venv\Scripts\activate           # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root:

   ```env
   FLASK_SECRET_KEY=your-secret-key
   FLASK_GOOGLE_CLIENT_ID=your-google-client-id
   FLASK_GOOGLE_CLIENT_SECRET=your-google-client-secret
   FLASK_OAUTH_REDIRECT_URI=http://localhost:5000/auth/callback
   GMAIL_SERVICE_ACCOUNT_EMAIL=your-service-account@example.iam.gserviceaccount.com
   GMAIL_PRIVATE_KEY=your-private-key
   GMAIL_SENDER_EMAIL=no-reply@yourdomain.com
   DEV_DATABASE_URL=sqlite:///data.sqlite
   ```

5. **Initialize the database**

   ```bash
   flask db upgrade
   flask shell
   >>> Role.insert_roles()
   >>> db.session.commit()
   ```

6. **Run the development server**

   ```bash
   flask run
   ```

***

## Running Tests

```bash
python -m pytest tests/ -v
```

The test suite covers three areas:

| Test Class | Tests | What It Validates |
|---|---|---|
| `TokenExpirationTestCase` | 6 | Signed token generation and expiration for confirm, reset, email change, and auth flows |
| `PasswordHashingTestCase` | 2 | Salt generation, SHA-256 hashing, and `verify_password` correctness |
| `ApplicantUserTestCase` | 5 | Role assignment, permission checks, and user initialization logic |

***

## Configuration

Three environments are available, selected via the `FLASK_ENV` variable or `config` mapping in `config.py`:

| Environment | Database | Debug | Notes |
|---|---|---|---|
| `development` | `data-dev.sqlite` | On | Default for local development |
| `production` | `$DATABASE_URL` | Off | Uses Waitress or Gunicorn |
| `testing` | In-memory SQLite | Off | CSRF disabled, isolated per test |

***

## Docker

A `Dockerfile` is included for containerized deployment.

```bash
docker build -t flask-advancing-ai .
docker run -p 5000:5000 --env-file .env flask-advancing-ai
```

***

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.