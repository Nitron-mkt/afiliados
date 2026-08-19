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

| # | Pendencia | Bloqueia |
|---|---|---|
| 1 | Frete nao medido | publicar o W7: os e-mails prometem comissao sem numero confiavel |
| 2 | Campo `Bairro` nao existe no GHL | W1 e W9 nao validam endereco; Sankhya nao emite nota |
| 3 | Chaves de merge field nao conferidas | `afiliado__marca_alocada`, `bairro`, `afiliado__codigo_de_rastreio` sao deducao |
| 4 | Lista de kits aprovados nao fechada | W1 passo 4 |
| 5 | Sincronizacao Supabase -> GHL e manual | `fila_ghl` existe, o envio nao |
| 6 | GMV nao volta do Sankhya/Shopify | W6 nunca dispara sozinho |
| 7 | Pesos do classificador sem calibracao | qualidade de tudo a jusante |

Pendencia 5 e a que mais custa tempo por dia. Pendencia 1 e a que mais
custa dinheiro se ignorada.

## Sub-conta GHL

Nitron — `rZ8y7lzqV7fzxsartaX2`
