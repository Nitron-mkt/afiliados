# Inventario real da sub-conta Nitron

Levantado pela API em 19/08/2026. Sub-conta `rZ8y7lzqV7fzxsartaX2`.

Este arquivo existe para nao adivinhar chave de merge field nem nome de stage.
Tudo aqui foi lido da API, nao deduzido. Reconferir quando alguem mexer no GHL
pela interface.

---

## O que o levantamento mudou

| # | Achado | Impacto |
|---|---|---|
| 1 | **W7 esta `published`** com frete nao medido | arma carregada, **nao** disparada: 0 contatos entraram. Ver a verificacao abaixo |
| 2 | **W0 nao existe** e a tag `afil-import` nao existe | a porta de entrada da importacao nao esta construida |
| 3 | **W4 nao existe** | ver nota de seguranca abaixo |
| 4 | Chaves `afiliado__marca_alocada` e `afiliado__codigo_de_rastreio` **confirmadas** | pendencia 3 do arquitetura.md resolvida em 2 de 3 |
| 5 | **`Bairro` nao existe** na sub-conta | confirma pendencia 2. Nao ha campo equivalente: `Zona` e `Praca` sao de outro contexto |
| 6 | Pipeline tem stage **`Key Account`** que o guia W0-W9 nao menciona | o roteamento do Supabase ja produz `key_account`; ha destino pronto para ele |
| 7 | Picklist de vitrine divergente do que o Supabase grava | 10 registros cairiam em campo vazio |
| 8 | Stages usam **acento**: `Inadimplente de conteúdo`, `Conteúdo publicado` | o guia escreve sem acento; condicao por texto exato nao casaria |

### Nota de seguranca sobre o W4

O guia manda construir o W4 **antes** do W2b, porque o W2b devolve card para
`Aceito` e o W4 dispara nesse stage. Hoje o W2b esta publicado e o W4 nao
existe — o que, por acaso, e seguro: sem W4 ninguem sequestra o card devolvido.

O risco aparece **no minuto em que o W4 for criado**. Ele precisa nascer ja com
o passo 1 (checar e limpar `afil-devolvido`). Criar o W4 sem esse passo, com o
W2b ja no ar, e exatamente a Colisao 2.

---

## Workflows

| Guia | Nome no GHL | ID | Status | Contatos que entraram |
|---|---|---|---|---|
| **W0** | — | — | **nao existe** | — |
| W1 | `W1 Marcação e ponte para logística` | `9936a193-811e-4da8-9bca-d745ad720fb4` | draft | 0 |
| W2 | `W2 Amostra entregue` | `7e9e8642-6515-4d4c-b6b1-cbe7a348f204` | published | **1223** |
| W2b | `W2b Amostra extraviada` | `c23929da-6c9c-4c39-9d98-92bd48793d0e` | published | **23** |
| W3 | `W3 Cobrança de conteúdo` | `fb518d9d-8591-4c83-b9fa-c71dca5e6fc2` | draft | 0 |
| **W4** | — | — | **nao existe** | — |
| W5 | `W5 Exclusão de revendedor` | `10a9877f-5f20-486b-bfd3-4c5df998a07b` | published | 0 |
| **W6** | — | — | nao existe (esperado: e o ultimo da ordem) | — |
| W7 | `W7 Sequência de e-mail` | `826540f2-4f9c-4161-a6d6-e57afa694164` | **published** | 0 |
| W8 | `W8 Resposta detectada` | `00e9d5d1-c9f4-492f-838b-8925baab61ba` | published | 32 |
| W9 | `W9 Formulário recebido` | `d6ff662d-782e-401a-9b71-77a015282a13` | published | 0 |

### A trava do passo 1 do W2 funciona — verificado

Os 1223 do W2 assustam, porque o trigger e `Entregas -> Entregue`, que dispara
em **toda** entrega da empresa, nao so em amostra de afiliado. Se a checagem
de tag do passo 1 nao estivesse no lugar, 1223 clientes teriam recebido
"sua caixa chegou?".

Nao receberam. Tres verificacoes independentes, 19/08/2026:

| Verificacao | Resultado | O que prova |
|---|---|---|
| contatos com a tag `amostra-afiliado` | **0** | a condicao do passo 1 e falsa para todo mundo que entrou |
| cards no pipeline `Afiliados Jornada` | **0** | ninguem chegou ao passo 2, que moveria para `Amostra recebida` |
| WhatsApp e SMS de saida com o texto do W2 | nenhum | o passo 4 nunca rodou |

