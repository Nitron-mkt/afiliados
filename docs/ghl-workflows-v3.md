# Workflows W0–W9 do programa de afiliados — especificação v3

Arquivo de conhecimento para agente. Versão 3, 20/08/2026.
Revisado em 27/08/2026: **P1 e P2 fechadas**, e a secção 0 corrigida.
Substitui `ghl-workflows-w0-w9.md` (v2).

Todo ID, chave e estado neste arquivo foi **lido da API do GoHighLevel**, não
deduzido. Onde algo não existe, está escrito que não existe.

---

## 0. Antes de qualquer coisa: o que você NÃO consegue fazer

**A API do GoHighLevel não cria nem edita workflows.** Existem apenas:

- `GET /workflows/` — lista workflows (id, nome, status, versão)
- `POST /contacts/{contactId}/workflow/{workflowId}` — adiciona contato a um workflow

Não existe endpoint de criação ou edição de workflow. **Montar ou alterar um
workflow é clique manual no Workflow Builder.** Não tente por API; não relate
sucesso sem que uma pessoa tenha clicado.

O que a API **faz**, e é bastante: contato, tag, campo customizado,
oportunidade, mover stage, mensagem, busca. Ver secção 3.

**Campo customizado de contato SE cria por API** — pela rota antiga. Corrigido
em 27/08/2026; a versão anterior deste arquivo afirmava o contrário.

| Rota | Payload | Resposta |
|---|---|---|
| `POST /custom-fields/` | `{ objectKey: "contact", ... }` | `400 "Api does not support objectKey of type contact or opportunity"` |
| `POST /locations/{locationId}/customFields` | `{ name, dataType, model: "contact" }` | **`201`** |

A rota `/custom-fields/` só aceita Custom Object e Company. A rota
`/locations/` aceita `model: "contact"` e `model: "opportunity"`. Use a segunda.

O `Bairro` foi criado assim em 27/08. Ler funciona nas duas
(`GET /locations/{id}/customFields?model=contact`).

**Tag também se cria por API:** `POST /locations/{locationId}/tags` com
`{ name }`. Duplicata devolve `400 "The tag name is already exist."`, o que
serve como checagem. Criar a tag não dispara nada — é rótulo até ser aplicada.

**Workflow continua sendo o que a API não faz.** Reconferido em 27/08 contra o
registro completo de operações: só `GET /workflows/`,
`POST /contacts/{id}/workflow/{id}` e `DELETE /contacts/{id}/workflow/{id}`.
Nenhuma escrita no workflow, e — diferente do caso do campo — **nenhuma rota
alternativa**. Não procure de novo.

---

## 1. Invariantes: nunca viole isto

Estas cinco regras existem porque cada uma já custou, ou custaria, frete ou
reputação. Não as remova em nome de simplificação.

| # | Invariante | Se violado |
|---|---|---|
| I1 | **O passo 1 do W4 checa e remove `afil-devolvido`, e encerra.** | Toda amostra extraviada vai para `Recorrente` como se fosse afiliado ativo pedindo a segunda |
| I2 | **O W2b devolve card para `Aceito`, nunca para `Amostra solicitada`.** | O W1 dispara na hora e gera segundo despacho para o endereço que acabou de falhar |
| I3 | **Os quatro ramos de rejeição do W1 aplicam `afil-devolvido` ANTES de mover o card.** | Card barrado por validação vai para `Recorrente` em vez de ficar em `Aceito` |
| I4 | **O W2 e o W2b checam a tag `amostra-afiliado` no passo 1.** | O trigger dispara em toda entrega da empresa. 1.223 contatos já entraram no W2 |
| I5 | **`Stop on Response` fica DESLIGADO no W3.** | Criador que responde "vou gravar sábado" sai da cobrança sem preencher a URL, e nunca é cobrado nem bloqueado |

Duas regras de ordem, que decorrem das acima:

- **W4 tem que existir antes de o W1 ser publicado.** W1 gera amostra → amostra
  gera extravio → extravio devolve card para `Aceito` → é aí que o W4 age.
- **O W0 não deve ser construído.** Ver secção 5.

---

## 2. Estado real hoje

### Workflows

| Guia | Nome no GHL | ID | Status | Contatos que entraram |
|---|---|---|---|---|
| W0 | — | — | não existe | — |
| W1 | `W1 Marcação e ponte para logística` | `9936a193-811e-4da8-9bca-d745ad720fb4` | draft | 0 |
| W2 | `W2 Amostra entregue` | `7e9e8642-6515-4d4c-b6b1-cbe7a348f204` | published | 1223 |
| W2b | `W2b Amostra extraviada` | `c23929da-6c9c-4c39-9d98-92bd48793d0e` | published | 23 |
| W3 | `W3 Cobrança de conteúdo` | `fb518d9d-8591-4c83-b9fa-c71dca5e6fc2` | draft | 0 |
| W4 | — | — | **não existe** | — |
| W5 | `W5 Exclusão de revendedor` | `10a9877f-5f20-486b-bfd3-4c5df998a07b` | published | 0 |
| W6 | — | — | não existe | — |
| W7 | `W7 Sequência de e-mail` | `826540f2-4f9c-4161-a6d6-e57afa694164` | **published** | 0 |
| W8 | `W8 Resposta detectada` | `00e9d5d1-c9f4-492f-838b-8925baab61ba` | published | 32 |
| W9 | `W9 Formulário recebido` | `d6ff662d-782e-401a-9b71-77a015282a13` | published | 0 |

Sobram na conta, e não fazem parte do programa:

- `New Workflow : 1786716077172` — `2d3a203a-b9d4-43bc-844e-e180c0297d61`, draft,
  criado 14/08. Rascunho abandonado. Apagar: workflow duplicado é a causa citada
  para o `Remove From Workflow` do W8 falhar.
