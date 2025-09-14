# PetCare Project - Frontend Setup Guide

This project uses Django as the backend API and Svelte as the frontend framework.

## Project Structure
```
PetCareThong_InuThai/
├── petcare/           # Django backend
├── frontend/          # Svelte frontend
├── myvenv/           # Python virtual environment
└── setup.bat         # Backend setup script
```

## Prerequisites
- Python 3.13+ installed
- Node.js 22.14+ installed
- npm or pnpm package manager

## Backend Setup (Django)
1. Run the setup script to create virtual environment and install dependencies:
   ```bash
   setup.bat
   ```

2. Navigate to the Django project:
   ```bash
   cd petcare
   ```

3. Activate virtual environment (if not already active):
   ```bash
   ..\myvenv\Scripts\activate.bat
   ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Start the Django development server:
   ```bash
   python manage.py runserver
   ```
   Django will run on: http://127.0.0.1:8000/

## Frontend Setup (Svelte)
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies (if not already installed):
   ```bash
   pnpm install
   ```
   Or if using npm:
   ```bash
   npm install
   ```

3. Start the Svelte development server:
   ```bash
   pnpm run dev
   ```
   Or if using npm:
   ```bash
   npm run dev
   ```
   Svelte will run on: http://localhost:5173/

## Development Workflow

### Running Both Servers
You'll need two terminal windows:

**Terminal 1 - Django Backend:**
```bash
cd petcare
..\myvenv\Scripts\activate.bat
python manage.py runserver
```

**Terminal 2 - Svelte Frontend:**
```bash
cd frontend
pnpm run dev
```

### API Communication
- Django backend: http://127.0.0.1:8000/
- Svelte frontend: http://localhost:5173/
- CORS is configured to allow requests from the Svelte dev server

### Making API Calls from Svelte
In your Svelte components, you can make API calls to Django:

```javascript
// Example API call
const response = await fetch('http://127.0.0.1:8000/api/endpoint/', {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include', // For session-based auth
});
const data = await response.json();
```

## Next Steps
1. Create Django API endpoints in your backend
2. Build Svelte components that consume these APIs
3. Set up authentication between frontend and backend
4. Configure production deployment settings

## Useful Commands

### Django
- `python manage.py startapp <appname>` - Create a new Django app
- `python manage.py makemigrations` - Create database migrations
- `python manage.py migrate` - Apply database migrations
- `python manage.py createsuperuser` - Create admin user

### Svelte
- `pnpm run build` - Build for production
- `pnpm run preview` - Preview production build
- `pnpm run check` - Type checking

## Development URLs
- Django Admin: http://127.0.0.1:8000/admin/
- Django API: http://127.0.0.1:8000/api/
- Svelte App: http://localhost:5173/