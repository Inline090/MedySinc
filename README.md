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

- React 19
- Vite

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
    frontend/            React client
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
| `CORS_ORIGIN` | Allowed browser origins, comma separated | `http://localhost:5173` |

### Lint and format

```bash
cd apps/api
uv run ruff check .
uv run ruff format .
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