- `AfiliadoNitron` — `2d3f541b-0a23-469c-b84c-77e8012c647a`, published, de
  março/2026. Anterior a este projeto. Conferir se não conflita.

### Verificações feitas

- **A trava do W2 funciona.** 1.223 contatos entraram; 0 contatos têm a tag
  `amostra-afiliado`, 0 cards vieram daí para `Afiliados Jornada`, 0 mensagens
  de saída. Ninguém indevido recebeu nada.
- **O W7 nunca enviou e-mail.** 0 contatos entraram, porque nada chegou a
  `Qualificado` — o pipeline de afiliados tem 1 card, criado por teste.
- **O pipeline `Afiliados Jornada` tem 1 card.** O programa não começou.

### Pendências que bloqueiam

| # | Pendência | Bloqueia |
|---|---|---|
| ~~P1~~ | ~~Campo `Bairro` não existe~~ | **fechada 27/08**: `contact.bairro`, id `dDlZtl9xsCdQYNXov8eQ`, TEXT. Falta só entrar no formulário |
| ~~P2~~ | ~~Cinco tags não existem~~ | **fechada 27/08**: todas as doze tags `afil-*` existem. IDs em `ghl-inventario.md` |
| P3 | Frete não medido, comissão não travada | publicar o W7 |
| P4 | GMV não volta do Sankhya/Shopify para o GHL | o W6 não teria o que observar |
| P5 | `Afiliado — Ref amostra Sankhya` vazio em todos os contatos, nada preenche | rastrear custo real por afiliado |

---

## 3. Referência: IDs e chaves

Sub-conta (`locationId`): **`rZ8y7lzqV7fzxsartaX2`**

### Pipeline `Afiliados Jornada` — `EbgtwZHPzdflM2Psu5jw`

| Pos | Estágio | `pipelineStageId` |
|---|---|---|
| 0 | Mapeado | `549a5362-dd4e-497c-a876-ff5bf33d299d` |
| 1 | Key Account | `e3fc2944-4365-475d-8c12-ff427aa73fa9` |
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

Os estágios 10 e 11 têm **acento**. Condição por texto exato sem acento não casa.

### Outros pipelines

| Pipeline | `pipelineId` | Estágio | `pipelineStageId` |
|---|---|---|---|
| Pedidos-Preparacao | `4DhlIKQogaq9CiIg8ghW` | Pedidos a Liberar | `6efd0b95-e097-4ed2-b8d4-fbad4a054d35` |
| Entregas | `YYykD6oEtzh9jpKYbpGp` | Entregue | `ec822b9b-ac7f-4170-8dfb-0cd163f425f0` |
| Entregas | `YYykD6oEtzh9jpKYbpGp` | Retorno | `ad46f442-7900-44ac-b6ff-fd18fb07b903` |

### Campos de contato

Todos `model: contact`. O **id** é para escrita por API; a **chave** é para
condições no Workflow Builder e para merge field.

| Nome no GHL | Chave | id | Tipo |
|---|---|---|---|
| CNPJ | `contact.cpfcnpj` | `TLRZeTrxxPBsMNRqbdHO` | TEXT |
| Codigo Representante | `contact.codigo_representante` | `Glhn2OQNaD311ONt8lCk` | TEXT |
| CPF | `contact.cpf` | `CM2BJoxHA7FA6yp0qn90` | TEXT |
| WhatsApp | `contact.whatsapp` | `yAsQNjO4m5dl7lBKOs1h` | PHONE |
| Instagram | `contact.instagram` | `goLActuA0uU3CloPUFBy` | TEXT |
| **Bairro** | `contact.bairro` | `dDlZtl9xsCdQYNXov8eQ` | TEXT |
| Afiliado — Kit alocado | `contact.afiliado__kit_alocado` | `XeGF0Od66n8c70ltFBrO` | TEXT |
| Afiliado — Marca alocada | `contact.afiliado__marca_alocada` | `HaR3w2zhAA2TYjroBAMJ` | TEXT |
| Afiliado — Trilha | `contact.afiliado__trilha` | `dj7l8lVTMAEK1SkeK6jD` | SINGLE_OPTIONS |
| Afiliado — Plataforma principal | `contact.afiliado__plataforma_principal` | `76ohuJZvTcRbHN8LnGRi` | SINGLE_OPTIONS |
| Afiliado — Handle principal | `contact.afiliado__handle_principal` | `UBfJdvWxRHBPTp4jdaON` | TEXT |
| Afiliado — URL do perfil | `contact.afiliado__url_do_perfil` | `aGtcG8QlLJf5tWDw3F6x` | TEXT |
| Afiliado — Seguidores | `contact.afiliado__seguidores` | `m5IjXrMQjZtULYcbbzUP` | NUMERICAL |
| Afiliado — Engajamento % | `contact.afiliado__engajamento_` | `EFA1oBYuWb3nIk5Q3FeM` | NUMERICAL |
| Afiliado — Posts ultimos 30 dias | `contact.afiliado__posts_ultimos_30_dias` | `KkwE2mW1Mimvs0bGKr1w` | NUMERICAL |
| Afiliado — Vende produto fisico | `contact.afiliado__vende_produto_fisico` | `LWC9nH8BTQvWJuKqzEmW` | SINGLE_OPTIONS |
| Afiliado na: (vitrine) | `contact.afiliado__vitrine` | `0eVAv3v98X2YRhkaeeTh` | SINGLE_OPTIONS |
| Afiliado — Comissao % | `contact.afiliado__comissao_` | `5xcgwYOjZqreTjypVrtD` | NUMERICAL |
| Afiliado — Comissao paga | `contact.afiliado__comissao_paga` | `UgUHyzD1j0I7Ac19lLgD` | MONETORY |
| Afiliado — Score | `contact.afiliado__score` | `l5WfXFGmqxC2fgyeMGPD` | NUMERICAL |
| Afiliado — Tema do video | `contact.afiliado__tema_do_video` | `ir6DY9ZwuWUgaGXi68K7` | TEXT |
| Afiliado — URL do video | `contact.afiliado__url_do_video` | `GcJUQbCwlZiQgTJpQCD1` | TEXT |
| Afiliado — Data do video | `contact.afiliado__data_do_video` | `jy7xLx7jsrxEi9w6DEcN` | DATE |
| Afiliado — Tier | `contact.afiliado__tier` | `w2J2W9u33BPaPifsGYBe` | SINGLE_OPTIONS |
| Afiliado — Fonte de captacao | `contact.afiliado__fonte_de_captacao` | `Y7Eq4RQgUwvVGbmfl0To` | SINGLE_OPTIONS |
| Afiliado — Motivo do descarte | `contact.afiliado__motivo_do_descarte` | `xbtzI5zlW5foKAgVzNlu` | SINGLE_OPTIONS |
| Afiliado — Data ultima amostra | `contact.afiliado__data_ultima_amostra` | `gH41i1uUppD622MsU0gB` | DATE |
| Afiliado — Qtd amostras enviadas | `contact.afiliado__qtd_amostras_enviadas` | `iN2PInIpnU9hhG1ZFWGA` | NUMERICAL |
| Afiliado — Codigo de rastreio | `contact.afiliado__codigo_de_rastreio` | `whA811XZg4VZEZgewOLR` | TEXT |
| Afiliado — Ref amostra Sankhya | `contact.afiliado__ref_amostra_sankhya` | `y1hQIUaAaQirLMnpnQST` | TEXT |
| Afiliado — GMV estimado | `contact.afiliado__gmv_estimado` | `A9QPFbzAWG5xhMBv5FTo` | MONETORY |
| Afiliado — GMV acumulado | `contact.afiliado__gmv_acumulado` | `NpIsp2NAT32Qa2wgRyDg` | MONETORY |
| Afiliado — ROI da amostra | `contact.afiliado__roi_da_amostra` | `cyA3dR23Bx8ucUHK8Kxh` | NUMERICAL |
| Afiliado — Cupom unico | `contact.afiliado__cupom_unico` | `sLbwj9F10eeN71X9wTKf` | TEXT |

