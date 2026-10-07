# MedSync

MedSync is a personal medical document assistant. Upload prescriptions, lab
reports and scans, then ask questions answered only from your own documents, with
each answer cited back to the file it came from.

## Architecture

```mermaid
flowchart TD
    Browser["Browser<br/>React 19 client components"]
    Web["Next.js on port 80<br/>App Router"]
    API["FastAPI on port 8000<br/>auth middleware and rate limiter"]
    Ingest["Ingestion, runs as a background task<br/>extract, chunk, embed"]
    Ask["Question answering<br/>search, rerank, write the answer"]
    DB[("PostgreSQL with pgvector<br/>documents, chunks, answer cache")]
    Store["Object storage<br/>S3 or local disk"]
    Model["Model API<br/>answers, summaries, medicines"]

    Browser -->|HTTPS| Web
    Web -->|"fetch /api/* with cookies"| API
    API -->|"upload returns first"| Ingest
    API -->|ask| Ask
    Ingest -.->|"the original file"| Store
    Ask -.->|"redacted excerpts"| Model
    Ingest -->|"text and vectors"| DB
    Ask -->|"your own chunks"| DB
```

Solid arrows are the request path. Dotted arrows are stored or external.

One host runs both apps. The browser talks to Next.js on port 80, Next.js talks to
the API on port 8000, and the API owns the database, the file storage and the model
calls. Ingestion runs as a background task inside the API process rather than in a
separate worker, so an upload returns before its document has finished being read.

## Features

- Register and sign in, or sign in with Google
- Upload PDFs and images. A PDF with no text layer is read with OCR
- Rename, annotate, download or delete any document you have uploaded
- Reject a file you have already uploaded, checked by content hash
- Generate an AI summary of a single document
- Ask a question and get an answer with its source cited and a one-word
  confidence label, or an explicit refusal when nothing relevant is found
- See every medicine found across your prescriptions
- Rate limits on register, login, upload and ask

## Tech stack

Frontend

- Next.js 16 (App Router), React 19, TypeScript
- Tailwind CSS 4

Backend

- Python 3.13, FastAPI
- PostgreSQL 17 with pgvector
- bge-m3 embeddings and a cross-encoder reranker, both running locally
- PaddleOCR for scanned documents
- uv for dependencies and the virtualenv

## Project structure

```txt
medsync/
  apps/
    frontend/            Next.js client
    api/                 FastAPI service
      app/
        ai/              extraction, chunking, embeddings, retrieval, answers
        controllers/     use cases
        core/            config, security, tokens, rate limiting
        db/              connection pool, migration runner and numbered .sql files
        middlewares/     auth dependency
        repositories/    all SQL lives here
        routers/         routes and their rate limits
        schemas/         request shapes
        storage/         local disk and S3 behind one interface
  scripts/               database helpers
```

## Getting started

### Database

```powershell
.\scripts\db-start.ps1
```

Starts PostgreSQL 17 with pgvector in a container named `medsync-postgres` on port
5434, backed by the `medsync-pgdata` volume. The script is safe to re-run: it
starts an existing container instead of creating a second one.

```powershell
.\scripts\db-stop.ps1
```

Stops the container without discarding its data.

### Configuration

```bash
cd apps/api
cp .env.example .env
```

`.env` is gitignored. `.env.example` lists every setting with its default and a
comment. For local development you only need to fill in a few of them. Paste this
block into `apps/api/.env`:

```ini
DATABASE_URL=postgresql://postgres:postgres@localhost:5434/medsync
JWT_SECRET=replace-with-a-long-random-secret
CORS_ORIGIN=http://localhost:3000
FRONTEND_URL=http://localhost:3000
STORAGE_BACKEND=local
AI_API_KEY=your-google-ai-studio-key
```

`AI_API_KEY` is the only one that needs an account. Without it the app runs and
everything works except answer generation and summaries, which return a clear
error. Google sign-in also needs `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`;
without them the Google button returns 503 and email sign-in still works.

### Migrations

```bash
cd apps/api
uv run python -m app.db.migrate
```

Applies every `.sql` file in `app/db/migrations/` in filename order, recording
each one in the `schema_migrations` table so it runs at most once. Re-running is
harmless. Migrations are not run at startup, so several API instances cannot race
each other.

### API

```bash
cd apps/api
uv sync
uv run uvicorn app.main:app --reload
```

The API runs at http://127.0.0.1:8000 and its interactive documentation is at
http://127.0.0.1:8000/docs.

### Frontend

```bash
cd apps/frontend
npm install
npm run dev
```

The client runs at http://localhost:3000.

### Tests

```bash
cd apps/api
uv run pytest
```

The API tests need the database running. They use a separate `medsync_test`
database and truncate tables between tests.

### Lint and format

Python:

```bash
cd apps/api
uv run ruff check .
uv run ruff format .
```

Client:

```bash
cd apps/frontend
npm run lint
npx tsc --noEmit
```

The Python checks run automatically on `git commit` for staged files. Install the
hook once per clone:

```bash
uv run --project apps/api pre-commit install
```

## License

MIT