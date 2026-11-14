# ReMan - Real Estate Manager Backend

Django-based web application and backend management system for real estate operations, inventory management, deal tracking, and financial analytics.

## Features
- **Project & Site Inventory Management**: Track layouts, site booking status, unearned revenue ledgers, and inventory allocation.
- **Financial Analytics & Accounting**: Cash-flow tracking, categorized expense monitoring, partner investment tracking, and automated profit-sharing calculations.
- **CRM & Deal Tracking**: Lead and contact management, landowner deals, follow-up scheduling, and document vault.
- **Audit Trails**: Activity logging and transaction records.

## Tech Stack
- **Framework**: Django 4.2+ / Python 3.10+
- **Frontend**: Bootstrap 5, Bootstrap Icons, Chart.js
- **Database**: SQLite (default / dev) / PostgreSQL / MySQL (production compatible)

## Production Cloud Deployment (Render / Railway / Heroku)

- **Build Command**: `pip install -r requirements.txt && python manage.py migrate`
- **Start Command**: `python manage.py migrate && gunicorn config.wsgi:application`

## Setup & Running Locally

1. **Clone the repository:**
   ```bash
   git clone https://github.com/letsbdift/ReMan-Backend.git
   cd ReMan-Backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply database migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser:**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the development server:**
   ```bash
   python manage.py runserver
   ```
   Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.
