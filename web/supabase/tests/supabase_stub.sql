-- Minimal stand-in for the parts of Supabase the migrations rely on.
do $$ begin create role anon nologin; exception when duplicate_object then null; end $$;
do $$ begin create role authenticated nologin; exception when duplicate_object then null; end $$;
create schema auth;
create schema extensions;
create extension pgcrypto with schema extensions;
create table auth.users (id uuid primary key, email text);
create function auth.uid() returns uuid language sql stable as $$
  select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid
$$;
grant usage on schema auth, extensions, public to anon, authenticated;
grant execute on all functions in schema auth to anon, authenticated;
grant execute on all functions in schema extensions to anon, authenticated;
alter default privileges in schema public grant select, insert, update, delete on tables to anon, authenticated;