A tag `afil-devolvido` tambem nao existe na sub-conta, o que confirma o mesmo
para os 23 do W2b: se algum tivesse passado do passo 1, o passo 2 teria criado
a tag.

**O pipeline de afiliados esta vazio: nenhum card, nunca.** Isso explica o 0
do W7 tambem — nada chegou a `Qualificado`, porque nada chegou a lugar nenhum.
O W7 esta publicado e inofensivo *por enquanto*, pela mesma razao. Ele deixa de
ser inofensivo no primeiro `ghl-sync` com `dry_run: false`.

Sobra tambem `New Workflow : 1786716077172` (`2d3a203a-...`, draft, criado
14/08) — parece rascunho abandonado. Vale apagar: o W8 remove contato do W7
por nome, e workflow duplicado e a causa citada no guia para remocao que falha.

Ha um `AfiliadoNitron` (`2d3f541b-...`, published, de marco/2026) anterior a
este projeto. Conferir se nao conflita.

---

## Pipeline `Afiliados Jornada`

`EbgtwZHPzdflM2Psu5jw`

| Pos | Stage | ID |
|---|---|---|
| 0 | Mapeado | `549a5362-dd4e-497c-a876-ff5bf33d299d` |
| 1 | **Key Account** | `e3fc2944-4365-475d-8c12-ff427aa73fa9` |
| 2 | Qualificado | `63ae5833-7303-4edd-ad72-a2310cee7410` |
| 3 | Contatado | `6cdb80f5-a9cc-43ab-9c1d-891267055708` |
| 4 | Respondeu | `b03524d6-b56b-4c38-b051-0d15e2cd3301` |
| 5 | Aceito | `67d1edef-5cd2-477f-8409-1e0a0aaeba2b` |
| 6 | Amostra solicitada | `58d240f3-b658-44ee-934c-6289757d0310` |
| 7 | Amostra recebida | `f3da73d1-ef8f-4fba-bfde-a6b0c60dd6fe` |
| 8 | Convertido | `07eb3c57-a99f-4941-af73-2be0cad29244` |
| 9 | Recorrente | `cb1c8b03-5cf1-462b-bdbc-cb98af2daf96` |
| 10 | Inadimplente de **conteúdo** | `08f79d67-d68b-4822-9d0e-5a61b9e7e654` |
| 11 | **Conteúdo** publicado | `d08d2a4d-083a-4a9e-b5f7-3785d0cca2b8` |

## Outros pipelines usados pela jornada

| Pipeline | ID | Stage relevante | ID do stage |
|---|---|---|---|
| Pedidos-Preparacao | `4DhlIKQogaq9CiIg8ghW` | Pedidos a Liberar | `6efd0b95-e097-4ed2-b8d4-fbad4a054d35` |
| Entregas | `YYykD6oEtzh9jpKYbpGp` | Entregue | `ec822b9b-ac7f-4170-8dfb-0cd163f425f0` |
| Entregas | `YYykD6oEtzh9jpKYbpGp` | Retorno | `ad46f442-7900-44ac-b6ff-fd18fb07b903` |

---

## Campos de afiliado — chaves confirmadas

Todos `model: contact`. Estas chaves foram lidas da API: pode colar sem medo.

