-- =========================================================
-- Migration: half-star ratings, activity feed posts, reporting
-- Run this once in the Supabase SQL Editor.
-- =========================================================

-- Half-star ratings (was integer 1-5, now allows X.5 steps)
alter table reviews alter column rating type numeric(2,1) using rating::numeric(2,1);
alter table reviews drop constraint if exists reviews_rating_check;
alter table reviews add constraint reviews_rating_check
  check (rating >= 1 and rating <= 5 and (rating * 2) = floor(rating * 2));

alter table user_books alter column rating type numeric(2,1) using rating::numeric(2,1);
alter table user_books drop constraint if exists user_books_rating_check;
alter table user_books add constraint user_books_rating_check
  check (rating is null or (rating >= 1 and rating <= 5 and (rating * 2) = floor(rating * 2)));

-- Activity feed: manual posts + auto-logged reading milestones
create table if not exists activity_posts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  type text check (type in ('post','started_reading','finished_reading')) not null default 'post',
  body text,
  book_id uuid references books(id) on delete set null,
  created_at timestamptz default now()
);
alter table activity_posts enable row level security;
create policy "activity_posts_select_all" on activity_posts for select using (true);
create policy "activity_posts_insert_own" on activity_posts for insert with check (auth.uid() = user_id);
create policy "activity_posts_delete_own" on activity_posts for delete using (auth.uid() = user_id);

-- Reports (reviews, discussions, comments, posts) — no admin dashboard yet,
-- but content that crosses a report threshold is auto-collapsed behind a
-- "reported multiple times" toggle. Select is intentionally open (true) so
-- the app can compute per-item counts server-side; the app never displays
-- individual report reasons/reporters publicly, only aggregate counts.
create table if not exists reports (
  id uuid primary key default gen_random_uuid(),
  reporter_id uuid references profiles(id) on delete cascade,
  target_type text check (target_type in ('review','discussion','discussion_comment','review_comment','activity_post')) not null,
  target_id uuid not null,
  reason text,
  created_at timestamptz default now()
);
alter table reports enable row level security;
create policy "reports_select_all" on reports for select using (true);
create policy "reports_insert_own" on reports for insert with check (auth.uid() = reporter_id);
