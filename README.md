# MedSync

MedSync is a personal medical document storage app. Upload medical documents,
keep them organised in one place, and use AI to make them easier to understand
later.

## Features

- User registration and login
- Upload medical documents such as reports, prescriptions, bills, and summaries
- Store document details including title, type, tags, and notes
- View, search, and filter uploaded documents
- Extract text from uploaded files
- Generate AI summaries of medical documents
- Ask questions answered from your own documents, with sources cited

## Tech Stack

### Frontend

- Next.js 16 (App Router)
- React 19
- Tailwind CSS 4

### Backend

- Python 3.13
- FastAPI
- PostgreSQL
- pgvector, for document embeddings
- Uvicorn

## Project Structure

```txt
medsync/
  apps/
    frontend/            Next.js client
    api/                 FastAPI service
      app/
        controllers/
        core/
        db/
        middlewares/
        models/
        repositories/
        routers/
        schemas/
        utils/
```

## Getting Started

### Database

```powershell
.\scripts\db-start.ps1
```

Starts a PostgreSQL 17 container with pgvector on port 5434, backed by the
`medsync-pgdata` volume.

```powershell
.\scripts\db-stop.ps1
```

Stops the container without discarding its data.

### Migrations

```bash
cd apps/api
uv run python -m app.db.migrate
```

Applies every `.sql` file in `app/db/migrations/` in filename order, recording
each one in the `schema_migrations` table so it runs at most once.

### API

```bash
cd apps/api
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload
```

The API runs at http://127.0.0.1:8000 and its interactive documentation is at
http://127.0.0.1:8000/docs.

Configuration is read from `apps/api/.env`:

| Variable | Description | Default |
| --- | --- | --- |
| `PORT` | Port the API listens on | `8000` |
| `DATABASE_URL` | PostgreSQL connection string | required |
| `CORS_ORIGIN` | Allowed browser origins, comma separated | `http://localhost:3000` |

### Lint and format

```bash
cd apps/api
uv run ruff check .
uv run ruff format .
```

Both run automatically on `git commit` for staged Python files. Install the hook
once per clone:

```bash
uv run --project apps/api pre-commit install
```

### Frontend

```bash
cd apps/frontend
npm install
npm run dev
```

The client runs at http://localhost:5173.

## License

MIT
