-- ============================================================
-- Tabela de pesos do classificador. Editavel sem mexer em codigo.
-- Os pesos NAO foram calibrados com verdade: sao estimativa informada.
-- Revisar manualmente os primeiros resultados e ajustar aqui.
-- ============================================================
create table public.classificador_pesos (
  chave     text primary key,
  peso      integer not null,
  categoria text not null check (categoria in ('positivo','negativo')),
  nota      text
);

alter table public.classificador_pesos enable row level security;

insert into public.classificador_pesos (chave, peso, categoria, nota) values
  ('vitrine_afiliado',   4, 'positivo', 'collshp.com e similares. Sinal mais forte que existe'),
  ('bio_palavra',        1, 'positivo', 'Por palavra encontrada, ate 3 pontos'),
  ('handle_afiliado',    2, 'positivo', 'achadinho, achados, indica, comprinha, promo'),
  ('agregador_link',     1, 'positivo', 'linktr.ee, bio.site. Sinal fraco'),
  ('dominio_proprio',   -3, 'negativo', 'Quem tem site proprio e marca, nao afiliado'),
  ('handle_marca',      -3, 'negativo', 'oficial, loja, moveis, artefatos, fabrica'),
  ('tt_seller',         -2, 'negativo', 'Vende os produtos dele: concorrente'),
  ('bio_comercial',     -2, 'negativo', 'CNPJ, orcamento, atacado, frete'),
  ('commerce_user',     -1, 'negativo', 'Conta comercial');

-- Listas de referencia, tambem editaveis
create table public.classificador_listas (
  tipo  text not null check (tipo in ('vitrine','agregador','bio_positiva','bio_negativa','handle_positivo','handle_negativo')),
  termo text not null,
  rotulo text,
  primary key (tipo, termo)
);

alter table public.classificador_listas enable row level security;

insert into public.classificador_listas (tipo, termo, rotulo) values
  ('vitrine','collshp.com','collshp.com'),
  ('vitrine','mycollection.shop','mycollection.shop'),
  ('vitrine','tipfy.pro','tipfy.pro'),
  ('vitrine','shopee.com.br','Shopee direto'),
  ('vitrine','shope.ee','Shopee direto'),
  ('vitrine','mercadolivre','Mercado Livre'),
  ('vitrine','amzn.to','Amazon'),
  ('vitrine','amazon','Amazon'),
  ('agregador','linktr.ee',null),
  ('agregador','lnk.bio',null),
  ('agregador','bio.site',null),
  ('agregador','beacons.ai',null),
  ('agregador','linkbio.co',null),
  ('agregador','stan.store',null),
  ('agregador','msha.ke',null),
  ('bio_positiva','achadinho',null),
  ('bio_positiva','achados',null),
  ('bio_positiva','comprinha',null),
  ('bio_positiva','link na bio',null),
  ('bio_positiva','links dos video',null),
  ('bio_positiva','link do produto',null),
  ('bio_positiva','todos os links',null),
  ('bio_positiva','cupom',null),
  ('bio_positiva','desconto',null),
  ('bio_positiva','recebido',null),
  ('bio_positiva','indico',null),
  ('bio_positiva','promoc',null),
  ('bio_positiva','vitrine',null),
  ('bio_negativa','cnpj',null),
  ('bio_negativa','atendimento',null),
  ('bio_negativa','orcamento',null),
  ('bio_negativa','loja fisica',null),
  ('bio_negativa','atacado',null),
  ('bio_negativa','revenda',null),
  ('bio_negativa','sob medida',null),
  ('bio_negativa','encomenda',null),
  ('bio_negativa','showroom',null),
  ('bio_negativa','fabricamos',null),
  ('handle_positivo','achadinho',null),
  ('handle_positivo','achados',null),
  ('handle_positivo','indica',null),
  ('handle_positivo','comprinha',null),
  ('handle_positivo','promo',null),
  ('handle_positivo','desconto',null),
  ('handle_negativo','oficial',null),
  ('handle_negativo','artefatos',null),
  ('handle_negativo','moveis',null),
  ('handle_negativo','marcenaria',null),
  ('handle_negativo','fabrica',null),
  ('handle_negativo','industria',null),
  ('handle_negativo','atacado',null),
  ('handle_negativo','distribuidora',null);

-- ============================================================
-- Helpers
-- ============================================================
create or replace function public.sem_acento(txt text)
returns text language sql immutable
set search_path = public, pg_temp
as $$
  select lower(translate(coalesce(txt,''),
    'áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ',
    'aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC'));
$$;

create or replace function public.extrair_email(bio text)
returns text language sql immutable
set search_path = public, pg_temp
as $$
  select (regexp_match(coalesce(bio,''),
    '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'))[1];
$$;

