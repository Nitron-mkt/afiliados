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
      ├── fila_sync_ghl     -> Edge Function ghl-sync -> contato + tags + card
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
| `docs/ghl-inventario.md` | ids reais de campos, stages e workflows do GHL, e as divergencias |
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

## Edge Functions

| Slug | O que faz | Secret que precisa |
|---|---|---|
| `apify-ingest` | recebe o webhook do Apify e entrega ao Postgres | `APIFY_TOKEN` |
| `ghl-sync` | leva a fila aprovada para o GHL: contato, tags e card | `GHL_API_TOKEN` |

`SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` sao injetados pelo runtime.

```bash
supabase functions deploy ghl-sync --project-ref rztvbnvwigtfegqsrtew
supabase secrets set GHL_API_TOKEN=... --project-ref rztvbnvwigtfegqsrtew
```

### Rodando o sync

O `dry_run` e **true por padrao** — sem `{"dry_run": false}` nada e escrito
no GHL. Antes do primeiro envio real, leia o aviso sobre o W7 em
`docs/arquitetura.md`.

```bash
# ensaio: mostra o payload exato de cada criador, sem escrever nada
curl -X POST "$SUPABASE_URL/functions/v1/ghl-sync" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"limite": 3}'

# de verdade, dois criadores escolhidos a mao
curl -X POST "$SUPABASE_URL/functions/v1/ghl-sync" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false, "handles": ["handle1", "handle2"]}'
```

O que o sync le e escreve, tudo editavel por SQL sem novo deploy:

| Tabela | Para que |
|---|---|
| `ghl_config` | ids de location, pipeline e stages |
| `ghl_campos` | de qual coluna do pool sai cada campo do GHL. `ativo=false` para de enviar |
| `ghl_mapa_valores` | traduz valor do pool para a picklist do GHL |
| `ghl_sync_log` | uma linha por tentativa, inclusive as que falharam |

```sql
-- o que falhou e por que
select handle, acao, http_status, erro, at
from ghl_sync_log where not ok order by at desc;

-- devolver um criador para a fila (contato apagado no GHL a mao)
select resetar_sync('handle');
```
