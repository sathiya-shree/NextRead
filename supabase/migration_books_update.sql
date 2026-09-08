-- =========================================================
-- Migration: allow updating shared catalog books (e.g. backfilling
-- missing cover images after a CSV import). Run once in the SQL Editor.
-- =========================================================

create policy "books_update_auth" on books for update
  using (auth.uid() is not null)
  with check (auth.uid() is not null);