create or replace function public.extrair_dominio(url text)
returns text language sql immutable
set search_path = public, pg_temp
as $$
  select nullif(regexp_replace(
    regexp_replace(lower(coalesce(url,'')), '^https?://', ''),
    '^www\.|/.*$', '', 'g'), '');
$$;

create or replace function public.derivar_vitrine(dominio text)
returns text language sql stable
set search_path = public, pg_temp
as $$
  select coalesce(
    (select coalesce(l.rotulo, l.termo) from public.classificador_listas l
      where l.tipo = 'vitrine' and coalesce(dominio,'') like '%'||l.termo||'%' limit 1),
    case when coalesce(dominio,'') = '' then 'Nenhuma' else 'Site proprio' end);
$$;

-- ============================================================
-- Score de afiliado
-- ============================================================
create or replace function public.calcular_score(
  p_handle text, p_bio text, p_dominio text,
  p_tt_seller boolean, p_commerce_user boolean
) returns integer language plpgsql stable
set search_path = public, pg_temp
as $$
declare
  h text := public.sem_acento(p_handle);
  b text := public.sem_acento(p_bio);
  d text := coalesce(lower(p_dominio),'');
  s integer := 0;
  n integer;
  function_peso integer;
begin
  -- vitrine de afiliado
  if exists (select 1 from public.classificador_listas
             where tipo='vitrine' and d like '%'||termo||'%') then
    s := s + (select peso from public.classificador_pesos where chave='vitrine_afiliado');
  -- dominio proprio (nao e vitrine nem agregador)
  elsif d <> '' and not exists (select 1 from public.classificador_listas
             where tipo='agregador' and d like '%'||termo||'%') then
    s := s + (select peso from public.classificador_pesos where chave='dominio_proprio');
  end if;

  -- agregador
  if exists (select 1 from public.classificador_listas
             where tipo='agregador' and d like '%'||termo||'%') then
    s := s + (select peso from public.classificador_pesos where chave='agregador_link');
  end if;

  -- palavras na bio (positivas, teto 3)
  select count(*) into n from public.classificador_listas
    where tipo='bio_positiva' and b like '%'||termo||'%';
  if n > 0 then
    s := s + least(n, 3) * (select peso from public.classificador_pesos where chave='bio_palavra');
  end if;

  -- palavras comerciais na bio
  if exists (select 1 from public.classificador_listas
             where tipo='bio_negativa' and b like '%'||termo||'%') then
    s := s + (select peso from public.classificador_pesos where chave='bio_comercial');
  end if;

  -- handle
  if exists (select 1 from public.classificador_listas
             where tipo='handle_positivo' and h like '%'||termo||'%') then
    s := s + (select peso from public.classificador_pesos where chave='handle_afiliado');
  end if;
  if exists (select 1 from public.classificador_listas
             where tipo='handle_negativo' and h like '%'||termo||'%') then
    s := s + (select peso from public.classificador_pesos where chave='handle_marca');
  end if;

  if p_tt_seller is true then
    s := s + (select peso from public.classificador_pesos where chave='tt_seller');
  end if;
  if p_commerce_user is true then
    s := s + (select peso from public.classificador_pesos where chave='commerce_user');
  end if;

  return s;
end $$;

-- ============================================================
-- Trilha a partir do termo de busca
-- ============================================================
create table public.trilha_mapa (
  padrao text primary key,
  trilha text not null
);
alter table public.trilha_mapa enable row level security;

insert into public.trilha_mapa (padrao, trilha) values
  ('achadinho',   'Achadinhos'),
  ('comprinha',   'Achadinhos'),
  ('mobiliando',  'Mudanca casa nova'),
  ('apartamento', 'Mudanca casa nova'),
  ('enxoval',     'Mudanca casa nova'),
  ('casa nova',   'Mudanca casa nova'),
  ('mudanca',     'Mudanca casa nova'),
  ('mesa posta',  'Curadoria teca'),
  ('madeira',     'Curadoria teca'),
  ('tabua',       'Curadoria teca'),
  ('churrasco',   'Curadoria teca'),
  ('organiz',     'Nicho organizacao'),
  ('cozinha',     'Nicho organizacao'),
  ('geladeira',   'Nicho organizacao'),
  ('limpeza',     'Nicho organizacao'),
  ('donadecasa',  'Nicho organizacao');

create or replace function public.derivar_trilha(p_query text)
returns text language sql stable
set search_path = public, pg_temp
as $$
  select coalesce(
    (select t.trilha from public.trilha_mapa t
      where public.sem_acento(p_query) like '%'||t.padrao||'%' limit 1),
    'Nicho organizacao');
$$;

revoke all on function public.calcular_score(text,text,text,boolean,boolean) from anon, authenticated;
revoke all on function public.derivar_trilha(text) from anon, authenticated;
revoke all on function public.derivar_vitrine(text) from anon, authenticated;
