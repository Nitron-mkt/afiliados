-- ============================================================
-- Perna que faltava: Supabase -> GHL.
--
-- Mesmo princípio do resto do projeto: a logica vive em SQL e as
-- configuracoes vivem em tabela. A Edge Function so pega o payload
-- pronto, entrega ao GHL e devolve o resultado. Trocar um id de campo
-- ou um valor de picklist e um update, nao um deploy.
-- ============================================================

-- ------------------------------------------------------------
-- 1) Ids da sub-conta. Levantados pela API em 19/08/2026.
--    Se alguem recriar um campo ou stage no GHL, o id muda: e aqui
--    que se corrige.
-- ------------------------------------------------------------
create table public.ghl_config (
  chave text primary key,
  valor text not null,
  nota  text
);
alter table public.ghl_config enable row level security;

comment on table public.ghl_config is 'Ids do GHL (sub-conta Nitron). Fonte: docs/ghl-inventario.md';

insert into public.ghl_config (chave, valor, nota) values
  ('location_id',        'rZ8y7lzqV7fzxsartaX2', 'Sub-conta Nitron'),
  ('pipeline_jornada',   'EbgtwZHPzdflM2Psu5jw', 'Afiliados Jornada'),
  ('stage_mapeado',      '549a5362-dd4e-497c-a876-ff5bf33d299d', 'entrada de quem tem e-mail'),
  ('stage_key_account',  'e3fc2944-4365-475d-8c12-ff427aa73fa9', 'entrada de key account: nao passa pelo W5 nem pelo W7'),
  ('stage_qualificado',  '63ae5833-7303-4edd-ad72-a2310cee7410', 'quem o W5 promove'),
  ('source_contato',     'Supabase afiliados', 'aparece no campo source do contato');

-- ------------------------------------------------------------
-- 2) De qual coluna do pool sai cada campo customizado do GHL.
--    O id do campo e obrigatorio: a API aceita 'key', mas o schema
--    exige 'id', e id nao depende de ninguem nao renomear o campo.
-- ------------------------------------------------------------
create table public.ghl_campos (
  coluna       text primary key,
  ghl_field_id text not null,
  ghl_key      text not null,
  ativo        boolean not null default true,
  nota         text
);
alter table public.ghl_campos enable row level security;

comment on table public.ghl_campos is 'Mapa coluna do pool -> campo customizado do GHL. ativo=false deixa de enviar.';
comment on column public.ghl_campos.ativo is 'Desligue para parar de enviar um campo sem mexer em codigo';

insert into public.ghl_campos (coluna, ghl_field_id, ghl_key, ativo, nota) values
  ('platform',       '76ohuJZvTcRbHN8LnGRi', 'afiliado__plataforma_principal', true,  null),
  ('handle',         'UBfJdvWxRHBPTp4jdaON', 'afiliado__handle_principal',     true,  'enviado com @ na frente'),
  ('profile_url',    'aGtcG8QlLJf5tWDw3F6x', 'afiliado__url_do_perfil',        true,  null),
  ('fans',           'm5IjXrMQjZtULYcbbzUP', 'afiliado__seguidores',           true,  null),
  ('engagement_pct', 'EFA1oBYuWb3nIk5Q3FeM', 'afiliado__engajamento_',         true,  null),
  ('posts_30d',      'KkwE2mW1Mimvs0bGKr1w', 'afiliado__posts_ultimos_30_dias',true,  null),
  ('vitrine',        '0eVAv3v98X2YRhkaeeTh', 'afiliado__vitrine',              true,  'passa por ghl_mapa_valores'),
  ('trilha',         'dj7l8lVTMAEK1SkeK6jD', 'afiliado__trilha',               true,  null),
  ('tema_do_video',  'ir6DY9ZwuWUgaGXi68K7', 'afiliado__tema_do_video',        true,  'quase sempre vazio hoje'),
  ('kit_alocado',    'X85LQ2NJm7A8ZpjUGLIo', 'afiliado__kit_alocado',          true,  'null em 100% do pool: nada aloca kit ainda'),
  ('marca_alocada',  'qcvIg5mpVpgqUn5yQhRh', 'afiliado__marca_alocada',        true,  'null em 100% do pool'),
  ('comissao_pct',   '5xcgwYOjZqreTjypVrtD', 'afiliado__comissao_',            true,  'null enquanto o frete nao estiver medido'),
  ('fonte_captacao', 'Y7Eq4RQgUwvVGbmfl0To', 'afiliado__fonte_de_captacao',    true,  'valor fixo Curadoria'),
  ('score_afiliado', 'l5WfXFGmqxC2fgyeMGPD', 'afiliado__score',               false, 'DESLIGADO: campo do GHL e 0-100, o score aqui vai de -6 a 8');

