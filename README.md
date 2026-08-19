# Afiliados Nitron

Sistema de prospeccao, qualificacao e acompanhamento de criadores afiliados.
Codigo e schema versionados aqui; execucao no Supabase e no GoHighLevel.

## Como as pecas se encaixam

```
Apify (scraper TikTok)
      │  webhook
      ▼
Edge Function  apify-ingest          supabase/functions/apify-ingest/
      │  rpc ingest_apify_items
      ▼
Postgres / Supabase                  supabase/migrations/
   creators · creator_videos · apify_runs
   classificador (pesos + listas editaveis em tabela)
   rotear_criadores()  ->  apto_email · fila_dm · key_account · descartado
      │
      ├── fila_ghl          -> vira contato no GHL com a tag afil-import
      ├── fila_dm           -> DM manual, 30 por dia
      └── fila_key_account  -> negociacao com cache, tratada por pessoa
                    │
                    ▼
GoHighLevel (sub-conta Nitron)        docs/ghl-workflows-w0-w9.md
   W0 .. W9: jornada do card, amostra, cobranca de conteudo, recorrencia
```

## Estrutura do repo

| Caminho | O que e |
|---|---|
| `supabase/migrations/` | schema versionado, espelho fiel do que esta aplicado no projeto |
| `supabase/functions/` | Edge Functions (Deno) |
| `docs/ghl-workflows-w0-w9.md` | guia de execucao dos workflows W0-W9 no GHL, com as tres colisoes conhecidas |
| `docs/arquitetura.md` | decisoes, limites e o que ainda esta pendente |
| `.env.example` | variaveis necessarias. O `.env` real nunca vai para o git |

## Projeto Supabase

| | |
|---|---|
| Nome | `afiliados` |
| Ref | `rztvbnvwigtfegqsrtew` |
| Regiao | `sa-east-1` |
| Postgres | 17 |

RLS ligado em todas as tabelas e **sem policy publica**: so a `service_role`
acessa. Os dados sao pessoais (nome, e-mail, e adiante CPF e endereco).
As views usam `security_invoker = true` para nao furar o RLS.

## Estado dos dados (19/08/2026)

97 criadores no pool, 110 videos, 2 rodadas do Apify registradas.

| Status | Qtd | Fans medio | Engajamento medio |
|---|---|---|---|
| `descartado` | 43 | 56.5k | 4.63% |
| `fila_dm` | 42 | 79.4k | 6.07% |
| `key_account` | 7 | 2.4M | 9.98% |
| `apto_email` | 5 | 29.8k | 10.83% |

Trilhas: Achadinhos 67 · Curadoria teca 23 · Key account 7.

Leitura: a raspagem atual traz muita gente sem e-mail na bio (42 de 97).
A fila de DM e o caminho principal hoje, nao a excecao.

## Rodando as migrations

Elas **ja estao aplicadas** no projeto. Os arquivos aqui existem para poder
recriar o banco do zero e para revisar mudanca antes de aplicar.

Via Supabase CLI (nao precisa de Postgres local, aponta para o projeto):

```bash
supabase link --project-ref rztvbnvwigtfegqsrtew
supabase db push
```

Nova migration: crie o arquivo em `supabase/migrations/` com timestamp UTC
`YYYYMMDDHHMMSS_descricao.sql`, aplique, e comite junto. Arquivo e banco
devem contar a mesma historia.

## Deploy da Edge Function

```bash
supabase functions deploy apify-ingest --project-ref rztvbnvwigtfegqsrtew
```

Secrets necessarios no projeto: `APIFY_TOKEN`.
`SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` sao injetados pelo runtime.
