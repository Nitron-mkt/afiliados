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

**O kit e escolhido pelo criador no formulario. O pool nao adivinha.**
Decidido em 19/08/2026. O classificador deriva trilha de uma string de bio —
isso serve para triagem, nao para decidir o que vai dentro de uma caixa com
frete pago. Quem conhece a audiencia e o criador.

A cadeia fica:

```
criador escolhe o kit no formulario  (lista aprovada no frete)
        v
marca deriva do kit                  (tabela fixa, nao inferencia)
        v
W1 passo 3 e 4 passam
```

Tres consequencias:

1. **Nao existe tabela `trilha -> kit` no Supabase, e nao deve existir.**
   Seria uma camada de adivinhacao no meio do caminho.
2. **`kit_alocado` e `marca_alocada` estao com `ativo = false` em
   `ghl_campos`**, para o sync nunca competir com o que o criador escolheu.
3. **A marca nunca foi problema de inferencia.** `Juta Oval` *e* produto Teak
   Brazil: isso e dado. O W9 deriva com um `If/Else` por kit, no mesmo formato
   do passo 5 que ja existe por marca.

O ganho secundario e o que mais importa a jusante: quem escolheu o kit tem
pele no jogo. A taxa de video entregue de quem pediu o produto e outra em
relacao a quem recebeu o que alguem achou que combinava — e e exatamente esse
o problema que o W3 existe para cobrar.

**Requisito que vem com a decisao:** `Afiliado — Kit alocado` esta como TEXT.
Precisa virar `SINGLE_OPTIONS`, senao o `contains` do W1 passo 4 quebra com um
espaco a mais ou uma caixa diferente. E se toda opcao da lista for
margem-segura, a escolha do criador nao pode custar dinheiro — o que transforma
a pendencia do frete: ela deixa de bloquear o sistema e passa a definir so o
conteudo de um dropdown.

**Excecao:** `key_account` normalmente nao preenche formulario. Amostra para
key account e decisao de pessoa, com cache, e o kit e combinado na conversa.

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
| 4 | Lista de kits aprovados nao fechada | agora bloqueia so as opcoes do dropdown do formulario, nao o fluxo | aberta, despriorizada |
| 5 | Sincronizacao Supabase -> GHL | — | **feita e testada com write real**: `ghl-sync` |
| 6 | GMV nao volta do Sankhya/Shopify | W6 nunca dispara sozinho | aberta |
| 7 | Pesos do classificador sem calibracao | qualidade de tudo a jusante | aberta |
| 8 | **W0 nao existe** | a porta de entrada da importacao | contornada pelo `ghl-sync`, que ja cria contato e card |
| 9 | **W4 nao existe** | a trava de reenvio | aberta, ver aviso abaixo |
| 10 | Kit e marca vazios | resolvido por decisao: kit vem do formulario, marca deriva do kit. Falta so o campo virar `SINGLE_OPTIONS` e entrar no formulario | encaminhada |
| 11 | Cinco tags do guia nao existem no GHL | `afil-devolvido` `afil-conteudo-combinado` `afil-revendedor` `afil-cadastro-incompleto` `afil-teste`. A `afil-import` passou a existir no teste do sync | aberta |

Nenhuma pendencia esta causando dano agora: o pipeline de afiliados esta
vazio, entao nenhum workflow chegou a agir sobre um afiliado de verdade. As
travas que ja existem foram verificadas e funcionam — ver a secao do W2 em
`ghl-inventario.md`.

Pendencia 1 e a que cria dano no minuto do primeiro sync real.
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