### Três nomes que enganam

1. **O campo chamado `CNPJ` tem a chave `contact.cpfcnpj`.** Não existe chave
   `cnpj`. Pegar o errado quebra a trava de revendedor em W5 e W9.
2. **O campo de vitrine se chama `Afiliado na:`**, com dois-pontos, e a chave é
   `contact.afiliado__vitrine`.
3. **`WhatsApp` é campo customizado**, separado do `phone` padrão do contato.

### Duas chaves para o mesmo campo

O GHL guarda duas identidades e elas **não** batem:

| Onde | Exemplo |
|---|---|
| `fieldKey` da API | `contact.afiliado__kit_alocado` |
| "Chave de consulta" no editor de formulário | `afiliado_—__kit_alocado` |

A segunda deriva do **nome** do campo (`Afiliado — Kit alocado`) e carrega o
travessão. Ao casar campo por nome/atributo no DOM, use só o pedaço final
(`kit_alocado`), que casa com as duas.

### Valores de picklist

```
afiliado__trilha:              Achadinhos | Mudanca casa nova | Nicho organizacao | Curadoria teca | Key account
afiliado__tier:                Bronze | Prata | Ouro | Black
afiliado__fonte_de_captacao:   TikTok Affiliate Center | YouTube API | Instagram hashtag | Curadoria | Open Collaboration | Indicacao
afiliado__motivo_do_descarte:  Fora do nicho | Engajamento baixo | Sem resposta | Recusou | E revendedor Nitron | Nao vende fisico | Amostra sem video
afiliado__vitrine:             collshp.com (Shopee) | mycollection.shop | tipfy.pro | Mercado Livre | Amazon | Site proprio | Nenhuma
afiliado__vende_produto_fisico: Sim | Nao | Nao identificado
afiliado__plataforma_principal: TikTok | Instagram | YouTube | Shopee | Mercado Livre | Kwai | Pinterest
```

`afiliado__kit_alocado` e `afiliado__marca_alocada` são **TEXT**, sem picklist:
quem escreve neles é o seletor de kits do formulário, nunca o criador.

### Tags

Existem:

| Tag | id |
|---|---|
| `afiliado` | `SiVQ6UgiZN3snBgnXFYu` |
| `afil-import` | `GITCCbKTv5TKLVVmNiqY` |
| `afil-bloqueado` | `68FYzdt5HYf8jvQvdRMH` |
| `amostra-afiliado` | `ogpBTX25NhIZZ1zolXPe` |
| `afil-nitron` | `zOR4GxgGo3vjjoq8oh9Q` |
| `afil-mundoud` | `bBM5nhlAv0X8jjmMkIUc` |
| `afil-teakbr` | `3M1fukkjZolef2jMyaJJ` |
| `afil-sem-email` | `UAZ9Jx4clAQjRsPHFGjR` |
| `afil-sem-marca` | `ASlYQszJxPqlJwPHLNvc` |

**Faltam criar** — sem elas as condições não têm o que selecionar:

| Tag | Usada em | Ciclo de vida |
|---|---|---|
| `afil-devolvido` | W1 rejeições, W2b, W4 | aplicada e removida **só por automação**. Nunca à mão |
| `afil-conteudo-combinado` | W3 | **100% manual**. Aplicar quando alguém combina data; remover quando o vídeo sai ou a data passa |
| `afil-revendedor` | W5, W9 | aplicada por automação, permanente |
| `afil-cadastro-incompleto` | W9 passo 4 | aplicada e removida por automação |
| `afil-teste` | contato de teste | manual |

Tags parecidas que **não** pertencem ao programa e não devem ser reaproveitadas:
`sem-email`, `creator_qualificado`, `teste-creator-piloto`, `origem-tiktok`,
`trilho:key-account`.

### Kits aprovados

