# Quick Setup Guide

## Prerequisites

- Python 3.8+ installed
- Node.js 14+ and npm installed
- pip (Python package manager)

## Step-by-Step Setup

### 1. Backend Setup

```bash
# Navigate to project root
cd "/Users/siddhantmahajan/Desktop/Support Ticket Project"

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# (Optional) Create admin user
python manage.py createsuperuser

# Start Django server
python manage.py runserver
```

The backend will run on `http://localhost:8000`

### 2. Frontend Setup

Open a new terminal window:

```bash
# Navigate to frontend directory
cd "/Users/siddhantmahajan/Desktop/Support Ticket Project/frontend"

# Install Node.js dependencies
npm install

# Start React development server
npm start
```

The frontend will run on `http://localhost:3000` and automatically open in your browser.

## Testing the Application

1. Open `http://localhost:3000` in your browser
2. Click "Sign up" to create a new account
3. Fill in the registration form and submit
4. You'll be automatically logged in and redirected to the dashboard
5. Click "+ Create New Ticket" to create your first ticket
6. Use the status filter dropdown to filter tickets by status
7. Click status action buttons to update ticket status

## Troubleshooting

### Backend Issues

- **Port 8000 already in use**: Change the port with `python manage.py runserver 8001`
- **Migration errors**: Run `python manage.py makemigrations` then `python manage.py migrate`
- **Module not found**: Ensure you've installed all requirements with `pip install -r requirements.txt`

### Frontend Issues

- **Port 3000 already in use**: React will prompt you to use a different port
- **npm install fails**: Try deleting `node_modules` and `package-lock.json`, then run `npm install` again
- **API connection errors**: Ensure the Django backend is running on port 8000

### CORS Issues

If you see CORS errors in the browser console, ensure:
1. Django CORS headers is installed (`pip install django-cors-headers`)
2. CORS middleware is added in `settings.py` (already configured)
3. `CORS_ALLOWED_ORIGINS` includes `http://localhost:3000` (already configured)

## API Testing

You can test the API endpoints directly using curl or Postman:

```bash
# Register a user
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","name":"Test User","password":"testpass123","password2":"testpass123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"username":"testuser","password":"testpass123"}'

# Get tickets (requires authentication)
curl -X GET http://localhost:8000/api/tickets/ \
  -H "Content-Type: application/json" \
  -b cookies.txt
```
