# PeerDrive – Peer-to-Peer Carpooling Platform

A full-stack Django web application that connects drivers and passengers for shared rides. Users can post rides, search for available cars by location using geolocation matching, and make bookings.

## Features

- User registration, login, and profile management
- Post a ride — add car details, route, dates, and seat count
- Search rides by location using geolocation (within 10 km radius matching)
- Route distance and estimated duration via OpenRouteService API
- Booking system with overlap detection
- Driver earnings dashboard
- Feedback and rating system
- Ride reports with date filtering
- Admin panel with full CRUD for all models

## Tech Stack

- **Backend:** Python, Django 4.1
- **Database:** MySQL (via PyMySQL)
- **Geolocation:** Geopy (Nominatim), OpenRouteService API
- **Frontend:** HTML, CSS, JavaScript (Django templates)

## Project Structure

```
peerdrive/
├── carpool/               # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── website/               # Main app
│   ├── models.py          # Customer, Mycar, Booking, Feedback, ContactUs
│   ├── views.py           # All view functions
│   ├── urls.py            # URL routing
│   ├── admin.py           # Admin configuration
│   └── migrations/
├── templates/             # HTML templates
├── static/                # CSS, JS, images
└── manage.py
```

## Setup

**Prerequisites:** Python 3.8+, MySQL

### 1. Clone the repo

```bash
git clone https://github.com/tomsyfrancis/peerdrive.git
cd peerdrive
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:
```
DJANGO_SECRET_KEY=your-secret-key
DB_NAME=carpooling
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306
ORS_API_KEY=your-openrouteservice-api-key
```

Get a free OpenRouteService API key at [openrouteservice.org](https://openrouteservice.org).

### 5. Create the database

In MySQL:
```sql
CREATE DATABASE carpooling;
```

### 6. Run migrations and start the server

```bash
cd carpool
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

## License

This project is for educational and portfolio purposes.

## Attribution
Built on top of the open-source carpooling project by prachik26
(https://github.com/prachik26/Peer-to-Peer-Carpooling).
Extended with geolocation search, OpenRouteService routing,
driver earnings, feedback system, and ride reports.