O valor gravado em `afiliado__kit_alocado` é a **referência do ERP**, não o nome.

| Referência | Kit | Marca | Custo direto |
|---|---|---|---|
| `905.K01.999` | Churrasco | Teak Brazil | 64,43 |
| `914.K01.002` | Micro-ondas | Mundo UD | 23,69 |
| `907.K01.999` | Frasqueira de Medicamentos | Mundo UD | 29,30 |

A marca deriva do kit por tabela fixa, dentro do seletor do formulário. A tabela
completa dos 20 kits está em `seletor-de-kits.md`.

---

## 4. Convenções do Workflow Builder

A interface da sub-conta está em **português**, mas trigger e action mantêm nome
em inglês. Se algum aparecer traduzido, está na mesma posição da lista.

### Nomes que a v2 usava errado

| Nome errado | No GHL é |
|---|---|
| `Move Opportunity` | **`Update Opportunity`** — escolhe pipeline e stage. Não existe "Move Opportunity" |
| `Add Tag` | **`Add Contact Tag`** |
| `Update Field` | **`Update Contact Field`** |
| `Remove from Workflow` | **`Remove From Workflow`** |
| comentário no card | **`Internal Notification`** — é e-mail para o time |

### Onde ficam as coisas

| O que | Caminho |
|---|---|
| Criar workflow | `Automation` → `Workflows` → `+ Create Workflow` → `Start from Scratch` |
| Adicionar trigger | `Add New Trigger`, topo do canvas |
| Adicionar ação | botão `+` abaixo do trigger |
| Ligar/desligar | toggle `Draft` / `Publish`, topo direito |
| `Allow Re-Entry`, `Stop on Response`, `Time Window` | ícone de engrenagem do workflow |
| Tags | `Settings` → `Tags` |
| Campos customizados | `Settings` → `Custom Fields` |

### Configuração por workflow

| Workflow | `Allow Re-Entry` | `Stop on Response` | `Time Window` |
|---|---|---|---|
| W9 | **ligado** | — | — |
| W7 | — | **ligado** | opcional |
| W3 | — | **DESLIGADO** (I5) | recomendado |
| W2 | — | **ligado** | recomendado |
| demais | — | — | — |

### Condição de campo customizado

1. no `If/Else`, categoria → `Custom Fields`
2. procurar pelo nome de exibição
3. operador → `is` / `is empty` / `is not empty` / `contains` / `greater than`
4. valor → **exatamente** como na picklist, incluindo acento ou a falta dele

### Condição de data relativa

O dropdown oferece oito opções. Para "nos últimos N dias" a correta é
**`In the Last`**.

| Opção | O que faz |
|---|---|
| **`In the Last` + N Dias** | a data cai dentro dos últimos N dias — **é esta** |
| `Before` + N Dias | data anterior a hoje−N, ou seja **mais antiga** que a janela. É o oposto, e a mais perigosa porque parece razoável |
| `After` + N Dias | posterior a hoje+N. Futuro, nunca casa |
| `In the Next` + N Dias | janela futura. Nunca casa para evento passado |
| `After date` / `Before date` | data fixa. Envelhece |
| `On` / `Yesterday` | dia exato, não janela |

**Data vazia não casa com `In the Last`.** Logo, não é preciso somar
`is not empty`: uma condição só, e o registro sem data cai no ramo NÃO.

---

## 4b. A regra do builder que reordena três workflows

Descoberta ao desenhar os canvas, 31/08/2026. Não estava em nenhuma versão
anterior deste arquivo, e explica por que a ordem dos passos aqui **não** é a
ordem em que você monta.

**Ramo do GHL nunca volta para o tronco.** Cada `Branch` (e cada lado de um
`If/Else`) segue sozinho até o fim. Não existe nó de junção.

Consequência: todo passo da forma *"faça X só se Y, **depois continue**"* custa
uma cópia de tudo o que vem depois dele. Então esses passos têm que ser os
últimos, ou virar o problema de outra camada.

Onde isso mordeu:

| Workflow | O que a especificação numerava no meio | O que fazer |
|---|---|---|
| **W9** | passo 5, tag de marca por `If/Else` de 4 ramos | vai para o **fim**. Nada dentro do W9 lê a tag de marca, então a ordem não muda comportamento — e economiza 16 nós repetidos |
| **W9** | passo 7, `fonte_de_captacao` vazia → `Curadoria` | **sai do workflow**. É um segundo "faça X só se Y, depois continue", e só um pode ser o último. Resolver no formulário (campo oculto com valor padrão) |
| **W7** | passos 3 a 10, a cadência depois do roteador de trilha | a cadência mora **dentro de cada ramo** de trilha. Não custa nada: os templates já eram por trilha (A2, B2, C2) |

E onde o `Condition` de vários `Branch` reduz nós, como já era o caso no W1:

| Workflow | Antes | Depois |
|---|---|---|
| W9 | 4 `If/Else` | 2 `Condition` |
| W4 | 2 `If/Else` | **1 `Condition`** — o workflow inteiro |
| W6 | 2 `If/Else` | 1 `Condition` |

**Em W4 e W6 a ordem dos `Branch` passa a ser a regra, não estética:**

- **W4** — `afil-devolvido` tem que ser o `Branch 1`. Uma amostra extraviada de
  quem recebeu amostra há 10 dias casa nos **dois** Branch; o GHL pega o
  primeiro. Se a ordem inverter, acontece a Colisão 2. É a invariante I1
  expressa como ordem de Branch.
- **W6** — `greater than 5000` tem que ser o `Branch 1`. Na versão sequencial
  funcionava porque o segundo `If/Else` sobrescrevia o primeiro. Numa
  `Condition`, se `greater than 0` vier primeiro ele casa com todo mundo e o
  ramo Ouro nunca é avaliado.

Os canvas nó por nó estão em `docs/canvas-workflows.html` (os nove) e
`docs/w1-canvas.html` (o W1).

