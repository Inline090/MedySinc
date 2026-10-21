# MedSync web client

A single page app built with React 19, React Router and Vite.

## Running it

```bash
npm install
npm run dev
```

It starts on http://localhost:3000 and talks to the API at http://localhost:8000
unless `VITE_API_URL` says otherwise.

## Building it

```bash
npm run build
```

The output is static files in `dist/`.

`VITE_API_URL` is baked in at build time, so changing it needs a rebuild, not a
restart.

## Layout

```
src/
  main.tsx        mounts React and sets up the router and the session
  App.tsx         the route table
  layouts/        AppShell (signed in) and AuthShell (signed out)
  pages/          one file per screen
  components/     shared pieces
  lib/            the API client, the session context and the response types
```

## Notes

The API client is plain `fetch`. When a request comes back 401 it refreshes the
session once and retries, so an expired access token is invisible to the user.

Session state lives in React context. There is no store, because the server owns the
data and each page fetches what it needs.