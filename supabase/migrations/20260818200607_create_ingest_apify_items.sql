-- Recebe os itens crus do dataset do Apify e faz tudo:
-- grava videos, agrega por criador, deriva campos e roteia.
-- A Edge Function so busca os dados e chama isto.

create or replace function public.ingest_apify_items(
  p_run_id     text,
  p_dataset_id text,
  p_items      jsonb
)
returns jsonb
language plpgsql
set search_path = public, pg_temp
as $$
declare
  v_itens int := jsonb_array_length(coalesce(p_items,'[]'::jsonb));
  v_videos int := 0;
  v_novos int := 0;
  v_antes int;
  v_result jsonb;
begin
  select count(*) into v_antes from public.creators;

  -- 1) criadores primeiro (creator_videos tem FK)
  with itens as (
    select i from jsonb_array_elements(p_items) i
  ),
  base as (
    select
      nullif(i->'authorMeta'->>'name','')            as handle,
      i->'authorMeta'->>'nickName'                   as nickname,
      i->'authorMeta'->>'signature'                  as bio,
      i->'authorMeta'->>'bioLink'                    as bio_link,
      (i->'authorMeta'->>'fans')::numeric            as fans,
      (i->'authorMeta'->>'video')::numeric           as vid_total,
      (i->'authorMeta'->>'verified')::boolean        as verified,
      (i->'authorMeta'->>'privateAccount')::boolean  as private_account,
      (i->'authorMeta'->>'ttSeller')::boolean        as tt_seller,
      (i->'authorMeta'->'commerceUserInfo'->>'commerceUser')::boolean as commerce_user,
      i->'authorMeta'->'commerceUserInfo'->>'category' as commerce_category,
      i->>'searchQuery'                              as search_query,
      i->'searchHashtag'->>'name'                    as search_hashtag,
      nullif(i->>'createTimeISO','')::timestamptz    as posted_at,
      coalesce((i->>'playCount')::numeric,0)         as play_count,
      coalesce((i->>'diggCount')::numeric,0)         as digg_count,
      coalesce((i->>'commentCount')::numeric,0)      as comment_count,
      coalesce((i->>'shareCount')::numeric,0)        as share_count
    from itens
  ),
  agg as (
    select
      handle,
      max(nickname)                        as nickname,
      max(bio)                             as bio,
      max(bio_link)                        as bio_link,
      max(fans)::int                       as fans,
      bool_or(verified)                    as verified,
      bool_or(private_account)             as private_account,
      bool_or(tt_seller)                   as tt_seller,
      bool_or(commerce_user)               as commerce_user,
      max(commerce_category)               as commerce_category,
      max(search_query)                    as search_query,
      max(search_hashtag)                  as search_hashtag,
      max(posted_at)                       as last_post_at,
      count(*) filter (where posted_at >= now() - interval '30 days')::int as posts_30d,
      sum(play_count)                      as play_total,
      sum(digg_count + comment_count + share_count) as eng_total
    from base
    where handle is not null
    group by handle
  )
  insert into public.creators as c (
    handle, nickname, platform, profile_url, fans, engagement_pct, posts_30d,
    last_post_at, bio, bio_link, bio_domain, email,
    tt_seller, commerce_user, commerce_category, private_account, verified,
    vitrine, score_afiliado, trilha,
    search_query, search_hashtag, status
  )
  select
    a.handle, a.nickname, 'TikTok', 'https://tiktok.com/@'||a.handle,
    a.fans,
    case when a.play_total > 0 then round(a.eng_total / a.play_total * 100, 2) else 0 end,
    a.posts_30d, a.last_post_at, a.bio, a.bio_link,
    public.extrair_dominio(a.bio_link),
    public.extrair_email(a.bio),
    a.tt_seller, a.commerce_user, a.commerce_category, a.private_account, a.verified,
    public.derivar_vitrine(public.extrair_dominio(a.bio_link)),
    public.calcular_score(a.handle, a.bio, public.extrair_dominio(a.bio_link),
                          a.tt_seller, a.commerce_user),
    public.derivar_trilha(coalesce(a.search_query, a.search_hashtag)),
    a.search_query, a.search_hashtag, 'pool'
  from agg a
  on conflict (handle) do update set
    nickname       = coalesce(excluded.nickname, c.nickname),
    fans           = coalesce(excluded.fans, c.fans),
    engagement_pct = excluded.engagement_pct,
    posts_30d      = excluded.posts_30d,
    last_post_at   = greatest(coalesce(c.last_post_at, excluded.last_post_at), excluded.last_post_at),
    bio            = coalesce(excluded.bio, c.bio),
    bio_link       = coalesce(excluded.bio_link, c.bio_link),
    bio_domain     = coalesce(excluded.bio_domain, c.bio_domain),
    email          = coalesce(c.email, excluded.email),
    tt_seller      = coalesce(excluded.tt_seller, c.tt_seller),
    commerce_user  = coalesce(excluded.commerce_user, c.commerce_user),
    vitrine        = excluded.vitrine,
    score_afiliado = excluded.score_afiliado,
    last_seen_at   = now(),
    run_count      = c.run_count + 1,
    -- nunca reverter quem ja foi para o GHL
    status         = case when c.status = 'no_ghl' then 'no_ghl' else 'pool' end;

  select count(*) - v_antes into v_novos from public.creators;

  -- 2) videos
  with itens as (select i from jsonb_array_elements(p_items) i)
  insert into public.creator_videos (
    video_url, handle, posted_at, play_count, digg_count, comment_count,
    share_count, caption, hashtags, search_query
  )
  select
    i->>'webVideoUrl',
    i->'authorMeta'->>'name',
    nullif(i->>'createTimeISO','')::timestamptz,
    (i->>'playCount')::bigint,
    (i->>'diggCount')::bigint,
    (i->>'commentCount')::bigint,
    (i->>'shareCount')::bigint,
    i->>'text',
    (select array_agg(h->>'name') from jsonb_array_elements(coalesce(i->'hashtags','[]'::jsonb)) h),
    i->>'searchQuery'
  from itens
  where i->>'webVideoUrl' is not null
    and i->'authorMeta'->>'name' is not null
  on conflict (video_url) do nothing;

  v_videos := (select count(*) from public.creator_videos
               where collected_at > now() - interval '2 minutes');

  -- 3) roteia
  perform public.rotear_criadores();

  -- 4) log
  insert into public.apify_runs (run_id, dataset_id, status, items_recebidos,
                                 criadores_novos, videos_novos, processed_at)
  values (p_run_id, p_dataset_id, 'processado', v_itens, v_novos, v_videos, now())
  on conflict (run_id) do update set
    items_recebidos = excluded.items_recebidos,
    criadores_novos = excluded.criadores_novos,
    videos_novos    = excluded.videos_novos,
    processed_at    = now(),
    status          = 'processado';

  select jsonb_build_object(
    'run_id', p_run_id,
    'itens_recebidos', v_itens,
    'criadores_novos', v_novos,
    'videos_novos', v_videos,
    'roteamento', (select jsonb_object_agg(status, qtd) from
       (select status, count(*) qtd from public.creators group by status) t)
  ) into v_result;

  return v_result;
end $$;

revoke all on function public.ingest_apify_items(text,text,jsonb) from anon, authenticated;