---

## 5. W0 — não construir

A edge function `ghl-sync` (repositório `nitron-mkt/afiliados`,
`supabase/functions/ghl-sync/`) já faz o trabalho do W0 e mais:

1. `POST /contacts/upsert` com os campos do pool
2. `POST /contacts/{id}/tags` com `afiliado` e `afil-import` — endpoint separado
   de propósito: o campo `tags` do upsert **substitui** todas as tags do
   contato, e o criador pode já existir na base como cliente B2B
3. `POST /opportunities/upsert` — card em `Mapeado`, ou em `Key Account` quando
   o roteamento do Supabase marcou key account

O W0 não sabia fazer o item 3 com desvio para `Key Account`. E a trava de
revendedor que ele faria, o W5 repete em `Mapeado` como rede de segurança.

Construir o W0 agora cria um segundo lugar onde a mesma lógica pode divergir.

---

## 6. Especificação por workflow

Ordem de construção: **W9 → W5 → W4 → W1 → W2/W2b → W3 → W8 → W7 → W6**.

### W9 · Formulário recebido

Porta de entrada real. Todo criador que chega a `Aceito` passa por aqui.

- **Trigger:** `Form Submitted` → formulário de cadastro de afiliado
- **Config:** `Allow Re-Entry` **ligado**

| # | Ação | Detalhe |
|---|---|---|
| 1 | `Add Contact Tag` | `afiliado` |
| 2 | `If/Else` "é revendedor?" | `contact.cpfcnpj` `is not empty` **OR** `contact.codigo_representante` `is not empty` |
| 3 | `If/Else` "está bloqueado?" | `Contact Tag` `is` `afil-bloqueado` |
| 4 | `If/Else` "cadastro completo?" | ver abaixo |
| 5 | `If/Else` 4 ramos "qual marca?" | ver abaixo |
| 6 | `Update Contact Field` | `afiliado__tier` = `Bronze` |
| 7 | `If/Else` `afiliado__fonte_de_captacao` `is empty` | SIM → `Curadoria`; NÃO → nada |
| 8 | `Create/Update Opportunity` | `Afiliados Jornada` / `Aceito` |
| 9 | `Send Email` | boas-vindas |

**Passo 2, ramo SIM:** `Update Contact Field` `afiliado__motivo_do_descarte` =
`E revendedor Nitron` · `Add Contact Tag` `afil-revendedor` ·
`Update Opportunity` `Status` = `Lost` · `Internal Notification` · **fim**

**Passo 3, ramo SIM:** `Internal Notification` · **fim**

**Passo 4, condições todas com `AND`, todas `is not empty`:**
`contact.cpf` · `contact.whatsapp` · `Postal Code` (padrão) ·
`Address` (padrão) · `Bairro` (`contact.bairro`)

- **Ramo NÃO:** `Add Contact Tag` `afil-cadastro-incompleto` · `Send Email`
  pedindo o dado que falta · `Update Opportunity` → `Respondeu` ·
  `Wait` `2 days` · `If/Else` `contact.cpf` `is empty` → segundo toque · **fim**
- **Ramo SIM:** `Remove Contact Tag` `afil-cadastro-incompleto` · segue

**Passo 5:** a marca **já chega preenchida** pelo formulário, derivada do kit.
Este passo só traduz o campo em tag.

| Condição | Ação |
|---|---|
| `afiliado__marca_alocada` `is` `Nitron` | `Add Contact Tag` `afil-nitron` |
| `is` `Mundo UD` | `Add Contact Tag` `afil-mundoud` |
| `is` `Teak Brazil` | `Add Contact Tag` `afil-teakbr` |
| `Else` | `Add Contact Tag` `afil-sem-marca` + `Internal Notification` |

O ramo `Else` deixou de ser caminho normal e virou **detector de anomalia**: só
cai ali quem enviou o formulário sem escolher kit. Se essa notificação começar a
chegar sempre, o problema está no seletor, não no criador.

**Nota de fluxo:** o passo 8 escreve em `Aceito`, o que dispara o W4. Para
criador novo é inofensivo (`data_ultima_amostra` vazia). Para quem reenvia o
formulário depois de já ter recebido amostra, o W4 move para `Recorrente` — e
nesse caso é o comportamento correto.

### W5 · Exclusão de revendedor

Rede de segurança. Pega card criado por qualquer caminho.

- **Trigger:** `Pipeline Stage Changed` → `Afiliados Jornada` / `Mapeado`

| # | Ação | Detalhe |
|---|---|---|
| 1 | `If/Else` "é revendedor?" | mesmas condições do W9 passo 2 |
| 2 | `Update Opportunity` | `Afiliados Jornada` / `Qualificado` |

**Passo 1, ramo SIM:** `Update Contact Field` `afiliado__motivo_do_descarte` =
`E revendedor Nitron` · `Add Contact Tag` `afil-revendedor` ·
`Update Opportunity` `Status` = `Lost` · `Internal Notification` · **fim**

**Key Account não passa por aqui.** O trigger é `Mapeado`, e o `ghl-sync` põe
key account direto em `Key Account`. Então criador grande nunca é promovido a
`Qualificado`, nunca entra no W7, e nunca recebe o e-mail automático de comissão
— que seria constrangedor com quem cobra cachê. É de propósito.

### W4 · Trava de reenvio

**Construir antes de publicar o W1.**

- **Trigger:** `Pipeline Stage Changed` → `Afiliados Jornada` / `Aceito`

| # | Ação | Detalhe |
|---|---|---|
| 1 | `If/Else` "foi devolvido por automação?" | `Contact Tag` `is` `afil-devolvido` |
| 2 | `If/Else` "já recebeu amostra recente?" | `afiliado__data_ultima_amostra` `is` `In the Last` `90` `Dias` |

**Passo 1, ramo SIM:** `Remove Contact Tag` `afil-devolvido` · **fim**

