-- flipcheck: saved live checks and a per-user daily quota. Row-level security on every table.

create table if not exists public.fc_checks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  question text not null check (char_length(question) between 8 and 600),
  model text not null check (char_length(model) <= 80),
  agreement real not null check (agreement between 0 and 1),
  flipped boolean not null,
  result jsonb not null,
  is_public boolean not null default false,
  created_at timestamptz not null default now()
);

create index if not exists fc_checks_user_created on public.fc_checks (user_id, created_at desc);
create index if not exists fc_checks_public_created on public.fc_checks (created_at desc) where is_public;

alter table public.fc_checks enable row level security;

drop policy if exists "read own or public checks" on public.fc_checks;
create policy "read own or public checks" on public.fc_checks
  for select using (is_public or user_id = (select auth.uid()));

drop policy if exists "insert own checks" on public.fc_checks;
create policy "insert own checks" on public.fc_checks
  for insert to authenticated with check (user_id = (select auth.uid()));

drop policy if exists "update own checks" on public.fc_checks;
create policy "update own checks" on public.fc_checks
  for update to authenticated using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));

drop policy if exists "delete own checks" on public.fc_checks;
create policy "delete own checks" on public.fc_checks
  for delete to authenticated using (user_id = (select auth.uid()));

create table if not exists public.fc_usage (
  user_id uuid not null references auth.users (id) on delete cascade,
  day date not null default current_date,
  count integer not null default 0,
  primary key (user_id, day)
);
alter table public.fc_usage enable row level security;

create or replace function public.fc_take_quota()
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  uid uuid := auth.uid();
  n integer;
begin
  if uid is null then
    return false;
  end if;
  insert into public.fc_usage (user_id, day, count)
  values (uid, current_date, 1)
  on conflict (user_id, day) do update set count = public.fc_usage.count + 1
  returning count into n;
  return n <= 15;
end;
$$;

revoke all on function public.fc_take_quota() from public, anon;
grant execute on function public.fc_take_quota() to authenticated;