-- ------------------------------------------------------------
-- 3) Traducao de valor para picklist do GHL.
--    Valor fora da picklist entra vazio, sem erro e sem aviso — e a
--    causa numero um de condicao que nunca casa. O rotulo interno
--    continua o que e; a traducao acontece so na saida.
-- ------------------------------------------------------------
create table public.ghl_mapa_valores (
  coluna text not null,
  de     text not null,
  para   text not null,
  primary key (coluna, de)
);
alter table public.ghl_mapa_valores enable row level security;

comment on table public.ghl_mapa_valores is 'Traducao de valor do pool para a picklist do GHL. Sem entrada aqui, o valor segue igual.';

insert into public.ghl_mapa_valores (coluna, de, para) values
  ('vitrine', 'collshp.com',   'collshp.com (Shopee)'),
  ('vitrine', 'Shopee direto', 'collshp.com (Shopee)');

create or replace function public.ghl_valor(p_coluna text, p_valor text)
returns text language sql stable
set search_path = public, pg_temp
as $$
  select coalesce(
    (select m.para from public.ghl_mapa_valores m
      where m.coluna = p_coluna and m.de = p_valor),
    p_valor);
$$;

-- ------------------------------------------------------------
-- 4) Auditoria. Toda tentativa fica registrada, inclusive a que falhou.
-- ------------------------------------------------------------
create table public.ghl_sync_log (
  id                 bigserial primary key,
  handle             text not null,
  acao               text not null,
  ok                 boolean not null,
  ghl_contact_id     text,
  ghl_opportunity_id text,
  http_status        integer,
  erro               text,
  payload_enviado    jsonb,
  at                 timestamptz not null default now()
);
alter table public.ghl_sync_log enable row level security;

create index ghl_sync_log_handle_idx on public.ghl_sync_log (handle, at desc);
create index ghl_sync_log_erro_idx   on public.ghl_sync_log (at desc) where ok = false;

comment on table public.ghl_sync_log is 'Uma linha por tentativa de envio ao GHL. Falha tambem entra.';

-- ------------------------------------------------------------
-- 5) O payload do contato, montado inteiro no banco.
-- ------------------------------------------------------------
create or replace function public.payload_ghl_contato(p_handle text)
returns jsonb language plpgsql stable
set search_path = public, pg_temp
as $$
declare
  c public.creators;
  v_campos jsonb;
begin
  select * into c from public.creators where handle = p_handle;
  if not found then
    raise exception 'handle % nao existe no pool', p_handle;
  end if;

  -- Um objeto por campo ativo que tenha valor. Campo vazio nao e
  -- enviado: mandar string vazia apaga o que ja estava no GHL.
  select jsonb_agg(jsonb_build_object('id', f.ghl_field_id, 'field_value', f.valor))
    into v_campos
  from (
    select g.ghl_field_id,
           public.ghl_valor(g.coluna, v.valor) as valor
    from public.ghl_campos g
    join lateral (
      select case g.coluna
        when 'platform'       then c.platform
        when 'handle'         then '@' || c.handle
        when 'profile_url'    then c.profile_url
        when 'fans'           then c.fans::text
        when 'engagement_pct' then c.engagement_pct::text
        when 'posts_30d'      then c.posts_30d::text
        when 'vitrine'        then c.vitrine
        when 'trilha'         then c.trilha
        when 'tema_do_video'  then c.tema_do_video
        when 'kit_alocado'    then c.kit_alocado
        when 'marca_alocada'  then c.marca_alocada
        when 'comissao_pct'   then c.comissao_pct::text
        when 'fonte_captacao' then 'Curadoria'
        when 'score_afiliado' then c.score_afiliado::text
      end as valor
    ) v on true
    where g.ativo
      and v.valor is not null
      and v.valor <> ''
  ) f;

  return jsonb_strip_nulls(jsonb_build_object(
    'locationId', (select valor from public.ghl_config where chave = 'location_id'),
    'firstName',  coalesce(nullif(c.nickname,''), c.handle),
    'email',      c.email,
    'website',    c.bio_link,
    'source',     (select valor from public.ghl_config where chave = 'source_contato'),
    'customFields', coalesce(v_campos, '[]'::jsonb)
  ));