Este passo é a invariante I1. Encerra o workflow e limpa a tag no mesmo
movimento, então nada acumula e ninguém precisa remover tag à mão.

**Passo 2, ramo SIM:** `Internal Notification` (texto na secção 7) ·
`Update Opportunity` → `Recorrente` · **fim**
**Ramo NÃO:** **fim** — segue livre para `Amostra solicitada`

Uma condição só no passo 2, não duas: data vazia não cai dentro de janela.

**Teste de sentido:** criador novo, com `data_ultima_amostra` vazia, tem que
passar reto. Se for para `Recorrente`, o operador está invertido.

### W1 · Ponte para logística

Porteiro antes do frete.

- **Trigger:** `Pipeline Stage Changed` → `Afiliados Jornada` / `Amostra solicitada`

#### Estrutura no canvas: 2 nós Condition, não 4

A especificação abaixo descreve quatro validações. No canvas do GHL, montá-las
como quatro `If/Else` em série gera 4 nós Condition e 12 nós de ação, com a
mesma sequência repetida quatro vezes.

Um `Condition` do GHL aceita **vários Branch** e pega o **primeiro que casar**.
Então a montagem correta inverte a pergunta:

```
Condition 1 — "tem algo errado?"
  Branch 1  Dados incompletos   CPF is empty OR Address is empty OR Postal Code is empty
  Branch 2  Bloqueado           Tags incluir afil-bloqueado
  Branch 3  Sem marca           afiliado__marca_alocada is empty
  None      passou              -> segue

Condition 2 — "kit permitido?"
  Branch    Kit na lista        afiliado__kit_alocado contains 905.K01.999 OR 914.K01.002 OR 907.K01.999
  None      kit fora            -> DEVOLVER
```

**A ordem dos Branch importa.** O GHL para no primeiro que casar. Criador sem
CPF **e** bloqueado cai no Branch 1, e a notificação é de dados incompletos.
Está correto: o primeiro problema é o que se resolve primeiro. Não inverta
`Bloqueado` para depois de `Dados incompletos` sem pensar — faria alguém
corrigir endereço de quem não pode receber.

Canvas desenhado nó por nó: `w1-canvas.html`.

Os quatro ramos de rejeição compartilham a mesma sequência:

**Ramo DEVOLVER:** `Add Contact Tag` `afil-devolvido` · `Internal Notification`
dizendo o que falta · `Update Opportunity` → `Aceito` · **fim**

A tag nos quatro ramos é a invariante I3.

| # | Ação | Condição | Se falhar |
|---|---|---|---|
| 1 | `If/Else` dados de envio | `contact.cpf` **AND** `Address` **AND** `Postal Code` **AND** `Bairro` (`contact.bairro`), todos `is not empty` | DEVOLVER |
| 2 | `If/Else` bloqueado | `Contact Tag` `is` `afil-bloqueado` | SIM → DEVOLVER |
| 3 | `If/Else` marca | `afiliado__marca_alocada` `is empty` | SIM → DEVOLVER |
| 4 | `If/Else` kit permitido | `afiliado__kit_alocado` `contains` cada referência, com `OR` | NÃO → DEVOLVER |
| 5 | `Create/Update Opportunity` | `Pedidos-Preparacao` / `Pedidos a Liberar`. Nome: `AMOSTRA - {{contact.first_name}} - {{contact.afiliado__kit_alocado}}` | |
| 6 | `Add Contact Tag` | `amostra-afiliado` — é a tag que o W2 e o W2b checam | |
| 7 | `Update Contact Field` | `afiliado__data_ultima_amostra` = hoje; `afiliado__qtd_amostras_enviadas` = atual + 1 | |

**Sobre o incremento do passo 7:** não está confirmado que o
`Update Contact Field` do GHL ofereça incremento de campo numérico. Se não
oferecer, em ordem de preferência: (a) usar
`{{contact.afiliado__qtd_amostras_enviadas}}` no valor, se o campo aceitar
merge field; (b) deixar de fora e contar pelo Supabase, que registra cada envio
em `ghl_sync_log`; (c) preencher à mão enquanto o volume é pequeno.
**Não gravar `1` fixo:** o W4 usa esse número para decidir segunda amostra, e um
valor sempre-1 esconde exatamente o caso que ele existe para pegar.

**Passo 4 compara referências, não nomes:** `905.K01.999`, `914.K01.002`,
`907.K01.999`. Kit novo liberado no frete = uma condição nova aqui.

**A ordem 1→4 antes do 5 não é negociável.** Invertido, gera pedido de amostra
para endereço vazio e o problema aparece na expedição, com o pacote na mão.

### W2 · Amostra entregue

- **Trigger:** `Pipeline Stage Changed` → `Entregas` / `Entregue`
- **Config:** `Stop on Response` **ligado**

| # | Ação | Detalhe |
|---|---|---|
| 1 | `If/Else` "é amostra de afiliado?" | `Contact Tag` `is` `amostra-afiliado`. NÃO → **fim** |
| 2 | `Update Opportunity` | `Afiliados Jornada` / `Amostra recebida` |
| 3 | `Wait` | `3 hours` |
| 4 | `Send WhatsApp` | ou `Send SMS`. Pergunta se chegou tudo certo, **sem citar o nome do kit** |

O passo 1 é a invariante I4: este trigger dispara em **toda entrega da empresa**.

O `Wait` de 3 horas existe porque "Entregue" costuma cair quando o pacote chega
na portaria. Mensagem antes de a pessoa ter a caixa na mão soa automática.

### W2b · Amostra extraviada

- **Trigger:** `Pipeline Stage Changed` → `Entregas` / `Retorno`

