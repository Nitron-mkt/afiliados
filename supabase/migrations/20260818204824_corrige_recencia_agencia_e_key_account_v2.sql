drop function if exists public.rotear_criadores(integer,numeric,integer);
drop function if exists public.calcular_score(text,text,text,boolean,boolean);

-- 1) novo status
alter table public.creators drop constraint creators_status_check;
alter table public.creators add constraint creators_status_check
  check (status in ('pool','apto_email','no_ghl','fila_dm','key_account','descartado'));

-- 2) termos de agencia como sinal POSITIVO
alter table public.classificador_listas drop constraint classificador_listas_tipo_check;
alter table public.classificador_listas add constraint classificador_listas_tipo_check
  check (tipo in ('vitrine','agregador','bio_positiva','bio_negativa',
                  'handle_positivo','handle_negativo','agencia'));

insert into public.classificador_listas (tipo, termo, rotulo) values
  ('agencia','agencia',null), ('agencia','assessoria',null),
  ('agencia','colab',null),   ('agencia','talentos',null),
  ('agencia','mgmt',null),    ('agencia','management',null),
  ('agencia','influencer',null), ('agencia','creators',null)
on conflict do nothing;

insert into public.classificador_pesos (chave, peso, categoria, nota) values
  ('agencia_ou_assessoria', 3, 'positivo', 'E-mail ou dominio de agencia. Criador profissional'),
  ('audiencia_massiva',     2, 'positivo', 'Acima do limite de key account')
on conflict (chave) do update set peso = excluded.peso, nota = excluded.nota;

-- 3) detector de agencia
create or replace function public.tem_sinal_agencia(p_email text, p_dominio text)
returns boolean language sql stable
set search_path = public, pg_temp
as $$
  select exists (
    select 1 from public.classificador_listas l
    where l.tipo = 'agencia'
      and (public.sem_acento(coalesce(p_email,''))   like '%'||public.sem_acento(l.termo)||'%'
        or public.sem_acento(coalesce(p_dominio,'')) like '%'||public.sem_acento(l.termo)||'%')
  );
$$;

-- 4) score: dominio de agencia deixa de penalizar
create function public.calcular_score(
  p_handle text, p_bio text, p_dominio text,
  p_tt_seller boolean, p_commerce_user boolean,
  p_email text default null, p_fans integer default null,
  p_limite_key_account integer default 500000
) returns integer language plpgsql stable
set search_path = public, pg_temp
as $$
declare
  h text := public.sem_acento(p_handle);
  b text := public.sem_acento(p_bio);
  d text := coalesce(lower(p_dominio),'');
  s integer := 0;
  n integer;
  eh_agencia boolean := public.tem_sinal_agencia(p_email, p_dominio);
begin
  if eh_agencia then
    s := s + (select peso from public.classificador_pesos where chave='agencia_ou_assessoria');
  end if;

  if exists (select 1 from public.classificador_listas
             where tipo='vitrine' and d like '%'||termo||'%') then
    s := s + (select peso from public.classificador_pesos where chave='vitrine_afiliado');
  elsif d <> '' and not eh_agencia
    and not exists (select 1 from public.classificador_listas
                    where tipo='agregador' and d like '%'||termo||'%') then
    s := s + (select peso from public.classificador_pesos where chave='dominio_proprio');
  end if;

  if exists (select 1 from public.classificador_listas
             where tipo='agregador' and d like '%'||termo||'%') then
    s := s + (select peso from public.classificador_pesos where chave='agregador_link');
  end if;

  select count(*) into n from public.classificador_listas
    where tipo='bio_positiva' and b like '%'||termo||'%';
  if n > 0 then
    s := s + least(n,3) * (select peso from public.classificador_pesos where chave='bio_palavra');
  end if;

  if exists (select 1 from public.classificador_listas
             where tipo='bio_negativa' and b like '%'||termo||'%') then
    s := s + (select peso from public.classificador_pesos where chave='bio_comercial');
  end if;

  if exists (select 1 from public.classificador_listas
             where tipo='handle_positivo' and h like '%'||termo||'%') then
    s := s + (select peso from public.classificador_pesos where chave='handle_afiliado');
  end if;
  if exists (select 1 from public.classificador_listas
             where tipo='handle_negativo' and h like '%'||termo||'%') then
    s := s + (select peso from public.classificador_pesos where chave='handle_marca');
  end if;

  if coalesce(p_fans,0) >= p_limite_key_account then
    s := s + (select peso from public.classificador_pesos where chave='audiencia_massiva');
  end if;

  if p_tt_seller is true then
    s := s + (select peso from public.classificador_pesos where chave='tt_seller');
  end if;
  if p_commerce_user is true then
    s := s + (select peso from public.classificador_pesos where chave='commerce_user');
  end if;

  return s;
end $$;

-- 5) roteamento SEM filtro de recencia
create function public.rotear_criadores(
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
revoke all on function public.tem_sinal_agencia(text,text) from anon, authenticated;
revoke all on function public.calcular_score(text,text,text,boolean,boolean,text,integer,integer) from anon, authenticated;

-- 6) fila manual de key account
create or replace view public.fila_key_account with (security_invoker = true) as
  select handle, nickname, fans, engagement_pct, email, bio_domain, bio_link,
         vitrine, score_afiliado, trilha, kit_alocado, profile_url,
         last_post_at, search_query,
         public.tem_sinal_agencia(email, bio_domain) as tem_agencia
  from public.creators
  where status = 'key_account'
  order by fans desc nulls last;
