-- =========================================================
-- Migration: custom lists (e.g. "Favorites", "Beach reads")
-- Run this once in the Supabase SQL Editor.
-- =========================================================

create table if not exists custom_lists (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  name text not null,
  description text,
  is_public boolean default true,
  created_at timestamptz default now()
);

create table if not exists list_books (
  id uuid primary key default gen_random_uuid(),
  list_id uuid references custom_lists(id) on delete cascade,
  book_id uuid references books(id) on delete cascade,
  added_at timestamptz default now(),
  unique (list_id, book_id)
);

create policy "books_update_auth" on books for update
  using (auth.uid() is not null)
  with check (auth.uid() is not null);

alter table custom_lists enable row level security;
alter table list_books enable row level security;

-- Lists: visible if public, or if you own them; only the owner can write
create policy "custom_lists_select" on custom_lists for select
  using (is_public or user_id = auth.uid());
create policy "custom_lists_insert_own" on custom_lists for insert
  with check (auth.uid() = user_id);
create policy "custom_lists_update_own" on custom_lists for update
  using (auth.uid() = user_id);
create policy "custom_lists_delete_own" on custom_lists for delete
  using (auth.uid() = user_id);

-- List entries: visible if the parent list is visible; only the list owner can add/remove books
create policy "list_books_select" on list_books for select
  using (
    exists (
      select 1 from custom_lists l
      where l.id = list_books.list_id and (l.is_public or l.user_id = auth.uid())
    )
  );
create policy "list_books_insert_owner" on list_books for insert
  with check (
    exists (select 1 from custom_lists l where l.id = list_books.list_id and l.user_id = auth.uid())
  );
create policy "list_books_delete_owner" on list_books for delete
  using (
    exists (select 1 from custom_lists l where l.id = list_books.list_id and l.user_id = auth.uid())
  );
