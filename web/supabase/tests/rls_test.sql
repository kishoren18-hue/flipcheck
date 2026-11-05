-- Row-level security and function tests. Each block asserts with RAISE.
\set ON_ERROR_STOP on
set client_min_messages = warning;

insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'teacher@example.com'),
  ('22222222-2222-2222-2222-222222222222', 'other@example.com');

-- helper: act as a role/user
create or replace function pg_temp.act(r text, uid text) returns void language plpgsql as $$
begin
  perform set_config('request.jwt.claim.sub', coalesce(uid, ''), false);
  execute format('set role %I', r);
end $$;

-- flipcheck
select pg_temp.act('authenticated', '11111111-1111-1111-1111-111111111111');
insert into public.fc_checks (question, model, agreement, flipped, result) values ('What is 2+2 really?', 'm', 1, false, '{}');
do $$ declare i int; begin
  for i in 1..15 loop if not public.fc_take_quota() then raise exception 'fc quota early'; end if; end loop;
  if public.fc_take_quota() then raise exception 'fc 16th allowed'; end if;
end $$;
reset role;
select pg_temp.act('authenticated', '22222222-2222-2222-2222-222222222222');
do $$ begin if (select count(*) from public.fc_checks) <> 0 then raise exception 'private check visible'; end if; end $$;
reset role;

select 'ALL RLS TESTS PASSED' as result;
