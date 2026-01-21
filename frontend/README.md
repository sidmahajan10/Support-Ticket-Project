# Support Ticket Frontend

React frontend for the Support Ticket Management System.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

The app will run on http://localhost:3000

## Features

- User authentication (Login/Register)
- Create and manage support tickets
- Filter tickets by status (Open, In Progress, Closed)
- Update ticket status
- Modern, responsive UI

## API Configuration

The frontend is configured to proxy API requests to the Django backend running on http://localhost:8000. Make sure the Django backend is running before starting the frontend.