| # | Ação | Detalhe |
|---|---|---|
| 1 | `If/Else` "é amostra de afiliado?" | `Contact Tag` `is` `amostra-afiliado`. NÃO → **fim** |
| 2 | `Add Contact Tag` | `afil-devolvido` — **antes** de mover o card (I1/I3) |
| 3 | `Internal Notification` | endereço, rastreio, quantas amostras já foram, roteiro do que conferir |
| 4 | `Update Opportunity` | `Afiliados Jornada` / **`Aceito`** (I2) |

Depois, uma pessoa: confirma o endereço com o criador, corrige no contato,
arrasta o card para `Amostra solicitada`. **O criador não sabe que voltou** —
vale um WhatsApp no mesmo dia, mesmo sem solução pronta.

### W3 · Cobrança de conteúdo

- **Trigger:** `Pipeline Stage Changed` → `Afiliados Jornada` / `Amostra recebida`
- **Config:** `Stop on Response` **DESLIGADO** (I5) · `Time Window` recomendado

**Condição "precisa cobrar?"**, idêntica nos quatro `If/Else`:

```
afiliado__url_do_video  is empty
AND  Contact Tag  is not  afil-conteudo-combinado
```

Se a conta não tiver `is not` para tag, monte dois `If/Else` em série: primeiro
checa a tag e encerra se existir, depois checa o campo.

| # | Ação | Se "precisa cobrar?" = SIM |
|---|---|---|
| 1 | `Wait` `3 days` | |
| 2 | `If/Else` | `Send WhatsApp` — pergunta o que achou do kit, não cobra vídeo |
| 3 | `Wait` `4 days` | |
| 4 | `If/Else` | `Send Email` — três ideias de roteiro |
| 5 | `Wait` `11 days` | |
| 6 | `If/Else` | `Send WhatsApp` aviso final **e** `Internal Notification` "vou bloquear em 3 dias" |
| 7 | `Wait` `3 days` | |
| 8 | `If/Else` | `Update Opportunity` → `Inadimplente de conteúdo` · `Add Contact Tag` `afil-bloqueado` · `Update Contact Field` `afiliado__motivo_do_descarte` = `Amostra sem video` |

Ramo NÃO em qualquer um dos quatro: **fim**.

Total 21 dias. A notificação do passo 6 **não é opcional**: `url_do_video` é
preenchido à mão, então se o criador postar e ninguém colar o link, o W3
bloqueia quem cumpriu. Os três dias entre aviso e corte existem para conferir.

**Alternância de canal:** toques 1 e 3 por WhatsApp, toque 2 por e-mail. Nos
dois canais em cada toque, o criador recebe seis mensagens em 21 dias e a última
é um bloqueio.

**No teste, troque os `Wait` para minutos.** Testar em 21 dias reais é inviável.

### W8 · Resposta detectada

- **Trigger:** `Customer Replied` → canal `Email`

| # | Ação | Detalhe |
|---|---|---|
| 1 | `If/Else` "é afiliado?" | `Contact Tag` `is` `afiliado`. NÃO → **fim** (cliente B2B respondendo) |
| 2 | `Update Opportunity` | `Afiliados Jornada` / `Respondeu` |
| 3 | `Remove From Workflow` | o W7, **pelo nome exato** |
| 4 | `Internal Notification` | handle, seguidores, engajamento, trilha, vitrine. Meta: responder em 4h |

Se existirem versões do W7, o contato pode estar numa que o passo 3 não remove.
**Manter um W7 só.** Ver o rascunho abandonado na secção 2.

### W7 · Sequência de e-mail

**Voltar para `Draft`** até o frete estar medido (P3). É o único workflow que faz
promessa para fora: os e-mails citam percentual de comissão.

- **Trigger:** `Pipeline Stage Changed` → `Afiliados Jornada` / `Qualificado`
- **Config:** `Stop on Response` **ligado**

| # | Ação | Detalhe |
|---|---|---|
| 1 | `If/Else` "tem e-mail?" | `Email` `is empty` → `Add Contact Tag` `afil-sem-email` · **fim** (fica em `Qualificado`, vai para fila de DM) |
| 2 | `If/Else` 4 ramos "qual trilha?" | ver abaixo |
| 3 | `Update Opportunity` | → `Contatado` |
| 4 | `Wait` `4 days` | |
| 5 | `If/Else` | segundo toque por trilha (A2, B2, C2) |
| 6 | `Wait` `5 days` | |
| 7 | `If/Else` | terceiro toque (A3, B3, C3) |
| 8 | `Wait` `5 days` | |
| 9 | `Update Contact Field` | `afiliado__motivo_do_descarte` = `Sem resposta` |
| 10 | `Update Opportunity` | `Status` = `Lost` |

**Passo 2:**

| Condição | Ação |
|---|---|
| `afiliado__trilha` `is` `Achadinhos` | `Send Email` template A1 |
| `is` `Mudanca casa nova` | `Send Email` template B1 |
| `is` `Curadoria teca` | `Send Email` template D1 → `Update Opportunity` `Contatado` → **fim** |
| `Else` | `Send Email` template C1 — pega `Nicho organizacao` e trilha vazia |

`Curadoria teca` sai no primeiro toque de propósito: negociação com cachê,
tratada por pessoa.

### W6 · Primeira venda

Último a construir. Depende de P4: hoje o GMV não volta para o GHL.

- **Trigger:** `Contact Changed` → filtro `afiliado__gmv_acumulado`

| # | Ação | Detalhe |
|---|---|---|
| 1 | `If/Else` `afiliado__gmv_acumulado` `greater than` `0` | SIM → `Update Opportunity` → `Convertido` · `Update Contact Field` `afiliado__tier` = `Prata` · `Internal Notification` |
| 2 | `If/Else` `greater than` `5000` | `Update Contact Field` `afiliado__tier` = `Ouro` |

---

## 7. Textos de Internal Notification

Todas tipo `Email`, destinatário o time. **O criador não recebe nada disto.**

### W4 · Reenvio detectado

**Assunto**

```
Afiliado recorrente pedindo amostra: {{contact.first_name}}
```

**Corpo**

