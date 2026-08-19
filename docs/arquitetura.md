# Arquitetura, decisoes e pendencias

## Divisao de responsabilidade

| Camada | Responsavel | Por que aqui |
|---|---|---|
| Raspagem | Apify | ja funciona, paga por uso |
| Ingestao e deduplicacao | Edge Function + `ingest_apify_items` | a funcao SQL faz tudo em uma transacao |
| Classificacao e score | Postgres, pesos em tabela | ajustar peso e um `update`, nao um deploy |
| Roteamento | `rotear_criadores()` | decide apto_email, fila_dm, key_account, descartado |
| Jornada do criador | GoHighLevel | pipeline, e-mail, WhatsApp, amostra |
| Nota fiscal e estoque | Sankhya | fora deste repo |

O principio: **o Supabase decide quem entra, o GHL conduz quem entrou.**
Enquanto essa fronteira estiver clara, os dois lados evoluem sem se atropelar.

## Decisoes que valem registro

**Pesos do classificador em tabela, nao em codigo.**
`classificador_pesos` e `classificador_listas` sao editaveis por SQL. Os pesos
nunca foram calibrados contra verdade observada: sao estimativa informada. Sem
revisao manual das primeiras dezenas, o score e um chute com casas decimais.

**`marca_alocada` deriva do kit, nunca do nicho.**
O kit e o que vai na nota fiscal. Derivar do nicho gera nota errada no Sankhya.

**Sinal de agencia e positivo, nao negativo.**
Um criador com e-mail de assessoria e profissional, nao ruido. Mas ele nao
recebe o e-mail automatico de comissao: vira `key_account`, trilha
`Key account`, e o W7 desvia.

**Dominio proprio penaliza (-3), exceto se for agencia.**
Quem tem site proprio normalmente e marca concorrente, nao afiliado.

**Fila de DM limitada a 30.**
Fila infinita nao e trabalhada. 30 e o que uma pessoa faz em duas horas.

## Colisoes entre workflows do GHL

Tres pontos onde um workflow dispara outro sem ninguem mandar. Estao detalhadas
em `ghl-workflows-w0-w9.md`, secao COLISOES. Resumo:

1. Devolver card para `Amostra solicitada` faz o W1 reenviar amostra sozinho
   para o endereco que acabou de falhar. Correcao: W2b devolve para `Aceito`.
2. Devolver para `Aceito` faz o W4 mover o card para `Recorrente`.
   Correcao: tag `afil-devolvido`, checada e limpa no passo 1 do W4.
3. `Stop on Response` no W3 tira o criador da cobranca sem preencher
   `URL do video` — ele nunca e cobrado nem bloqueado.
   Correcao: tag manual `afil-conteudo-combinado`, `Stop on Response` desligado.

A ordem de construcao importa: **W4 antes do W2b**. Publicar o W2b sem a trava
do W4 manda a primeira amostra extraviada para `Recorrente`.

## Pendencias reais

Revisado em 19/08/2026 contra o estado real do GHL — ver `ghl-inventario.md`.

| # | Pendencia | Bloqueia | Estado |
|---|---|---|---|
| 1 | **W7 esta publicado com frete nao medido** | nenhum e-mail saiu ainda (0 contatos entraram, pipeline vazio), mas dispara no primeiro sync real | aberta |
| 2 | Campo `Bairro` nao existe no GHL | W1 e W9 nao validam endereco; Sankhya nao emite nota | aberta, confirmada |
| 3 | Chaves de merge field | `afiliado__marca_alocada` e `afiliado__codigo_de_rastreio` **confirmadas**; `bairro` nao existe | resolvida em 2 de 3 |
| 4 | Lista de kits aprovados nao fechada | W1 passo 4 | aberta |
| 5 | Sincronizacao Supabase -> GHL | — | **feita e testada com write real**: `ghl-sync` |
| 6 | GMV nao volta do Sankhya/Shopify | W6 nunca dispara sozinho | aberta |
| 7 | Pesos do classificador sem calibracao | qualidade de tudo a jusante | aberta |
| 8 | **W0 nao existe** e a tag `afil-import` nao existe | a porta de entrada da importacao | contornada pelo `ghl-sync` |
| 9 | **W4 nao existe** | a trava de reenvio | aberta, ver aviso abaixo |
| 10 | **Nada aloca kit nem marca** | `kit_alocado` e `marca_alocada` sao null nos 97 criadores. Sem marca o W9 aplica `afil-sem-marca` e o W1 barra a amostra | aberta |
| 11 | Cinco tags do guia nao existem no GHL | `afil-devolvido` `afil-conteudo-combinado` `afil-revendedor` `afil-cadastro-incompleto` `afil-teste`. A `afil-import` passou a existir no teste do sync | aberta |

Nenhuma pendencia esta causando dano agora: o pipeline de afiliados esta
vazio, entao nenhum workflow chegou a agir sobre um afiliado de verdade. As
travas que ja existem foram verificadas e funcionam — ver a secao do W2 em
`ghl-inventario.md`.

Pendencia 1 e a que cria dano no minuto do primeiro sync real.
Pendencia 10 e a que trava a jornada no meio, depois do aceite.
Pendencia 9 e a que cria dano na primeira amostra extraviada.

**Aviso sobre o W4:** o guia manda construir o W4 antes do W2b. Hoje o W2b
esta publicado e o W4 nao existe — por acaso, seguro. O risco aparece no
minuto em que o W4 nascer: ele precisa ja vir com o passo 1 que checa e limpa
`afil-devolvido`, ou a Colisao 2 acontece na primeira amostra extraviada.

## Como o `ghl-sync` se encaixa

Ele faz o que o W0 faria, e um pouco mais, do lado do Supabase:

1. Le `fila_sync_ghl` — quem esta em `apto_email` ou `key_account` e ainda
   nao tem `ghl_contact_id`
2. `POST /contacts/upsert` com o payload montado por `payload_ghl_contato()`
3. `POST /contacts/{id}/tags` — separado de proposito: o campo `tags` do
   upsert **substitui** todas as tags do contato, e o criador pode ja existir
   na base como cliente B2B
4. `POST /opportunities/upsert` — card em `Mapeado`, ou em `Key Account` se
   o roteamento marcou key account
5. `marcar_sincronizado()` — grava os ids, move para `no_ghl`, registra em
   `ghl_sync_log`

Falha em qualquer passo entra em `ghl_sync_log` e **nao** marca como
sincronizado: a rodada seguinte tenta de novo, e o upsert nao duplica.

**`dry_run` e true por padrao.** Sem `{"dry_run": false}` explicito nada e
escrito. Isso existe por causa de uma cadeia: card em `Mapeado` dispara o W5,
que promove para `Qualificado`, que dispara o W7 — que esta publicado. Ou
seja, hoje sincronizar de verdade **manda e-mail prometendo comissao**.
Key account nao tem esse problema: entra direto no stage `Key Account`, que
nao e trigger de nada.

Por que o sync cria o card em vez de deixar o W0 fazer: o W0 nao existe, e a
trava de revendedor que ele faria (CNPJ, Codigo Representante) o W5 ja repete
como rede de seguranca. Se um dia o W0 for construido, ele usa
`Create/Update Opportunity` — atualiza o card em vez de duplicar.

## Sub-conta GHL

Nitron — `rZ8y7lzqV7fzxsartaX2`
