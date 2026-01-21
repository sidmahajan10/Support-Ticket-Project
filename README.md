# Support Ticket Management System

A modern support ticket management system built with Django REST Framework backend and React frontend.

## Features

- **User Authentication**: Secure login and registration system
- **Ticket Management**: Create, view, and manage support tickets
- **Status Filtering**: Filter tickets by status (Open, In Progress, Closed)
- **Status Updates**: Update ticket status with a single click
- **Modern UI**: Beautiful, responsive React frontend with gradient design
- **RESTful API**: Clean Django REST Framework API backend

## Project Structure

```
Support Ticket Project/
├── frontend/              # React frontend application
├── ticket/                # Django ticket app
├── user/                  # Django user app
├── supportticket/         # Django project settings
└── templates/             # Legacy HTML templates (kept for compatibility)
```

## Setup Instructions

### Backend Setup (Django)

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run migrations:**
```bash
python manage.py migrate
```

3. **Create a superuser (optional):**
```bash
python manage.py createsuperuser
```

4. **Start the Django development server:**
```bash
python manage.py runserver
```

The backend API will be available at `http://localhost:8000`

### Frontend Setup (React)

1. **Navigate to the frontend directory:**
```bash
cd frontend
```

2. **Install Node.js dependencies:**
```bash
npm install
```

3. **Start the React development server:**
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register a new user
- `POST /api/auth/login/` - Login user
- `POST /api/auth/logout/` - Logout user
- `GET /api/auth/user/` - Get current authenticated user

### Tickets
- `GET /api/tickets/` - List all tickets for authenticated user
- `GET /api/tickets/?status=open` - Filter tickets by status
- `POST /api/tickets/` - Create a new ticket
- `GET /api/tickets/{id}/` - Get ticket details
- `PATCH /api/tickets/{id}/update_status/` - Update ticket status

## Usage

1. Start both the Django backend and React frontend servers
2. Navigate to `http://localhost:3000` in your browser
3. Register a new account or login with existing credentials
4. Create tickets and manage them from the dashboard
5. Use the status filter to view tickets by status

## Technologies Used

### Backend
- Django 5.1.4
- Django REST Framework
- Django CORS Headers
- SQLite (default database)

### Frontend
- React 18.2.0
- React Router DOM
- Axios
- CSS3 (Modern styling with gradients and animations)

## Improvements Made

1. **Separated Frontend**: Created a separate React frontend repository
2. **RESTful API**: Converted Django views to REST API endpoints
3. **Status Filtering**: Added filtering capability by ticket status
4. **Modern UI**: Implemented a beautiful, responsive design with:
   - Gradient backgrounds
   - Card-based layouts
   - Smooth animations
   - Status badges with color coding
   - Mobile-responsive design
5. **Better Code Quality**:
   - Proper error handling
   - Loading states
   - Form validation
   - Context API for authentication state management
   - Private routes for protected pages

## Development Notes

- The frontend uses a proxy configuration to communicate with the Django backend
- CORS is configured to allow requests from `localhost:3000`
- Session authentication is used for API authentication
- The legacy HTML templates are kept for backward compatibility but are not used by the React frontend
