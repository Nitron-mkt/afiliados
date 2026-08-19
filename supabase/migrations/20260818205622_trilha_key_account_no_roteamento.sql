-- Quem vai para key_account tambem tem a trilha marcada como 'Key account',
-- para o W7 no GHL desviar do e-mail automatico de comissao.
create or replace function public.rotear_criadores(
  min_fans           integer default 3000,
  min_engajamento    numeric default 1.5,
  limite_key_account integer default 500000
)
returns table (destino text, quantidade bigint)
language plpgsql
set search_path = public, pg_temp
as $$
begin
  update public.creators c set
    status = case
      when c.private_account is true                       then 'descartado'
      when coalesce(c.score_afiliado,0) < 0                then 'descartado'
      when coalesce(c.fans,0) < min_fans                   then 'descartado'
      when coalesce(c.engagement_pct,0) < min_engajamento  then 'descartado'
      when public.tem_sinal_agencia(c.email, c.bio_domain)
        or coalesce(c.fans,0) >= limite_key_account        then 'key_account'
      when c.email is not null and c.email <> ''           then 'apto_email'
      else 'fila_dm'
    end,
    trilha = case
      when (public.tem_sinal_agencia(c.email, c.bio_domain)
            or coalesce(c.fans,0) >= limite_key_account)
        and c.private_account is not true
        and coalesce(c.score_afiliado,0) >= 0
        and coalesce(c.fans,0) >= min_fans
        and coalesce(c.engagement_pct,0) >= min_engajamento then 'Key account'
      else c.trilha
    end,
    descarte_motivo = case
      when c.private_account is true                       then 'Perfil privado'
      when coalesce(c.score_afiliado,0) < 0                then 'E marca ou seller'
      when coalesce(c.fans,0) < min_fans                   then 'Audiencia pequena'
      when coalesce(c.engagement_pct,0) < min_engajamento   then 'Engajamento baixo'
      else null
    end
  where c.status = 'pool';

  return query
    select cr.status, count(*) from public.creators cr
    where cr.updated_at > now() - interval '1 minute'
    group by cr.status;
end $$;

revoke all on function public.rotear_criadores(integer,numeric,integer) from anon, authenticated;

-- aplica nos que ja estao em key_account
update public.creators set trilha = 'Key account' where status = 'key_account';
