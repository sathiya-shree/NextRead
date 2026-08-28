-- =========================================================
-- Shelfie: Goodreads + Fable hybrid — Supabase schema
-- Run this in the Supabase SQL Editor (Project > SQL Editor)
-- =========================================================

-- Profiles (extends Supabase auth.users)
create table if not exists profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  username text unique not null,
  display_name text,
  avatar_url text,
  bio text,
  created_at timestamptz default now()
);

-- Books (shared catalog — anyone authenticated can add a book)
create table if not exists books (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  author text not null,
  isbn text,
  cover_url text,
  description text,
  page_count int,
  published_year int,
  genre text,
  added_by uuid references profiles(id),
  created_at timestamptz default now()
);
create index if not exists idx_books_title on books using gin (to_tsvector('english', title || ' ' || author));

-- Shelves / reading status (Goodreads-style: want_to_read, reading, read)
create table if not exists user_books (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  book_id uuid references books(id) on delete cascade,
  status text check (status in ('want_to_read','reading','read')) not null default 'want_to_read',
  rating int check (rating between 1 and 5),
  progress_pages int default 0,
  started_at timestamptz,
  finished_at timestamptz,
  updated_at timestamptz default now(),
  unique (user_id, book_id)
);

-- Reviews (Goodreads-style long-form review, separate from quick rating)
create table if not exists reviews (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  book_id uuid references books(id) on delete cascade,
  rating int check (rating between 1 and 5) not null,
  body text,
  spoiler boolean default false,
  created_at timestamptz default now(),
  unique (user_id, book_id)
);

-- Likes on reviews (social layer, like Fable)
create table if not exists review_likes (
  review_id uuid references reviews(id) on delete cascade,
  user_id uuid references profiles(id) on delete cascade,
  created_at timestamptz default now(),
  primary key (review_id, user_id)
);

-- Comments on reviews
create table if not exists review_comments (
  id uuid primary key default gen_random_uuid(),
  review_id uuid references reviews(id) on delete cascade,
  user_id uuid references profiles(id) on delete cascade,
  body text not null,
  created_at timestamptz default now()
);

-- Follows (social graph)
create table if not exists follows (
  follower_id uuid references profiles(id) on delete cascade,
  following_id uuid references profiles(id) on delete cascade,
  created_at timestamptz default now(),
  primary key (follower_id, following_id),
  check (follower_id <> following_id)
);

-- Book Clubs (Fable-style)
create table if not exists clubs (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  description text,
  cover_url text,
  is_private boolean default false,
  owner_id uuid references profiles(id),
  created_at timestamptz default now()
);

create table if not exists club_members (
  club_id uuid references clubs(id) on delete cascade,
  user_id uuid references profiles(id) on delete cascade,
  role text check (role in ('owner','moderator','member')) default 'member',
  joined_at timestamptz default now(),
  primary key (club_id, user_id)
);

-- The book currently (or previously) assigned to a club
create table if not exists club_books (
  id uuid primary key default gen_random_uuid(),
  club_id uuid references clubs(id) on delete cascade,
  book_id uuid references books(id) on delete cascade,
  is_current boolean default true,
  start_date date,
  end_date date,
  created_at timestamptz default now()
);

-- Discussion threads inside a club (can be tied to a chapter/page range)
create table if not exists discussions (
  id uuid primary key default gen_random_uuid(),
  club_id uuid references clubs(id) on delete cascade,
  club_book_id uuid references club_books(id) on delete cascade,
  user_id uuid references profiles(id) on delete cascade,
  title text not null,
  body text,
  page_marker int,
  spoiler boolean default false,
  created_at timestamptz default now()
);

create table if not exists discussion_comments (
  id uuid primary key default gen_random_uuid(),
  discussion_id uuid references discussions(id) on delete cascade,
  user_id uuid references profiles(id) on delete cascade,
  body text not null,
  created_at timestamptz default now()
);

-- Custom lists (e.g. "Favorites", "Beach reads") — user-curated, separate
-- from the fixed want_to_read/reading/read shelves.
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

