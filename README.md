# Shelfie — Goodreads × Fable

A book-tracking + social reading app. Track what you read (want to read / reading /
read), rate and review books, follow other readers, and run book clubs with
chapter-by-chapter discussion threads — like a mashup of Goodreads and Fable.

**Stack:** FastAPI (Python) + Jinja2 templates + Tailwind (CDN) · Supabase (Postgres +
Auth) · deployed on Vercel.

## Features

- **Shelves** — want to read / currently reading / read, per user
- **Ratings & reviews** — 1–5 stars, spoiler-tagged text reviews, likes
- **Social graph** — follow/unfollow, public profile with shelves + reviews
- **Book clubs** — create/join clubs, assign a "current book," start discussion
  threads pinned to a page number, spoiler-tagged replies
- **Activity feed** — recent reviews across the whole app on the homepage
- **Auth** — email/password via Supabase Auth, session cookie-based

## Project structure

```
app/
  main.py            FastAPI app + middleware + router registration
  db.py               Supabase client setup
  auth.py             session/current-user helpers
  templating.py       Jinja2 render() helper
  routers/
    auth_router.py    signup/login/logout
    books.py          home feed, add book, book detail
    shelves.py         shelve/unshelve
    reviews.py         write review, like, comment
    clubs.py            create/join club, assign book, discussions
    users.py            profile pages, follow/unfollow
  templates/           Jinja2 HTML templates
  static/              CSS/assets (Tailwind is loaded via CDN, no build step)
api/index.py           Vercel serverless entrypoint (re-exports app.main:app)
supabase/schema.sql     full DB schema + Row Level Security policies
vercel.json              Vercel routing/build config
requirements.txt
.env.example
```

## 1. Set up Supabase

1. Create a free project at [supabase.com](https://supabase.com).
2. In **SQL Editor**, paste the contents of `supabase/schema.sql` and run it.
   This creates every table (profiles, books, user_books, reviews, follows,
   clubs, club_members, club_books, discussions, discussion_comments), enables
   Row Level Security, and adds a trigger that auto-creates a `profiles` row
   whenever someone signs up.
3. In **Project Settings → API**, copy:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` key → `SUPABASE_ANON_KEY`
   - `service_role` key → `SUPABASE_SERVICE_ROLE_KEY` (keep secret; used server-side only)
4. Optional: in **Authentication → Providers**, disable "Confirm email" while
   developing so signup logs you in immediately.

## 2. Run locally

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env with your Supabase URL + keys

uvicorn app.main:app --reload
```

Visit `http://localhost:8000`.

## 3. Deploy to Vercel

```bash
npm i -g vercel
vercel login
vercel
```

When prompted, accept the defaults (the included `vercel.json` handles the
Python build via `@vercel/python`, pointed at `api/index.py`). Then add your
environment variables:

```bash
vercel env add SUPABASE_URL
vercel env add SUPABASE_ANON_KEY
vercel env add SUPABASE_SERVICE_ROLE_KEY
vercel env add SESSION_SECRET
vercel --prod
```

(You can also paste these into the Vercel dashboard under
**Project → Settings → Environment Variables** instead of the CLI.)

`SESSION_SECRET` can be any long random string — used to sign the login
session cookie (`openssl rand -hex 32` works well).

## How auth works

Supabase Auth issues a JWT `access_token` on login/signup. Shelfie stores that
token in a server-side session cookie (via `SessionMiddleware`). Every
authenticated Supabase request is made with `client.postgrest.auth(access_token)`,
so **Postgres Row Level Security enforces permissions** (e.g. you can only
edit your own shelf/reviews) — the app code doesn't have to re-implement
authorization, the database does.

## Extending it

Natural next additions, all straightforward given the schema:
- Cover image upload via Supabase Storage instead of pasting a URL
- Reading progress bar / pages-per-day stats
- Club moderator tools (remove posts, private club invites)
- Genre/shelf-based recommendations
- Full-text search using the `pg_trgm`/`tsvector` index already on `books.title`
