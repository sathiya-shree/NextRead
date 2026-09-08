-- =========================================================
-- Migration: notifications, yearly reading goals, activity streaks
-- Run this once in the Supabase SQL Editor.
-- =========================================================

-- Notifications (follows, comments, likes, club joins)
create table if not exists notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,   -- recipient
  actor_id uuid references profiles(id) on delete cascade,  -- who triggered it
  type text check (type in ('follow','review_comment','review_like','discussion_reply','club_join')) not null,
  message text not null,
  link text not null,
  is_read boolean default false,
  created_at timestamptz default now()
);

-- Yearly reading goals ("12 of 24 books this year")
create table if not exists reading_goals (
  user_id uuid references profiles(id) on delete cascade,
  year int not null,
  target int not null check (target > 0),
  primary key (user_id, year)
);

-- One row per user per day they did something reading-related —
-- the basis for computing streaks.
create table if not exists reading_activity (
  user_id uuid references profiles(id) on delete cascade,
  activity_date date not null,
  primary key (user_id, activity_date)
);

alter table notifications enable row level security;
alter table reading_goals enable row level security;
alter table reading_activity enable row level security;

-- Notifications: only the recipient can read/manage their own; any signed-in
-- user can create one FOR someone else, but only naming themself as actor
-- (prevents spoofing who triggered it).
create policy "notifications_select_own" on notifications for select
  using (auth.uid() = user_id);
create policy "notifications_insert_as_actor" on notifications for insert
  with check (auth.uid() = actor_id);
create policy "notifications_update_own" on notifications for update
  using (auth.uid() = user_id);
create policy "notifications_delete_own" on notifications for delete
  using (auth.uid() = user_id);

-- Reading goals: private to the owner
create policy "reading_goals_select_own" on reading_goals for select
  using (auth.uid() = user_id);
create policy "reading_goals_upsert_own" on reading_goals for insert
  with check (auth.uid() = user_id);
create policy "reading_goals_update_own" on reading_goals for update
  using (auth.uid() = user_id);

-- Reading activity: publicly viewable (so streaks can show on profiles),
-- only the owner can log their own activity
create policy "reading_activity_select_all" on reading_activity for select using (true);
create policy "reading_activity_insert_own" on reading_activity for insert
  with check (auth.uid() = user_id);