end $$;

comment on function public.payload_ghl_contato is 'Corpo do POST /contacts/upsert. Nao inclui tags: tags vao por endpoint separado, senao o upsert sobrescreve as que o contato ja tem.';

-- ------------------------------------------------------------
-- 6) A fila de envio.
--
--    Inclui key_account, que o guia W0-W9 nao previa. Key account entra
--    direto no stage Key Account: nao passa pelo Mapeado, entao nao
--    dispara o W5 nem cai na sequencia de e-mail do W7. Negociacao com
--    cache e conversa de pessoa.
-- ------------------------------------------------------------
create or replace view public.fila_sync_ghl with (security_invoker = true) as
  select
    c.handle,
    c.status,
    c.nickname,
    c.email,
    c.fans,
    c.score_afiliado,
    c.trilha,
    case when c.status = 'key_account'
      then (select valor from public.ghl_config where chave = 'stage_key_account')
      else (select valor from public.ghl_config where chave = 'stage_mapeado')
    end as stage_id,
    '@' || c.handle || ' - ' || coalesce(c.fans::text, 's/ dado') as opportunity_name,
    public.payload_ghl_contato(c.handle) as payload
  from public.creators c
  where c.status in ('apto_email','key_account')
    and c.ghl_contact_id is null
  order by
    case when c.status = 'key_account' then 0 else 1 end,
    c.score_afiliado desc nulls last,
    c.fans desc nulls last;

comment on view public.fila_sync_ghl is 'Criadores prontos para o GHL e ainda nao enviados, com payload montado.';

-- ------------------------------------------------------------
-- 7) Fechamento do ciclo.
-- ------------------------------------------------------------
create or replace function public.marcar_sincronizado(
  p_handle         text,
  p_contact_id     text,
  p_opportunity_id text default null,
  p_payload        jsonb default null
) returns void language plpgsql
set search_path = public, pg_temp
as $$
begin
  update public.creators set
    ghl_contact_id     = p_contact_id,
    ghl_opportunity_id = coalesce(p_opportunity_id, ghl_opportunity_id),
    synced_at          = now(),
    status             = 'no_ghl'
  where handle = p_handle;

  if not found then
    raise exception 'handle % nao existe no pool', p_handle;
  end if;

  insert into public.ghl_sync_log (handle, acao, ok, ghl_contact_id,
                                   ghl_opportunity_id, payload_enviado)
  values (p_handle, 'sync', true, p_contact_id, p_opportunity_id, p_payload);
end $$;

comment on function public.marcar_sincronizado is 'Grava os ids do GHL, move para no_ghl e registra no log. Chamado pela Edge Function apos sucesso.';

create or replace function public.registrar_falha_sync(
  p_handle  text,
  p_acao    text,
  p_status  integer,
  p_erro    text,
  p_payload jsonb default null
) returns void language plpgsql
set search_path = public, pg_temp
as $$
begin
  insert into public.ghl_sync_log (handle, acao, ok, http_status, erro, payload_enviado)
  values (p_handle, p_acao, false, p_status, p_erro, p_payload);
end $$;

-- O status no_ghl e final para o ingest (ele nunca reverte), mas se um
-- contato for apagado no GHL a mao, isto devolve o criador para a fila.
create or replace function public.resetar_sync(p_handle text)
returns void language plpgsql
set search_path = public, pg_temp
as $$
begin
  update public.creators set
    ghl_contact_id = null, ghl_opportunity_id = null, synced_at = null,
    status = case when public.tem_sinal_agencia(email, bio_domain)
                   or coalesce(fans,0) >= 500000 then 'key_account'
                  else 'apto_email' end
  where handle = p_handle;
end $$;

comment on function public.resetar_sync is 'Devolve um criador para a fila de envio. Use se o contato foi apagado no GHL a mao.';

-- ------------------------------------------------------------
-- 8) Nada disso e exposto pela API publica.
-- ------------------------------------------------------------
revoke all on function public.ghl_valor(text,text)                          from anon, authenticated;
revoke all on function public.payload_ghl_contato(text)                     from anon, authenticated;
revoke all on function public.marcar_sincronizado(text,text,text,jsonb)     from anon, authenticated;
revoke all on function public.registrar_falha_sync(text,text,integer,text,jsonb) from anon, authenticated;
revoke all on function public.resetar_sync(text)                            from anon, authenticated;