```
{{contact.first_name}} voltou para Aceito e ja recebeu amostra nos ultimos
90 dias. O card foi movido para Recorrente e NAO vai gerar pedido sozinho.

QUEM E
Handle: {{contact.afiliado__handle_principal}}
Perfil: {{contact.afiliado__url_do_perfil}}
Tier: {{contact.afiliado__tier}}
Marca: {{contact.afiliado__marca_alocada}}

O QUE JA FOI MANDADO
Amostras enviadas: {{contact.afiliado__qtd_amostras_enviadas}}
Ultima amostra em: {{contact.afiliado__data_ultima_amostra}}
Kit da ultima (referencia): {{contact.afiliado__kit_alocado}}

O QUE ELE DEU EM TROCA
Video: {{contact.afiliado__url_do_video}}
GMV acumulado: {{contact.afiliado__gmv_acumulado}}

COMO DECIDIR
O GMV e o criterio. Se ele vendeu, a segunda amostra se paga. Se nao
vendeu, e frete jogado fora.

Se o campo Video estiver vazio, confira o perfil dele ANTES de concluir
que nao entregou: esse campo e preenchido a mao, e pode ser que o video
exista e ninguem tenha colado o link.

Se Amostras enviadas for 3 ou mais, pare e pense. Tres amostras para a
mesma pessoa sem GMV nao e generosidade, e vazamento.

SE FOR PARA MANDAR
Arraste o card de Recorrente para Amostra solicitada. O W1 valida
endereco e kit de novo antes de gerar o pedido.

Nao fazer nada tambem e uma decisao valida: o card fica parado em
Recorrente e nenhuma amostra sai.
```

### Textos ainda não escritos

Os quatro ramos de rejeição do W1, o do W2b, o "bloqueio em 3 dias" do W3, o do
W8, o de revendedor (W5/W9), o de sem-marca (W9) e o da primeira venda (W6)
existem na v2 (`ghl-workflows-w0-w9.md`, secção TEXTOS DAS NOTIFICAÇÕES
INTERNAS). **Antes de reaproveitar, conferir duas coisas:**

1. as chaves de merge field contra a tabela da secção 3 — a v2 tinha chaves
   deduzidas, e algumas estavam erradas
2. a linha do kit, que agora traz **referência** e não nome; rotular como
   "Kit (referencia)" para o leitor não procurar um nome que não vem

---

## 8. Teste ponta a ponta

Contato de teste com a tag `afil-teste`. Precisa ser **limpo**: sem
`contact.cpfcnpj`, sem `contact.codigo_representante`, e **não existir antes na
base**.

> No teste de 20/08 o contato usado já existia como cliente do Clube Nitron e
> tinha CNPJ preenchido. Os campos de kit e marca gravaram certo, mas nenhum
> card nasceu em `Afiliados Jornada` — e não houve como distinguir "a trava de
> revendedor funcionou" de "o W9 não disparou".

| Passo | Esperado |
|---|---|
| Enviar formulário sem escolher kit | W9 vai a `Aceito` com `afil-sem-marca` + notificação |
| Enviar formulário sem CPF | W9 vai a `Respondeu` com `afil-cadastro-incompleto` |
| Enviar formulário completo com kit | W9 vai a `Aceito`; `kit_alocado` tem a referência, `marca_alocada` tem a marca |
| Preencher CNPJ e reenviar | W9 barra, `Status` = `Lost`, aplica `afil-revendedor` |
| **Mover a `Amostra solicitada` com endereço vazio** | W1 devolve a `Aceito`, aplica `afil-devolvido`, e o card **fica em `Aceito`** — não vai a `Recorrente` |
| Preencher endereço e mover de novo | W1 cria card em `Pedidos-Preparacao`, aplica `amostra-afiliado` |
| **Mover o card de Entregas a `Retorno`** | W2b devolve a `Aceito` e o card **fica lá** — nenhum pedido novo, nenhum card em `Recorrente` |
| Mover a `Amostra solicitada` de novo | W1 cria o pedido normalmente |
| Mover o card de Entregas a `Entregue` | W2 move a `Amostra recebida` e manda WhatsApp 3h depois |
| Esperar, com `Wait` em minutos | W3 manda os três toques, notifica, e só então bloqueia |
| **Repetir o W3 com `afil-conteudo-combinado` aplicada** | nenhuma mensagem sai, nenhum bloqueio acontece |
| Criador novo, `data_ultima_amostra` vazia, entrando em `Aceito` | W4 deixa passar. Se for a `Recorrente`, o operador de data está invertido |

As quatro linhas em negrito testam as invariantes I1, I2, I3 e I5. Se qualquer
uma falhar, pare: a tag `afil-devolvido` não está no lugar certo, ou o W4 nasceu
sem o passo 1.

Ao terminar, **apagar o contato de teste**. A tag `afil-teste` serve para achá-lo.

---

## 9. Arquivos relacionados no repositório

- `docs/canvas-workflows.html` — os nove workflows nó por nó, no formato do
  builder, com a configuração exata de cada nó
- `docs/w1-canvas.html` — o mesmo para o W1

| Arquivo | O que tem |
|---|---|
| `ghl-workflows-v3.html` | o mesmo passo a passo, formatado para uma pessoa clicar. Não traz os ids de campo nem a secção de invariantes |
| `ghl-inventario.md` | inventário completo da sub-conta e histórico de recriação de campos |
| `arquitetura.md` | divisão de responsabilidade entre Apify, Supabase, GHL e Sankhya; decisões e pendências |
| `seletor-de-kits.md` | o seletor do formulário, os 20 kits com referência e custo |
| `time/programa-de-afiliados.html` | visão geral para o time, não operacional |
| `ghl-workflows-w0-w9.md` | v2, **superada**. Fica pelos textos de notificação e pelo registro das decisões |
| `../supabase/functions/ghl-sync/` | a edge function que substitui o W0 |
