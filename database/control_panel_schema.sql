-- SHRI AI Control Panel schema (Postgres / Supabase)

create table if not exists cp_agents (
  agent_id uuid primary key default gen_random_uuid(),
  name text not null,
  description text not null default '',
  system_prompt text not null default 'You are a helpful AI assistant.',
  api_key text not null unique,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists cp_channels (
  channel_id uuid primary key default gen_random_uuid(),
  agent_id uuid not null references cp_agents(agent_id) on delete cascade,
  channel_type text not null,
  config jsonb not null default '{}'::jsonb,
  connected_at timestamptz not null default now(),
  unique (agent_id, channel_type)
);

create table if not exists cp_usage_events (
  event_id uuid primary key default gen_random_uuid(),
  agent_id uuid not null references cp_agents(agent_id) on delete cascade,
  event_type text not null,
  meta jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_cp_usage_events_agent_created_at
  on cp_usage_events(agent_id, created_at desc);