| Campo | Chave | Tipo | Picklist |
|---|---|---|---|
| Afiliado — Plataforma principal | `contact.afiliado__plataforma_principal` | SINGLE_OPTIONS | TikTok · Instagram · YouTube · Shopee · Mercado Livre · Kwai · Pinterest |
| Afiliado — Handle principal | `contact.afiliado__handle_principal` | TEXT | |
| Afiliado — URL do perfil | `contact.afiliado__url_do_perfil` | TEXT | |
| Afiliado — Seguidores | `contact.afiliado__seguidores` | NUMERICAL | |
| Afiliado — Engajamento % | `contact.afiliado__engajamento_` | NUMERICAL | |
| Afiliado — Posts ultimos 30 dias | `contact.afiliado__posts_ultimos_30_dias` | NUMERICAL | |
| Afiliado — Vende produto fisico | `contact.afiliado__vende_produto_fisico` | SINGLE_OPTIONS | Sim · Nao · Nao identificado |
| Afiliado na: (vitrine) | `contact.afiliado__vitrine` | SINGLE_OPTIONS | ver divergencia abaixo |
| Afiliado — Trilha | `contact.afiliado__trilha` | SINGLE_OPTIONS | Achadinhos · Mudanca casa nova · Nicho organizacao · Curadoria teca · Key account |
| Afiliado — Marca alocada | `contact.afiliado__marca_alocada` | TEXT | Nitron · Mundo UD · Teak Brazil (sem picklist: quem escreve e o seletor) |
| Afiliado — Kit alocado | `contact.afiliado__kit_alocado` | TEXT | recebe a **referencia** do ERP, ex. `905.K01.999` |
| Afiliado — Comissao % | `contact.afiliado__comissao_` | NUMERICAL | |
| Afiliado — Comissao paga | `contact.afiliado__comissao_paga` | MONETORY | |
| Afiliado — Score | `contact.afiliado__score` | NUMERICAL | placeholder diz "0 a 100" |
| Afiliado — Tema do video | `contact.afiliado__tema_do_video` | TEXT | |
| Afiliado — URL do video | `contact.afiliado__url_do_video` | TEXT | |
| Afiliado — Data do video | `contact.afiliado__data_do_video` | DATE | |
| Afiliado — Tier | `contact.afiliado__tier` | SINGLE_OPTIONS | Bronze · Prata · Ouro · Black |
| Afiliado — Fonte de captacao | `contact.afiliado__fonte_de_captacao` | SINGLE_OPTIONS | TikTok Affiliate Center · YouTube API · Instagram hashtag · Curadoria · Open Collaboration · Indicacao |
| Afiliado — Motivo do descarte | `contact.afiliado__motivo_do_descarte` | SINGLE_OPTIONS | Fora do nicho · Engajamento baixo · Sem resposta · Recusou · E revendedor Nitron · Nao vende fisico · Amostra sem video |
| Afiliado — Data ultima amostra | `contact.afiliado__data_ultima_amostra` | DATE | |
| Afiliado — Qtd amostras enviadas | `contact.afiliado__qtd_amostras_enviadas` | NUMERICAL | |
| Afiliado — Codigo de rastreio | `contact.afiliado__codigo_de_rastreio` | TEXT | |
| Afiliado — Ref amostra Sankhya | `contact.afiliado__ref_amostra_sankhya` | TEXT | |
| Afiliado — GMV estimado | `contact.afiliado__gmv_estimado` | MONETORY | |
| Afiliado — GMV acumulado | `contact.afiliado__gmv_acumulado` | MONETORY | |
| Afiliado — ROI da amostra | `contact.afiliado__roi_da_amostra` | NUMERICAL | |
| Afiliado — Cupom unico | `contact.afiliado__cupom_unico` | TEXT | |

Campos gerais que a jornada usa:

| Campo | Chave | Nota |
|---|---|---|
| CPF | `contact.cpf` | |
| CNPJ | `contact.cpfcnpj` | atencao: o **nome** e CNPJ, a **chave** e `cpfcnpj` |
| Codigo Representante | `contact.codigo_representante` | trava de revendedor do W0/W5/W9 |
| WhatsApp | `contact.whatsapp` | campo customizado, separado do phone padrao |
| **Bairro** | **nao existe** | criar como TEXT, sem prefixo de afiliado. **So pela interface** — ver abaixo |

### Kit e Marca recriados em 20/08/2026 — e a regra que sai disso

Os dois campos foram apagados e recriados **duas vezes** no mesmo dia:
TEXT -> `SINGLE_OPTIONS` -> TEXT. A ida e volta teve motivo: campo
`SINGLE_OPTIONS` **nao tem a caixa `Oculto`** no editor do formulario, e
campo de texto tem. Como quem escreve nesses dois campos e o seletor, e nao
o criador, eles nao precisam de picklist — precisam ficar invisiveis.

Estado final:

| Campo | id atual | tipo | ids anteriores |
|---|---|---|---|
| `Afiliado — Kit alocado` | `XeGF0Od66n8c70ltFBrO` | TEXT | `X85LQ2NJm7A8ZpjUGLIo`, `EdwnNYOZ8DjDA3pcxBVe` |
| `Afiliado — Marca alocada` | `HaR3w2zhAA2TYjroBAMJ` | TEXT | `qcvIg5mpVpgqUn5yQhRh` |

**A chave sobreviveu as tres vezes; o id mudou nas tres.** E isso separa as
duas integracoes:

- o **seletor de kits** casa por pedaco de chave (`kit_alocado`), entao
  atravessou as tres recriacoes sem uma linha de mudanca
- o **`ghl-sync`** escreve por id, entao cada recriacao deixou o id antigo
  apontando para um campo que nao existe mais

