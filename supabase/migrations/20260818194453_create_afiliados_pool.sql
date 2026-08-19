-- Pool de prospeccao de afiliados: 100% da raspagem do Apify vive aqui.
-- Somente os aptos (com e-mail, score ok, ativos) sao enviados ao GHL.

create table public.creators (
  handle              text primary key,
  nickname            text,
  platform            text not null default 'TikTok',
  profile_url         text,
  fans                integer,
  engagement_pct      numeric(7,2),
  posts_30d           integer,
  last_post_at        timestamptz,
  bio                 text,
  bio_link            text,
  bio_domain          text,
  email               text,
  tt_seller           boolean,
  commerce_user       boolean,
  commerce_category   text,
  private_account     boolean,
  verified            boolean,

  -- derivados pelo classificador
  vitrine             text,
  score_afiliado      integer,
  trilha              text,
  kit_alocado         text,
  marca_alocada       text,
  comissao_pct        numeric(6,2),
  tema_do_video       text,
  tema_revisado       boolean not null default false,

  -- origem
  search_query        text,
  search_hashtag      text,
  first_seen_at       timestamptz not null default now(),
  last_seen_at        timestamptz not null default now(),
  run_count           integer not null default 1,

  -- roteamento
  status              text not null default 'pool'
                      check (status in ('pool','apto_email','no_ghl','fila_dm','descartado')),
  descarte_motivo     text,
  ghl_contact_id      text,
  ghl_opportunity_id  text,
  synced_at           timestamptz,

  updated_at          timestamptz not null default now()
);

comment on table public.creators is 'Pool de criadores raspados do TikTok via Apify. Uma linha por handle.';
comment on column public.creators.status is 'pool=nao avaliado, apto_email=fila do GHL, no_ghl=ja criado, fila_dm=sem e-mail, descartado=reprovado';
comment on column public.creators.marca_alocada is 'DERIVAR DO KIT, nunca do nicho: o kit e o que vai na nota fiscal';

create index creators_status_idx        on public.creators (status);
create index creators_score_idx         on public.creators (score_afiliado desc nulls last);
create index creators_last_post_idx     on public.creators (last_post_at desc nulls last);
create index creators_email_idx         on public.creators (email) where email is not null;
create index creators_trilha_idx        on public.creators (trilha);
create unique index creators_ghl_uidx   on public.creators (ghl_contact_id) where ghl_contact_id is not null;

create table public.creator_videos (
  video_url     text primary key,
  handle        text not null references public.creators(handle) on delete cascade,
  posted_at     timestamptz,
  play_count    bigint,
  digg_count    bigint,
  comment_count bigint,
  share_count   bigint,
  caption       text,
  hashtags      text[],
  search_query  text,
  collected_at  timestamptz not null default now()
);

comment on table public.creator_videos is 'Um registro por video coletado. Base para engajamento, recencia e tema do video.';

create index creator_videos_handle_idx on public.creator_videos (handle);
create index creator_videos_posted_idx on public.creator_videos (posted_at desc nulls last);

-- Log de execucoes do Apify, para auditoria e para nao reprocessar dataset
create table public.apify_runs (
  run_id          text primary key,
  dataset_id      text,
  actor_id        text,
  status          text,
  items_recebidos integer,
  criadores_novos integer,
  videos_novos    integer,
  erro            text,
  received_at     timestamptz not null default now(),
  processed_at    timestamptz
);

comment on table public.apify_runs is 'Auditoria das rodadas do scraper. Evita reprocessar o mesmo dataset.';

-- RLS ligado e SEM policy publica: so a service_role acessa.
-- Necessario porque o projeto esta com Data API e auto-expose ativos,
-- e estes dados sao pessoais (nome, e-mail e depois CPF e endereco).
alter table public.creators       enable row level security;
alter table public.creator_videos enable row level security;
alter table public.apify_runs     enable row level security;

-- Mantem updated_at coerente
create or replace function public.touch_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

create trigger creators_touch
  before update on public.creators
  for each row execute function public.touch_updated_at();