-- =========================================================
-- Row Level Security
-- =========================================================
alter table profiles enable row level security;
alter table books enable row level security;
alter table user_books enable row level security;
alter table reviews enable row level security;
alter table review_likes enable row level security;
alter table review_comments enable row level security;
alter table follows enable row level security;
alter table clubs enable row level security;
alter table club_members enable row level security;
alter table club_books enable row level security;
alter table discussions enable row level security;
alter table discussion_comments enable row level security;
alter table custom_lists enable row level security;
alter table list_books enable row level security;

-- Profiles: readable by everyone, editable by owner
create policy "profiles_select_all" on profiles for select using (true);
create policy "profiles_update_own" on profiles for update using (auth.uid() = id);
create policy "profiles_insert_own" on profiles for insert with check (auth.uid() = id);

-- Books: readable by everyone, insertable by any logged-in user
create policy "books_select_all" on books for select using (true);
create policy "books_insert_auth" on books for insert with check (auth.uid() is not null);

-- User books (shelves): only owner can see/edit their own shelf
create policy "user_books_select_own" on user_books for select using (auth.uid() = user_id);
create policy "user_books_cud_own" on user_books for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Reviews: public read, owner write
create policy "reviews_select_all" on reviews for select using (true);
create policy "reviews_cud_own" on reviews for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Review likes: public read, owner write
create policy "review_likes_select_all" on review_likes for select using (true);
create policy "review_likes_cud_own" on review_likes for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Review comments: public read, owner write
create policy "review_comments_select_all" on review_comments for select using (true);
create policy "review_comments_cud_own" on review_comments for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Follows: public read, owner write
create policy "follows_select_all" on follows for select using (true);
create policy "follows_cud_own" on follows for all using (auth.uid() = follower_id) with check (auth.uid() = follower_id);

-- Clubs: public read (non-private) or member read; owner write
create policy "clubs_select_all" on clubs for select using (true);
create policy "clubs_insert_auth" on clubs for insert with check (auth.uid() = owner_id);
create policy "clubs_update_owner" on clubs for update using (auth.uid() = owner_id);

-- Club members: public read, self join/leave
create policy "club_members_select_all" on club_members for select using (true);
create policy "club_members_insert_self" on club_members for insert with check (auth.uid() = user_id);
create policy "club_members_delete_self" on club_members for delete using (auth.uid() = user_id);

-- Club books: public read, club owner/mod write (simplified: any member can propose)
create policy "club_books_select_all" on club_books for select using (true);
create policy "club_books_insert_member" on club_books for insert
  with check (exists (select 1 from club_members m where m.club_id = club_books.club_id and m.user_id = auth.uid()));

-- Discussions: public read, member write
create policy "discussions_select_all" on discussions for select using (true);
create policy "discussions_insert_member" on discussions for insert
  with check (auth.uid() = user_id and exists (select 1 from club_members m where m.club_id = discussions.club_id and m.user_id = auth.uid()));

-- Discussion comments: public read, member write
create policy "discussion_comments_select_all" on discussion_comments for select using (true);
create policy "discussion_comments_insert_auth" on discussion_comments for insert with check (auth.uid() = user_id);

-- Custom lists: visible if public, or owned; only the owner can write
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

-- =========================================================
-- Storage bucket for profile avatars
-- =========================================================
insert into storage.buckets (id, name, public)
values ('avatars', 'avatars', true)
on conflict (id) do nothing;

-- Anyone can view avatars (public bucket)
create policy "avatar_public_read" on storage.objects for select
  using (bucket_id = 'avatars');

-- A user can only upload/update/delete files inside their own folder,
-- i.e. a path like {user_id}/whatever.jpg
create policy "avatar_owner_insert" on storage.objects for insert
  with check (bucket_id = 'avatars' and (storage.foldername(name))[1] = auth.uid()::text);

create policy "avatar_owner_update" on storage.objects for update
  using (bucket_id = 'avatars' and (storage.foldername(name))[1] = auth.uid()::text);

create policy "avatar_owner_delete" on storage.objects for delete
  using (bucket_id = 'avatars' and (storage.foldername(name))[1] = auth.uid()::text);

-- =========================================================
-- Auto-create a profile row when a new auth user signs up
-- =========================================================
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, username, display_name)
  values (new.id, split_part(new.email, '@', 1) || '_' || substr(new.id::text, 1, 4), split_part(new.email, '@', 1));
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
