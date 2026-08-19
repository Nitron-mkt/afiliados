-- As views nasceram como SECURITY DEFINER, o que faria elas ignorarem o RLS
-- das tabelas e expor dado pessoal via Data API. Recriando como INVOKER.
drop view if exists public.fila_dm;
drop view if exists public.fila_ghl;

create view public.fila_dm with (security_invoker = true) as
  select handle, nickname, fans, engagement_pct, last_post_at,
         profile_url, bio_link, vitrine, trilha, kit_alocado, score_afiliado
  from public.creators
  where status = 'fila_dm'
  order by score_afiliado desc nulls last, engagement_pct desc nulls last
  limit 30;

create view public.fila_ghl with (security_invoker = true) as
  select handle, nickname, email, fans, engagement_pct, posts_30d,
         profile_url, vitrine, trilha, kit_alocado, marca_alocada,
         comissao_pct, tema_do_video, tema_revisado, score_afiliado,
         search_query, platform
  from public.creators
  where status = 'apto_email'
  order by score_afiliado desc nulls last, fans desc nulls last;

-- search_path fixo evita sequestro de funcao por schema malicioso
create or replace function public.touch_updated_at()
returns trigger language plpgsql
set search_path = public, pg_temp
as $$
begin
  new.updated_at = now();
  return new;
end $$;

create or replace function public.rotear_criadores(
  min_fans        integer default 3000,
  min_engajamento numeric default 1.5,
  max_dias_inativo integer default 45
)
returns table (destino text, quantidade bigint)
language plpgsql
set search_path = public, pg_temp
as $$
begin
  update public.creators c set
    status = case
      when c.private_account is true                                   then 'descartado'
      when coalesce(c.score_afiliado, 0) < 0                           then 'descartado'
      when coalesce(c.fans, 0) < min_fans                              then 'descartado'
      when coalesce(c.engagement_pct, 0) < min_engajamento             then 'descartado'
      when c.last_post_at is null
        or c.last_post_at < now() - (max_dias_inativo || ' days')::interval then 'descartado'
      when c.email is not null and c.email <> ''                       then 'apto_email'
      else 'fila_dm'
    end,
    descarte_motivo = case
      when c.private_account is true                                   then 'Perfil privado'
      when coalesce(c.score_afiliado, 0) < 0                           then 'E marca ou seller'
      when coalesce(c.fans, 0) < min_fans                              then 'Audiencia pequena'
      when coalesce(c.engagement_pct, 0) < min_engajamento             then 'Engajamento baixo'
      when c.last_post_at is null
        or c.last_post_at < now() - (max_dias_inativo || ' days')::interval then 'Inativo'
      else null
    end
  where c.status = 'pool';

  return query
    select cr.status, count(*) from public.creators cr
    where cr.updated_at > now() - interval '1 minute'
    group by cr.status;
end $$;

-- Nao expor a funcao de roteamento pela API publica
revoke all on function public.rotear_criadores(integer, numeric, integer) from anon, authenticated;