Regra: **recriar campo customizado no GHL exige atualizar `ghl_campos`.**
Nao ha erro quando o id esta errado — a API aceita e ignora em silencio. Os
dois estao com `ativo = false` por decisao de arquitetura, o que por sorte
tornou as tres trocas inofensivas; se estivessem ligados, seriam tres
periodos de escrita no vazio.

### Primeiro envio real do formulario — 20/08/2026

Contato `8E3rKOQodCSx5F0NBQh4` (Renan Dan Yamamoto), enviado 14:28. Os dois
campos chegaram gravados:

| Campo | Valor |
|---|---|
| `Afiliado — Kit alocado` | `905.K01.999` |
| `Afiliado — Marca alocada` | `Teak Brazil` |

O seletor esta provado ponta a ponta: clique no card -> escrita no campo do
GHL -> submit -> valor no contato.

**O que este teste NAO validou, e por que:** nenhum card foi criado em
`Afiliados Jornada`. O contato usado ja existia na base como cliente do Clube
Nitron (Polypus Digital) e tem **CNPJ preenchido** — que e exatamente a trava
de revendedor do W9 passo 2. Para testar o resto do W9, precisa de um contato
limpo, sem CNPJ nem codigo de representante, com a tag `afil-teste`.

### Campo de contato nao se cria por API — testado

### Campo de contato nao se cria por API — testado

Tentado em 19/08/2026, e a API responde sem ambiguidade:

```
POST /custom-fields/  { objectKey: "contact", fieldKey: "contact.bairro", ... }
-> 400  "Api does not support objectKey of type contact or opportunity"
```

A rota de leitura por id tem o mesmo limite:
`GET /custom-fields/{id}` -> 400 `"Fields with model contact is not supported on this route"`.

O `POST /custom-fields/` so aceita Custom Object e Company. Ler a lista de
campos de contato funciona (`GET /locations/{id}/customFields?model=contact`),
criar nao. Nao insistir: e limite do GHL, nao de credencial.

**Como criar o Bairro:** `Settings` -> `Custom Fields`, na mesma pasta onde
estao `CPF`, `CNPJ`, `Codigo Representante`, `Zona` e `Praca`
(id `BBYq38L550saG72oULys`). Tipo **TEXT**, nome **Bairro**, sem prefixo de
afiliado — ele serve para a conta toda, nao so para afiliado.

Depois de criar, faltam dois passos que a interface tambem exige:
1. incluir o campo no formulario de cadastro de afiliado, senao o criador
   nunca preenche
2. adicionar `Bairro is not empty` nas condicoes do W9 passo 4 e do W1 passo 1

---

## Divergencias entre o que o Supabase grava e o que o GHL aceita

### 1. Vitrine — quebra de verdade

`derivar_vitrine()` no Supabase produz valores que a picklist do GHL nao tem:

| Supabase grava | GHL aceita | Registros hoje |
|---|---|---|
| `collshp.com` | `collshp.com (Shopee)` | **10** |
| `mycollection.shop` | `mycollection.shop` | 1 (ok) |
| `tipfy.pro` | `tipfy.pro` | 0 (ok) |
| `Shopee direto` | **nao existe na picklist** | 0 hoje |
| `Mercado Livre` | `Mercado Livre` | 0 (ok) |
| `Amazon` | `Amazon` | 0 (ok) |
| `Site proprio` | `Site proprio` | 36 (ok) |
| `Nenhuma` | `Nenhuma` | 50 (ok) |

Valor fora da picklist cai vazio — a causa numero um de condicao que nunca casa,
citada no proprio guia. Corrigido no sync por tabela de mapeamento
(`ghl_mapa_valores`), nao mudando o classificador: o rotulo do Supabase serve
para analise interna e nao precisa imitar a picklist.

### 2. Score em escalas diferentes

O `Afiliado — Score` do GHL foi pensado como 0 a 100. O `score_afiliado` do
Supabase e uma soma de pesos e hoje vai de **-6 a 8**. Nao trava nada (o campo
e numerico), mas quem olhar no GHL vai ler errado. Decidir: reescalar no sync,
ou mudar o placeholder do campo. Enquanto nao decidir, o sync **nao envia** o
score.

### 3. Motivo do descarte

O Supabase grava `Perfil privado`, `E marca ou seller`, `Audiencia pequena`,
`Inativo` — nenhum existe na picklist do GHL. Impacto baixo hoje: descartado
nao vai para o GHL. Vira problema se algum dia descartado for sincronizado.

