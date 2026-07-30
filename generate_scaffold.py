from pathlib import Path

root = Path(r'c:\Users\kenne\Documents\cmsc-personal_project\adventure-engine')
entries = {
    '.gitignore': """# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
/dist
/build
/.vite
.DS_Store

# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
*.pyd
*.env
venv/
env/
.venv/
*.sqlite3
*.sqlite
*.db
coverage/

# IDE
.vscode/
.idea/
*.swp
""",
    'README.md': """# Adventure Arbitrage Engine

A portfolio-quality full-stack scaffold for the Adventure Arbitrage Engine.

## Structure

- `frontend/` - React + TypeScript application with routing and environment support.
- `backend/` - FastAPI Python service with structured API, database, and configuration support.
- `database/` - SQLite initialization and schema files.
- `data/` - Placeholder folders for destination, activities, deals, and user preferences data.
- `algorithms/` - Placeholder modules for recommendation scoring and ranking logic.
- `scrapers/` - Placeholder modules for future data collection.
- `api_connections/` - Placeholder modules for external API integrations.
- `tests/` - Frontend and backend test folders.
- `documentation/` - Architecture documentation and development notes.

## Quickstart

### Frontend
```bash
cd adventure-engine/frontend
npm install
npm run dev
```
Open `http://localhost:5173` to confirm the React homepage.

### Backend
```bash
cd adventure-engine/backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Visit `http://localhost:8000/api/health` for the health check endpoint.

### Database
```bash
cd adventure-engine/database
python init_db.py
```

## Roadmap

1. Build the recommendation engine and scoring modules.
2. Add external API connectors and scrapers.
3. Implement PostgreSQL migration support.
4. Add tests for frontend and backend functionality.
""",
    'frontend/package.json': """{
  "name": "adventure-engine-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.16.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@types/react-router-dom": "^6.4.0",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.6.0",
    "vite": "^5.4.0"
  }
}
""",
    'frontend/tsconfig.json': """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
""",
    'frontend/tsconfig.node.json': """{
  "compilerOptions": {
    "module": "ESNext",
    "moduleResolution": "Node"
  }
}
""",
    'frontend/vite.config.ts': """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
});
""",
    'frontend/.env.example': """VITE_API_URL=http://localhost:8000/api
""",
    'frontend/README.md': """# Frontend

This directory contains the React + TypeScript frontend for Adventure Arbitrage Engine.

## Setup

```bash
npm install
npm run dev
```

Open `http://localhost:5173`.
""",
    'frontend/public/index.html': """<!DOCTYPE html>
<html lang=\"en\">
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>Adventure Arbitrage Engine</title>
  </head>
  <body>
    <div id=\"root\"></div>
    <script type=\"module\" src=\"/src/main.tsx\"></script>
  </body>
</html>
""",
    'frontend/src/main.tsx': """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
""",
    'frontend/src/App.tsx': """import { BrowserRouter } from 'react-router-dom';
import AppRoutes from './routes/AppRoutes';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className='app-shell'>
        <AppRoutes />
      </div>
    </BrowserRouter>
  );
}

export default App;
""",
    'frontend/src/routes/AppRoutes.tsx': """import { Routes, Route, Link } from 'react-router-dom';
import HomePage from '../pages/HomePage';
import NotFoundPage from '../pages/NotFoundPage';

export default function AppRoutes() {
  return (
    <div>
      <header className='app-header'>
        <Link to='/' className='brand'>Adventure Arbitrage Engine</Link>
      </header>
      <Routes>
        <Route path='/' element={<HomePage />} />
        <Route path='*' element={<NotFoundPage />} />
      </Routes>
    </div>
  );
}
""",
    'frontend/src/pages/HomePage.tsx': """import { API_BASE_URL } from '../services/api';

export default function HomePage() {
  return (
    <main className='home-page'>
      <h1>Adventure Arbitrage Engine</h1>
      <p>Your full-stack portfolio scaffold is running.</p>
      <p>Backend API base URL: <code>{API_BASE_URL}</code></p>
      <p>Use <code>/health</code> on the backend to confirm connectivity.</p>
    </main>
  );
}
""",
    'frontend/src/pages/NotFoundPage.tsx': """export default function NotFoundPage() {
  return (
    <main>
      <h2>Page not found</h2>
      <p>The requested route does not exist.</p>
    </main>
  );
}
""",
    'frontend/src/services/api.ts': """export const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api';
""",
    'frontend/src/App.css': """body {
  margin: 0;
  font-family: Inter, system-ui, sans-serif;
}

.app-shell {
  min-height: 100vh;
  background: #f5f7fb;
  color: #102a43;
}

.app-header {
  padding: 1rem 2rem;
  background: #1f2937;
}

.brand {
  color: #ffffff;
  text-decoration: none;
  font-size: 1.25rem;
  font-weight: 700;
}

.home-page {
  padding: 3rem 2rem;
}
""",
    'frontend/src/index.css': """* {
  box-sizing: border-box;
}

html, body, #root {
  min-height: 100%;
}

body {
  margin: 0;
  background: #f5f7fb;
  color: #102a43;
}
""",
    'backend/pyproject.toml': """[project]
name = "adventure-engine-backend"
version = "0.1.0"
description = "FastAPI backend for Adventure Arbitrage Engine"
requires-python = ">=3.10"

dependencies = [
  "fastapi>=0.110.0",
  "uvicorn[standard]>=0.23.0",
  "python-dotenv>=1.0.0",
  "pydantic>=2.10.0",
  "sqlalchemy>=2.0.0"
]

[project.scripts]
start = "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
""",
    'backend/requirements.txt': """fastapi>=0.110.0
uvicorn[standard]>=0.23.0
python-dotenv>=1.0.0
pydantic>=2.10.0
sqlalchemy>=2.0.0
""",
    'backend/.env.example': """DATABASE_URL=sqlite:///./adventure.db
APP_ENV=development
SECRET_KEY=change-me
""",
    'backend/README.md': """# Backend

This directory contains the FastAPI backend for Adventure Arbitrage Engine.

## Setup

```bash
cd adventure-engine/backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Health Check

Visit `http://localhost:8000/api/health`.
""",
    'backend/app/main.py': """from fastapi import FastAPI
from app.api.routes.health import router as health_router

app = FastAPI(title='Adventure Arbitrage Engine API')
app.include_router(health_router, prefix='/api')

@app.get('/')
def root():
    return {'message': 'Adventure Arbitrage Engine backend is running.'}
""",
    'backend/app/core/config.py': """from pathlib import Path
from pydantic import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    app_name: str = 'Adventure Arbitrage Engine API'
    database_url: str = 'sqlite:///./adventure.db'
    environment: str = 'development'
    secret_key: str = 'change-me'

    class Config:
        env_file = BASE_DIR / '.env'
        case_sensitive = True

settings = Settings()
""",
    'backend/app/api/__init__.py': """# API package for route registration and dependency wiring
""",
    'backend/app/api/routes/__init__.py': """from .health import router as health_router

__all__ = ['health_router']
""",
    'backend/app/api/routes/health.py': """from fastapi import APIRouter

router = APIRouter()

@router.get('/health')
def health_check():
    return {'status': 'ok', 'message': 'Backend is healthy.'}
""",
    'backend/app/services/__init__.py': """# Service layer placeholder for business logic and helpers
""",
    'backend/app/database/__init__.py': """# Database package placeholder for connection and migration utilities
""",
    'backend/app/database/connection.py': """# Placeholder database connection and session management utilities
""",
    'backend/app/models/__init__.py': """# Models package placeholder for SQLAlchemy models and schemas
""",
    'backend/app/models/base.py': """from sqlalchemy.orm import declarative_base

Base = declarative_base()
""",
    'database/schema.sql': """-- SQLite schema for initial Adventure Arbitrage Engine data
CREATE TABLE IF NOT EXISTS health_checks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  checked_at TEXT NOT NULL
);
""",
    'database/init_db.py': """import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent / 'adventure.db'
SCHEMA_PATH = BASE_DIR / 'schema.sql'


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        with SCHEMA_PATH.open('r', encoding='utf-8') as schema_file:
            connection.executescript(schema_file.read())
    print(f'Initialized SQLite database at {DB_PATH}')


if __name__ == '__main__':
    init_db()
""",
    'database/migrations/.gitkeep': '',
    'data/destinations/.gitkeep': '',
    'data/activities/.gitkeep': '',
    'data/deals/.gitkeep': '',
    'data/preferences/.gitkeep': '',
    'algorithms/scoring/.gitkeep': '',
    'algorithms/ranking/.gitkeep': '',
    'scrapers/destinations/.gitkeep': '',
    'scrapers/activities/.gitkeep': '',
    'scrapers/deals/.gitkeep': '',
    'api_connections/travel/.gitkeep': '',
    'api_connections/payments/.gitkeep': '',
    'tests/frontend/.gitkeep': '',
    'tests/backend/.gitkeep': '',
    'documentation/architecture.md': """# Architecture

This project is structured as a full-stack application with separate frontend and backend modules.

- `frontend/` contains the React + TypeScript user interface.
- `backend/` contains the FastAPI application with API routes and database scaffolding.
- `database/` contains SQLite schema and initialization tooling.
- `data/`, `algorithms/`, `scrapers/`, and `api_connections/` are placeholders for future domain logic.
""",
    'documentation/development_notes.md': """# Development Notes

- Use SQLite locally and configure PostgreSQL for production later.
- Maintain separate service, database, and model layers in the backend.
- Keep frontend routes and API client code decoupled.
- Add tests for each backend endpoint and frontend page.
""",
}

for relative_path, content in entries.items():
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')

print('Created scaffold at', root)