### 4. Kit e marca vazios em 100% do pool

`kit_alocado` e `marca_alocada` estao **null nos 97 criadores**. Nada no pipeline
atual preenche esses campos. Consequencia em cadeia: sem marca o W9 aplica
`afil-sem-marca`, e o W1 barra a amostra no passo 3. A alocacao de kit e marca
e um passo que ainda nao existe — nem no Supabase, nem no GHL.

---

## Tags

Existem: `afiliado` `afil-bloqueado` `amostra-afiliado` `afil-nitron`
`afil-mundoud` `afil-teakbr` `afil-sem-email` `afil-sem-marca`

Faltam:

| Tag | Usada em | Gravidade |
|---|---|---|
| `afil-import` | **trigger do W0** | alta: sem ela a porta de entrada nao existe |
| `afil-devolvido` | W1 rejeicoes · W2b · W4 | alta: e a trava da Colisao 2 |
| `afil-conteudo-combinado` | W3, manual | alta: e a trava da Colisao 3 |
| `afil-revendedor` | W0 passo 1 | media |
| `afil-cadastro-incompleto` | W9 passo 4 | media |
| `afil-teste` | contato de teste | baixa |

Tags que ja existem e podem confundir por semelhanca: `sem-email` (sem prefixo
`afil-`), `creator_qualificado`, `teste-creator-piloto`, `origem-tiktok`,
`trilho:key-account`. Nenhuma e usada pelos W0-W9 — nao reaproveitar por
engano.


---

## Teste real do `ghl-sync` — 19/08/2026

Primeiro write de verdade no GHL vindo do pool. Escolhido de proposito um
`key_account`, porque ele entra no stage `Key Account`, que nao e trigger de
workflow nenhum: zero chance de mensagem sair.

**Criador:** `@beavilhosa` — 30.800 seguidores, 5,21% de engajamento,
`beatrizcolabs@gmail.com`. Virou key account pelo sinal de agencia no e-mail
(`colabs`), nao por audiencia.

| Passo | Endpoint | HTTP | Resultado |
|---|---|---|---|
| 1 | `POST /contacts/upsert` | 201 | contato novo `y5O6rdYtr4hRyUkVUP9c`, `new: true` |
| 2 | `POST /contacts/{id}/tags` | 201 | `tagsAdded: [afiliado, afil-import]` |
| 3 | `POST /opportunities/upsert` | 201 | card `awtONOhMvByWN5E0ggKw` em `Key Account` |
| 4 | `marcar_sincronizado()` | — | status `no_ghl`, ids gravados, 1 linha em `ghl_sync_log` |

### O que o teste provou

**Os 9 campos customizados entraram todos, pelo id.** E o GHL coage o tipo:
mandei `"5.21"`, `"30800"` e `"0"` como string e voltaram como numero
(`5.21`, `30800`, `0`). Nao precisa converter na origem.

**A tag entra aditiva.** O endpoint separado devolveu `tagsAdded` com as duas,
e o `upsert` do passo 1 deixou `tags: []` — confirmando que ele nao mexe em
tag quando o campo `tags` nao e enviado.

**O card nasce no stage certo e ninguem o move.** Reconsultado depois:
`lastStageChangeAt` igual ao `createdAt`, ainda em `Key Account`. O W5 nao
disparou, como esperado — o trigger dele e `Mapeado`.

**Nenhuma mensagem saiu.** Consultado por `contactId`: 0 mensagens em
WhatsApp/SMS e 0 em Email. O W7 nao tocou nele.

**A fila fechou o ciclo:** de 12 para 11 criadores pendentes, 1 log ok,
0 falhas.

### Efeito colateral util

A tag **`afil-import` passou a existir** (`GITCCbKTv5TKLVVmNiqY`), criada pelo
proprio endpoint de tags. Ou seja, o `add-tags` do GHL cria tag que nao existe
em vez de falhar. Restam cinco por criar: `afil-devolvido`,
`afil-conteudo-combinado`, `afil-revendedor`, `afil-cadastro-incompleto`,
`afil-teste`.

### O que o teste NAO cobriu

Os tres writes foram feitos pelas ferramentas do GHL, com o payload exato que
a `fila_sync_ghl` produziu, nao pela edge function rodando de ponta a ponta.
O que ficou sem exercicio e o laco da propria funcao: iteracao sobre varios
itens, tratamento de falha item a item e o `registrar_falha_sync`. A resolucao
do token pelo Vault **foi** exercitada, no ensaio que respondeu 200.
