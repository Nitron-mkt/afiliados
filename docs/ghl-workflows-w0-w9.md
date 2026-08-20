> **ESTE ARQUIVO É A VERSÃO 2 E ESTÁ SUPERADO.**
>
> A versão em uso é `docs/ghl-workflows-v3.html`. Ela reflete: o W0 que não
> deve ser construído, o kit escolhido pelo criador no formulário, a
> referência do ERP como valor gravado, o estágio `Key Account`, e os IDs e
> chaves reais lidos da API.
>
> Este arquivo fica no repo como histórico da decisão, não como instrução.

# Workflows W0 a W9 — guia de execução no GHL

Sub-conta **Nitron** `rZ8y7lzqV7fzxsartaX2`
**Versão 2** — substitui a anterior

---

## O QUE MUDOU NESTA VERSÃO

| # | Mudança | Onde |
|---|---|---|
| 1 | Três colisões entre workflows identificadas e corrigidas | seção `COLISÕES` |
| 2 | W2b devolve o card para `Aceito`, não para `Amostra solicitada` | W2b |
| 3 | Nova tag `afil-devolvido` para impedir o W4 de sequestrar cards devolvidos | W1, W2b, W4 |
| 4 | W3 reestruturado: aviso antes do bloqueio, revisão humana antes do corte | W3 |
| 5 | Nova tag `afil-conteudo-combinado` como critério de saída do W3 | W3 |
| 6 | Textos para o criador escritos: W2 e os três toques do W3 | seção `TEXTOS PARA O CRIADOR` |
| 7 | Notificação do W2b reescrita com checklist de decisão | seção `NOTIFICAÇÕES INTERNAS` |
| 8 | `Wait` de 3 horas no W2 antes de mandar mensagem | W2 |

---

## LEIA ISTO PRIMEIRO

### Sobre os nomes que eu uso

Os nomes de trigger e action do GHL mudam entre versões e entre idioma da conta. Uso os nomes **em inglês**, que é o padrão do Workflow Builder. Se sua conta estiver em português, o nome aparece traduzido mas na mesma posição da lista.

**Se você não achar algum item, me diga quais aparecem na sua lista** e eu aponto o equivalente. Não fique travado tentando adivinhar.

### Tradução dos termos que não existem no GHL

| Nome errado | No GHL é |
|---|---|
| `Move Opportunity` | **`Update Opportunity`** — você escolhe pipeline e stage |
| `Add Tag` | **`Add Contact Tag`** |
| `Update Field` | **`Update Contact Field`** |
| `Remove from Workflow` | **`Remove From Workflow`** |
| notificação interna | é `Internal Notification`, **não** é comentário no card |

**Não existe "Move Opportunity".** Para mover um card você usa `Update Opportunity` e seleciona o stage de destino.

### Onde ficam as coisas

| O que | Caminho |
|---|---|
| Criar workflow | `Automation` → `Workflows` → `+ Create Workflow` → `Start from Scratch` |
| Adicionar trigger | Botão `Add New Trigger` no topo do canvas |
| Adicionar ação | Botão `+` abaixo do trigger |
| Custom Values | `Settings` → `Custom Values` |
| Campos customizados | `Settings` → `Custom Fields` |
| Tags | `Settings` → `Tags` |
| Ligar/desligar | Toggle `Draft` / `Publish` no topo direito |
| Reentrada | Ícone de engrenagem do workflow → `Allow Re-Entry` |
| Canal de WhatsApp | `Settings` → `Phone Numbers` / `WhatsApp` |

### Como preencher condição de campo customizado

No bloco `If/Else`, ao escolher a condição:

1. Categoria → `Custom Fields`
2. Procure o campo pelo nome, ex. `Afiliado — Trilha`
3. Operador → `is` / `is empty` / `is not empty`
4. Valor → digite **exatamente** como está na picklist, sem acento: `Mudanca casa nova`, `Nao`, `Indicacao`

Valor com acento onde a picklist não tem acento é a causa número um de condição que nunca casa.

### Configurações de workflow que resolvem metade dos problemas

Na engrenagem de cada workflow:

| Configuração | Onde usar |
|---|---|
| **`Allow Re-Entry`** — desligado por padrão | Ligue no **W9**. O criador pode reenviar o formulário |
| **`Stop on Response`** | Ligue no **W2** e no **W7**. Ver a ressalva do W3 abaixo |
| **`Time Window`** | Opcional no W7 e no W3. Não manda mensagem às 3h da manhã |

---

## MAPA DO FLUXO

Como um criador atravessa o sistema, do zero à recorrência:

```
CSV importado (tag afil-import)
        │
      [W0] barra revendedor e bloqueado, cria card
        ▼
   MAPEADO ──[W5] rede de segurança, barra de novo
        ▼
  QUALIFICADO
        │
      [W7] sequência de e-mail por trilha (A/B/C/D)
        ▼
   CONTATADO
        │
      [W8] criador responde
        ▼
   RESPONDEU
        │
      [W9] formulário validado: revendedor, bloqueio,
           cadastro completo, marca, tier, fonte
        ▼
    ACEITO ◄──────────────────────┐
        │                         │
        │ (movimento manual)      │ [W2b] amostra voltou
        ▼                         │  ou  [W1] validação falhou
 AMOSTRA SOLICITADA               │
        │                         │
      [W1] valida endereço, kit, marca
        │  └── falhou ────────────┘
        │
        ├──► cria card em Pedidos-Preparacao
        ▼
   (Entregas)
        ├── Entregue ──[W2]──► AMOSTRA RECEBIDA
        └── Retorno  ──[W2b]─► volta para ACEITO
                                  │
   AMOSTRA RECEBIDA               │
        │                         │
      [W3] toque 1 (d3) · toque 2 (d7) · toque 3 (d18)
        │
        ├── postou ──► CONTEUDO PUBLICADO
        │                    │
        │                  [W6] GMV > 0
        │                    ▼
        │               CONVERTIDO ──► RECORRENTE
        │                                  ▲
        └── não postou (d21)               │
                 ▼                    [W4] pediu amostra
      INADIMPLENTE DE CONTEUDO        de novo em 90 dias
      + tag afil-bloqueado
```

---

## COLISÕES — leia antes de publicar qualquer coisa

Três lugares onde um workflow dispara outro sem você mandar. Todas as três produzem o mesmo tipo de erro: frete gasto ou card no stage errado, descoberto semanas depois.

### Colisão 1 — devolver para `Amostra solicitada` reenvia sozinho

O W1 tem trigger `Pipeline Stage Changed` → `Amostra solicitada`. Qualquer coisa que devolva um card para esse stage faz o W1 criar na hora um novo pedido em `Pedidos-Preparacao` — para o mesmo endereço que acabou de falhar. Expedição despacha, pacote volta, frete dobrado, ninguém decidiu nada.

**Correção:** o W2b devolve para `Aceito`. Você corrige o endereço e arrasta para `Amostra solicitada` na mão. Uma etapa manual, zero frete perdido.

### Colisão 2 — devolver para `Aceito` move o card para `Recorrente`

Consequência da correção acima. O W4 tem trigger `Pipeline Stage Changed` → `Aceito` e move para `Recorrente` quem já tem `Data ultima amostra` preenchida. Uma amostra extraviada sempre tem essa data preenchida — o W1 preencheu no envio. Então o card devolvido pelo W2b iria direto para `Recorrente`, como se o criador fosse um afiliado ativo pedindo a segunda amostra.

O mesmo vale para os ramos de rejeição do W1: eles devolvem para `Aceito` e caem na mesma armadilha.

**Correção:** tag `afil-devolvido`.

- O W2b aplica a tag antes de devolver o card
- Os quatro ramos de rejeição do W1 aplicam a tag antes de devolver o card
- O W4 checa a tag no primeiro passo: se existe, remove a tag e encerra

A tag se limpa sozinha. Você não precisa lembrar de nada.

### Colisão 3 — `Stop on Response` não serve para o W3

No W7 o critério de saída é o criador responder, então `Stop on Response` funciona. No W3 o critério de saída é o campo `URL do video` estar preenchido. Se o criador responder "vou gravar sábado", o `Stop on Response` tira ele da sequência mas o campo continua vazio — e ele nunca é bloqueado nem cobrado. Se você deixar desligado, a cobrança continua rodando em cima de quem já te deu uma data.

**Correção:** tag `afil-conteudo-combinado`, aplicada à mão quando alguém combina uma data. Todo `If/Else` do W3 checa essa tag. `Stop on Response` fica **desligado** no W3.

---

# W0 · Importação vira card

**Objetivo:** transformar contato importado por CSV em card no pipeline, já barrando revendedor.

**Trigger:** `Contact Tag`
- Tag: `afil-import`
- Condição: `Tag Added`

**Ações:**

**1.** `If/Else` — "É revendedor?"
- Condição A: `Custom Fields` → `CNPJ` → `is not empty`
- Condição B (operador **OR**): `Custom Fields` → `Codigo Representante` → `is not empty`

- **Ramo SIM:**
  - `Add Contact Tag` → `afil-revendedor`
  - `Update Contact Field` → `Afiliado — Motivo do descarte` = `E revendedor Nitron`
  - `Internal Notification`
  - **fim do ramo** — não cria card nenhum

- **Ramo NÃO:** segue

**2.** `If/Else` — "Está bloqueado?"
- Condição: `Contact Tag` → `is` → `afil-bloqueado`
- SIM → `Internal Notification` → fim
- NÃO → segue

**3.** `Create/Update Opportunity`
- Pipeline: `Afiliados Jornada`
- Stage: `Mapeado`
- Opportunity Name: `{{contact.afiliado__handle_principal}} - {{contact.afiliado__seguidores}}`
- Status: `Open`
- Monetary Value: `0`

**4.** `Add Contact Tag` → `afiliado`

**Por que a trava vem antes de criar o card:** revendedor nunca aparece no kanban. Kanban limpo desde o primeiro dia.

---

# W5 · Rede de segurança da exclusão

**Objetivo:** pegar card criado por qualquer caminho que não seja o W0 — importação antiga, criação manual, outro workflow.

**Trigger:** `Pipeline Stage Changed`
- Pipeline: `Afiliados Jornada`
- Stage: `Mapeado`

> **Verifique se sua conta tem o trigger `Opportunity Created`.** Se tiver, use ele. Se não, use `Pipeline Stage Changed` como acima. Se nenhum dos dois disparar no seu teste, a lógica do W0 já cobre o caminho principal — o W5 é redundância, não deixe ele travar seu progresso.

**Ações:**

**1.** `If/Else` — "É revendedor?" (mesmas condições do W0 passo 1)
- SIM → `Update Contact Field` `Motivo do descarte` = `E revendedor Nitron` → `Update Opportunity` com Status = `Lost` → `Internal Notification` → fim
- NÃO → segue

**2.** `Update Opportunity`
- Pipeline: `Afiliados Jornada`
- Stage: `Qualificado`

---

# W7 · Sequência de e-mail

**Objetivo:** abordar por e-mail, ramificando por trilha.

**⚠️ Deixe em `Draft` até o frete estar medido.** Os e-mails prometem uma comissão que hoje não tem número confiável.

**Trigger:** `Pipeline Stage Changed`
- Pipeline: `Afiliados Jornada`
- Stage: `Qualificado`

**Configuração:** ligue `Stop on Response` na engrenagem.

**Ações:**

**1.** `If/Else` — "Tem e-mail?"
- Condição: `Contact` → `Email` → `is empty`
- SIM → `Add Contact Tag` `afil-sem-email` → fim (fica em `Qualificado`, vai para fila de DM)
- NÃO → segue

**2.** `If/Else` com **4 ramos** — "Qual trilha?"
- Ramo 1: `Custom Fields` → `Afiliado — Trilha` → `is` → `Achadinhos` → `Send Email` (template A1)
- Ramo 2: → `is` → `Mudanca casa nova` → `Send Email` (template B1)
- Ramo 3: → `is` → `Curadoria teca` → `Send Email` (template D1) → `Update Opportunity` para `Contatado` → **fim**, não entra na sequência
- Ramo 4 (`Else`): `Send Email` (template C1) — pega `Nicho organizacao` e trilha vazia

**3.** `Update Opportunity` → Stage `Contatado`

**4.** `Wait` → `4 days`

**5.** `If/Else` — segundo toque conforme trilha (A2, B2 ou C2)

**6.** `Wait` → `5 days`

**7.** terceiro toque (A3, B3 ou C3)

**8.** `Wait` → `5 days`

**9.** `Update Contact Field` → `Afiliado — Motivo do descarte` = `Sem resposta`

**10.** `Update Opportunity` → Status = `Lost`

**Sobre a trilha `Curadoria teca`:** ela sai no passo 2 e não recebe cobrança automática. É negociação com cachê, retorno tratado por pessoa.

**Antes de publicar:** frete medido, comissão real travada, formulário de afiliado criado, W8 no ar, tema do vídeo preenchido à mão por contato, e três envios manuais feitos. O A/B do shell Pessoal contra texto puro sai desses três primeiros.

---

# W8 · Resposta detectada

**Teste o `Stop on Response` do W7 primeiro.** Se funcionar, você só precisa do W8 para mover o card e avisar o time — sem o passo de remoção.

**Trigger:** `Customer Replied`
- Canal: `Email`

**Ações:**

**1.** `If/Else` — "É afiliado?"
- Condição: `Contact Tag` → `is` → `afiliado`
- NÃO → fim (é cliente B2B respondendo, não mexe)
- SIM → segue

**2.** `Update Opportunity`
- Pipeline: `Afiliados Jornada`
- Stage: `Respondeu`

**3.** `Remove From Workflow` → selecione **W7 pelo nome exato**

**4.** `Internal Notification`

**Cuidado:** se você tiver versões do W7 (`W7 v2`, `W7 teste`), o contato pode estar numa versão que o passo 3 não remove. Mantenha um W7 só.

---

# W9 · Formulário recebido

**Objetivo:** a porta de entrada real. Valida e leva para `Aceito`.

**Trigger:** `Form Submitted`
- Form: seu formulário de cadastro de afiliado

**Configuração:** ligue `Allow Re-Entry`. O criador pode reenviar depois de completar dados.

**Ações:**

**1.** `Add Contact Tag` → `afiliado`

**2.** `If/Else` — "É revendedor?" (mesmas condições do W0)
- SIM → `Update Contact Field` `Motivo do descarte` = `E revendedor Nitron` → `Update Opportunity` Status = `Lost` → `Internal Notification` → fim
- NÃO → segue

**3.** `If/Else` — "Está bloqueado?"
- Condição: `Contact Tag` → `is` → `afil-bloqueado`
- SIM → `Internal Notification` → fim
- NÃO → segue

**4.** `If/Else` — "Cadastro completo?"
- Condições, todas com **AND**: `CPF` `is not empty` · `WhatsApp` `is not empty` · `Postal Code` `is not empty` · `Address` `is not empty` · `Bairro` `is not empty`
- **Ramo NÃO:**
  - `Add Contact Tag` → `afil-cadastro-incompleto`
  - `Send Email` (template de dado faltante)
  - `Update Opportunity` → Stage `Respondeu`
  - `Wait` `2 days` → `If/Else` `CPF` `is empty` → segundo toque
  - fim
- **Ramo SIM:**
  - `Remove Contact Tag` → `afil-cadastro-incompleto`
  - segue

**5.** `If/Else` com **4 ramos** — "Qual marca?"
- `Afiliado — Marca alocada` `is` `Nitron` → `Add Contact Tag` `afil-nitron`
- `is` `Mundo UD` → `Add Contact Tag` `afil-mundoud`
- `is` `Teak Brazil` → `Add Contact Tag` `afil-teakbr`
- `Else` → `Add Contact Tag` `afil-sem-marca` + `Internal Notification`

**6.** `Update Contact Field` → `Afiliado — Tier` = `Bronze`

**7.** `If/Else` — `Afiliado — Fonte de captacao` `is empty`
- SIM → `Update Contact Field` → `Fonte de captacao` = `Curadoria`
- NÃO → nada

**8.** `Create/Update Opportunity`
- Pipeline: `Afiliados Jornada` · Stage: `Aceito`
- O `Create/Update` resolve os dois casos: se já existe card, atualiza; se não existe (inbound, indicação), cria

**9.** `Send Email` → boas-vindas

> **Nota de fluxo:** o passo 8 dispara o W4. Para criador novo isso é inofensivo, porque `Data ultima amostra` está vazia. Para criador que reenvia o formulário depois de já ter recebido amostra, o W4 vai mover o card para `Recorrente` — e nesse caso é o comportamento correto.

---

# W1 · Ponte para logística

**Objetivo:** virar o aceite em pedido de amostra no fluxo que já existe.

**Trigger:** `Pipeline Stage Changed`
- Pipeline: `Afiliados Jornada`
- Stage: `Amostra solicitada`

**Ações:**

**1.** `If/Else` — "Dados de envio OK?"
- `CPF` `is not empty` AND `Address` `is not empty` AND `Postal Code` `is not empty` AND `Bairro` `is not empty`
- NÃO → `Add Contact Tag` `afil-devolvido` → `Internal Notification` → `Update Opportunity` Stage `Aceito` → fim
- SIM → segue

**2.** `If/Else` — "Bloqueado?"
- `Contact Tag` `is` `afil-bloqueado`
- SIM → `Add Contact Tag` `afil-devolvido` → `Internal Notification` → `Update Opportunity` Stage `Aceito` → fim
- NÃO → segue

**3.** `If/Else` — "Marca preenchida?"
- `Afiliado — Marca alocada` `is empty`
- SIM → `Add Contact Tag` `afil-devolvido` → `Internal Notification` → `Update Opportunity` Stage `Aceito` → fim
- NÃO → segue

**4.** `If/Else` — "Kit permitido?"
- `Afiliado — Kit alocado` `contains` cada kit aprovado, com **OR** entre eles
- NÃO → `Add Contact Tag` `afil-devolvido` → `Internal Notification` "kit fora da faixa de margem" → `Update Opportunity` Stage `Aceito` → fim
- SIM → segue

**5.** `Create/Update Opportunity`
- Pipeline: `Pedidos-Preparacao`
- Stage: `Pedidos a Liberar`
- Name: `AMOSTRA - {{contact.first_name}} - {{contact.afiliado__kit_alocado}}`

**6.** `Add Contact Tag` → `amostra-afiliado`

**7.** `Remove Contact Tag` → `afil-extravio` *(se você tiver usado a variante com essa tag; com a `afil-devolvido` o W4 já se limpa sozinho)*

**8.** `Update Contact Field`
- `Afiliado — Data ultima amostra` = data de hoje
- `Afiliado — Qtd amostras enviadas` = valor atual + 1

**Lista de kits do passo 4:** depende do frete. Começando só com teca: `Cafe`, `Juta Oval`, `Juta Retangular`, `Churrasco`.

**A ordem importa.** Passos 1 a 4 vêm antes do 5. Invertido, você gera pedido de amostra para endereço vazio e o problema aparece na expedição.

**A tag `afil-devolvido` nos quatro ramos de rejeição é obrigatória.** Sem ela, todo card barrado por validação vai para `Recorrente` em vez de ficar parado em `Aceito` esperando correção. Ver `Colisão 2`.

---

# W2 · Amostra entregue

**Trigger:** `Pipeline Stage Changed`
- Pipeline: `Entregas`
- Stage: `Entregue`

**Configuração:** ligue `Stop on Response`. Se o criador responder, nenhuma outra automação deve atropelar a conversa.

**Ações:**

**1.** `If/Else` — "É amostra de afiliado?"
- `Contact Tag` `is` `amostra-afiliado`
- NÃO → **fim** (é entrega de cliente comum)
- SIM → segue

**2.** `Update Opportunity`
- Pipeline: `Afiliados Jornada` · Stage: `Amostra recebida`

**3.** `Wait` → `3 hours`

**4.** `Send WhatsApp` (ou `Send SMS` se o canal de WhatsApp não estiver configurado) → texto `W2-1` na seção de textos

**A checagem do passo 1 é obrigatória.** Esse trigger dispara em **toda** entrega da sua empresa.

**Por que o `Wait` de 3 horas:** o status "Entregue" costuma cair quando o pacote chega no prédio ou é deixado com o porteiro. Mensagem que chega antes da pessoa ter a caixa na mão soa automática.

---

# W2b · Amostra extraviada

**Trigger:** `Pipeline Stage Changed`
- Pipeline: `Entregas` · Stage: `Retorno`

**Ações:**

**1.** `If/Else` — "É amostra de afiliado?"
- `Contact Tag` `is` `amostra-afiliado`
- NÃO → **fim**
- SIM → segue

**2.** `Add Contact Tag` → `afil-devolvido`

**3.** `Internal Notification` → texto `Amostra voltou` na seção de notificações

**4.** `Update Opportunity`
- Pipeline: `Afiliados Jornada` · Stage: `Aceito`

**Por que `Aceito` e não `Amostra solicitada`:** ver `Colisão 1`. Devolver para `Amostra solicitada` dispara o W1 na hora e gera um segundo despacho para o endereço que acabou de falhar.

**Por que a tag no passo 2:** ver `Colisão 2`. Sem ela, o W4 dispara ao ver a mudança para `Aceito` e move o card para `Recorrente`.

**O que você faz depois:** confirma o endereço com o criador, corrige no contato, arrasta o card para `Amostra solicitada`. O W1 roda com dado limpo.

Sem esse workflow, amostra perdida trava o card para sempre e o criador fica esperando.

---

# W3 · Cobrança de conteúdo

**Trigger:** `Pipeline Stage Changed`
- Pipeline: `Afiliados Jornada` · Stage: `Amostra recebida`

**Configuração:** `Stop on Response` **desligado**. Ver `Colisão 3`. Ligue `Time Window` se o canal for WhatsApp.

**A condição de cobrança**, usada igual nos quatro `If/Else`. Chame de "Precisa cobrar?":
- `Custom Fields` → `Afiliado — URL do video` → `is empty`
- **AND** `Contact Tag` → `is not` → `afil-conteudo-combinado`

> Se sua conta não tiver o operador `is not` para tag, monte como `If/Else` de dois níveis: primeiro checa a tag e encerra se existir, depois checa o campo.

**Ações:**

**1.** `Wait` → `3 days`

**2.** `If/Else` "Precisa cobrar?"
- SIM → `Send WhatsApp` → texto `W3-1`
- NÃO → fim

**3.** `Wait` → `4 days`

**4.** `If/Else` "Precisa cobrar?"
- SIM → `Send Email` → texto `W3-2` (briefing)
- NÃO → fim

**5.** `Wait` → `11 days`

**6.** `If/Else` "Precisa cobrar?"
- SIM → `Send WhatsApp` → texto `W3-3` (aviso final)
- SIM → `Internal Notification` → texto `Bloqueio em 3 dias`
- NÃO → fim

**7.** `Wait` → `3 days`

**8.** `If/Else` "Precisa cobrar?"
- SIM → `Update Opportunity` Stage `Inadimplente de conteudo` → `Add Contact Tag` `afil-bloqueado` → `Update Contact Field` `Motivo do descarte` = `Amostra sem video`
- NÃO → fim

**Total: 21 dias**, igual à versão anterior. A diferença é onde eles caem.

**O que mudou e por quê:**

Na versão 1, o passo 5 era `Wait 14 days` e o evento seguinte era o bloqueio. Quatorze dias de silêncio e a pessoa era queimada sem nunca ter sido avisada. Agora o aviso final sai no dia 18 e o corte no 21.

**A notificação do passo 6 não é opcional.** O campo `URL do video` é preenchido à mão. Se o criador postar e você não colar o link, o W3 bloqueia um afiliado que cumpriu — e você descobre meses depois. Os três dias entre o aviso e o corte existem para você conferir.

**Alternância de canal.** Toque 1 e 3 por WhatsApp, toque 2 por e-mail. Se você mandar nos dois canais em cada toque, o criador recebe seis mensagens em 21 dias e a última é um bloqueio. Os textos existem nas duas versões na seção de textos — escolha um canal por toque.

**No teste, troque os `Wait` para minutos.** Depois volte para dias. Testar isso em 21 dias reais é inviável.

---

# W4 · Trava de reenvio

**Trigger:** `Pipeline Stage Changed`
- Pipeline: `Afiliados Jornada` · Stage: `Aceito`

**Ações:**

**1.** `If/Else` — "Foi devolvido por automação?"
- Condição: `Contact Tag` → `is` → `afil-devolvido`
- **SIM** → `Remove Contact Tag` `afil-devolvido` → **fim**
- NÃO → segue

**2.** `If/Else` — `Afiliado — Data ultima amostra` `is not empty` AND data nos últimos 90 dias
- SIM → `Internal Notification` → `Update Opportunity` Stage `Recorrente` → fim
- NÃO → fim (segue livre para `Amostra solicitada`)

**O passo 1 é novo e é a peça que faz o W2b funcionar.** Ver `Colisão 2`. Ele encerra o workflow e limpa a tag no mesmo movimento, então nada acumula e você não precisa lembrar de remover nada à mão.

> Comparação de data relativa no GHL às vezes não aceita "últimos 90 dias" direto. Se não achar o operador, use `Afiliado — Qtd amostras enviadas` `greater than` `0` como aproximação e trate na mão. Não é perfeito, mas não trava seu progresso.

---

# W6 · Primeira venda

**Trigger:** `Contact Changed`
- Filtro: `Afiliado — GMV acumulado`

**Ações:**

**1.** `If/Else` → `Afiliado — GMV acumulado` `greater than` `0`
- SIM → `Update Opportunity` Stage `Convertido` → `Update Contact Field` `Tier` = `Prata` → `Internal Notification`

**2.** `If/Else` → `greater than` `5000` → `Update Contact Field` `Tier` = `Ouro`

Este é o último a construir. Sem venda acontecendo, não faz nada.

---

# TEXTOS PARA O CRIADOR

Merge fields para conferir em `Settings` → `Custom Fields` antes de colar. Clique no campo e copie a chave exata — `{{contact.afiliado__marca_alocada}}` e `{{contact.bairro}}` são dedução minha a partir do nome do campo, não chave verificada. Campo com chave errada sai vazio e deixa um buraco no meio da frase.

**Regra dos textos:** nunca use o nome do kit na mensagem. "Seu Kit Juta Oval foi entregue" entrega que veio de sistema. "Sua caixa" soa como alguém que sabe o que mandou.

---

## `W2-1` · Amostra chegou · WhatsApp · dia 0

```
Oi {{contact.first_name}}, tudo bem? Aqui é a {{custom_values.nome_responsavel}}, da {{contact.afiliado__marca_alocada}} 🙂

O sistema me avisou que sua caixa foi entregue hoje. Chegou tudo certinho?

Se algo veio quebrado ou faltando, me fala que eu resolvo — e se der tudo certo, me conta depois o que você achou. Fico curiosa mesmo.
```

**Versão e-mail**, se preferir esse canal.
**Assunto:** `sua caixa chegou?`

```
Oi {{contact.first_name}},

O sistema me avisou que sua caixa foi entregue hoje. Chegou tudo
certinho?

Se algo veio quebrado ou faltando, me fala que eu resolvo. E se deu
tudo certo, me conta depois o que você achou — fico curiosa mesmo.

{{custom_values.nome_responsavel}}
```

**Alternativa mais seca**, para usar se o retorno do seu lado vai demorar dias. Assinar com nome de pessoa real só funciona se essa pessoa realmente responder depois.

```
Oi {{contact.first_name}}! Aqui é a {{custom_values.nome_responsavel}}, da {{contact.afiliado__marca_alocada}}.

Sua caixa saiu como entregue agora há pouco. Chegou aí?

Qualquer coisa fora do lugar, é só me chamar por aqui mesmo.
```

---

## `W3-1` · Primeiro toque · dia 3

Este é o **segundo** contato, não o primeiro — o W2 já perguntou se chegou. Por isso não pergunta de novo.

**WhatsApp:**

```
Oi {{contact.first_name}}! Passando pra saber o que você achou do kit de verdade. Já usou?

Pergunto porque sua opinião muda o que eu mando pros próximos criadores — inclusive se for crítica.

E quando você gravar alguma coisa, me manda o link que eu acompanho por aqui.
```

**E-mail** — Assunto: `e aí, o que você achou?`

```
Oi {{contact.first_name}},

Sua caixa chegou faz alguns dias. Queria saber de verdade: o que
você achou?

Pergunto porque a sua opinião muda o que eu mando para os próximos
criadores. Se tiver crítica, é ainda mais útil.

Quando você gravar algo, me manda o link — eu acompanho e reposto
o que fica bom.

Dúvida sobre comissão, link ou como marcar a gente, é só responder
esse e-mail.

{{custom_values.nome_responsavel}}
```

---

## `W3-2` · Segundo toque · dia 7 · briefing

**E-mail** — Assunto: `3 ideias pro vídeo, se o roteiro for o que travou`

```
Oi {{contact.first_name}},

Não sei se o que travou foi a ideia do vídeo, então trouxe três
caminhos que funcionaram bem com outros criadores. Pega o que fizer
sentido e ignora o resto — quem conhece sua audiência é você.

1. O desembalo honesto
   Abre a caixa na câmera e fala o que passa na cabeça, sem roteiro.
   Funciona porque a reação real não dá pra atuar.

2. O antes e depois
   Grava o espaço como ele está hoje, monta, grava de novo. É o
   formato que mais converte, porque mostra o resultado, não o
   produto.

3. O uso de verdade
   Uma cena curta do kit sendo usado num dia normal. Sem produção.
   Esse é o que mais gera comentário do tipo "onde comprou?".

O que a gente pede em qualquer um dos três:
• marcar o perfil da marca
• link na bio ou na vitrine
• não prometer preço ou prazo, porque isso muda e a cobrança
  sobra pra você

Sua comissão é de {{contact.afiliado__comissao_}}% e vale para toda
venda pelo seu link — não só a do primeiro vídeo. É por isso que o
primeiro vídeo importa: ele é o que abre a torneira.

Se o que travou foi outra coisa — tempo, luz, o que for — me
responde que eu ajudo a resolver.

{{custom_values.nome_responsavel}}
```

**WhatsApp curto**, se você preferir manter o toque 2 nesse canal:

```
Oi {{contact.first_name}}! Te mandei um e-mail com 3 ideias de roteiro, caso o que esteja travando seja isso.

Se for outra coisa — tempo, luz, ideia — me fala aqui que eu dou uma mão.
```

---

## `W3-3` · Terceiro toque · dia 18 · aviso final

**Este texto não existia na versão 1.** Ele é a diferença entre bloquear alguém e avisar antes.

**WhatsApp:**

```
Oi {{contact.first_name}}, sem cobrança nenhuma: o vídeo ainda faz sentido pra você?

Se não rolar agora, tudo bem — só me avisa que eu acerto aqui do meu lado. E se rolar, me diz até quando que eu te espero.

Prefiro saber do que ficar imaginando.
```

**E-mail** — Assunto: `ainda faz sentido?`

```
Oi {{contact.first_name}},

Faz umas duas semanas e meia que a amostra chegou e o vídeo não
saiu. Não estou cobrando — estou perguntando.

Se mudou de ideia, se não deu tempo, se o kit não combinou com seu
conteúdo: qualquer um desses é uma resposta boa. Só me diz qual, que
eu acerto aqui do meu lado.

Se ainda vai sair, me manda uma data e eu te espero.

{{custom_values.nome_responsavel}}
```

**Quando alguém responder com uma data:** aplique a tag `afil-conteudo-combinado` no contato. Isso tira ele do W3 sem tirar do radar.

---

# TEXTOS DAS NOTIFICAÇÕES INTERNAS

Todas são `Internal Notification`, tipo `Email`, destinatário = você. **O criador não recebe nada disso.**

### Revendedor detectado (W0, W5, W9)
**Assunto:** `Revendedor tentou entrar como afiliado: {{contact.first_name}}`
```
{{contact.first_name}} caiu na trava de revendedor.

CNPJ: {{contact.cpfcnpj}}
Codigo representante: {{contact.codigo_representante}}
Handle: {{contact.afiliado__handle_principal}}

Marcado como Lost. Vale uma ligacao: pode ser cliente querendo
divulgar, o que e outra conversa.
```

### Bloqueado tentou entrar (W0, W9)
**Assunto:** `Bloqueado tentou se cadastrar: {{contact.first_name}}`
```
{{contact.first_name}} esta com a tag afil-bloqueado.

Handle: {{contact.afiliado__handle_principal}}
Amostras enviadas: {{contact.afiliado__qtd_amostras_enviadas}}
Ultima amostra: {{contact.afiliado__data_ultima_amostra}}
Motivo: {{contact.afiliado__motivo_do_descarte}}

Nenhuma acao automatica. Decidir manualmente se libera.
```

### Sem marca (W9)
**Assunto:** `Afiliado sem marca alocada: {{contact.first_name}}`
```
{{contact.first_name}} completou o cadastro sem Marca alocada.

Handle: {{contact.afiliado__handle_principal}}
Kit alocado: {{contact.afiliado__kit_alocado}}
Trilha: {{contact.afiliado__trilha}}

Card seguiu para Aceito com a tag afil-sem-marca, mas a amostra
NAO pode ser despachada: sem marca a nota sai errada no Sankhya.

1. Preencher Marca alocada
2. Conferir se bate com o kit (Cafe, Juta, Churrasco = Teak Brazil;
   organizacao e cozinha = Mundo UD)
3. Aplicar a tag de marca e remover afil-sem-marca

Se este aviso chega sempre, o problema esta na planilha de
importacao.
```

### Dados de envio incompletos (W1)
**Assunto:** `Amostra barrada por dados incompletos: {{contact.first_name}}`
```
{{contact.first_name}} chegou em Amostra solicitada sem dados
completos. Card devolvido para Aceito.

CPF: {{contact.cpf}}
Endereco: {{contact.address1}}
CEP: {{contact.postal_code}}
WhatsApp: {{contact.whatsapp}}

Corrigir o que falta e arrastar o card de volta para Amostra
solicitada.
```

### Kit fora da faixa (W1)
**Assunto:** `Kit nao permitido: {{contact.afiliado__kit_alocado}}`
```
{{contact.first_name}} esta com kit fora da faixa de margem.

Kit: {{contact.afiliado__kit_alocado}}
Comissao no cadastro: {{contact.afiliado__comissao_}}%

Card devolvido para Aceito. Trocar o kit por um da lista aprovada
e arrastar de volta para Amostra solicitada.
```

### Amostra voltou (W2b) — **reescrita**
**Assunto:** `Amostra voltou: {{contact.first_name}} ({{contact.afiliado__kit_alocado}})`
```
A amostra de {{contact.first_name}} voltou para a base. Card
devolvido para Aceito.

QUEM E
Handle: {{contact.afiliado__handle_principal}}
Seguidores: {{contact.afiliado__seguidores}}
Marca: {{contact.afiliado__marca_alocada}}
Kit: {{contact.afiliado__kit_alocado}}
Amostras ja enviadas: {{contact.afiliado__qtd_amostras_enviadas}}

O QUE VOLTOU
Rastreio: {{contact.afiliado__codigo_de_rastreio}}
Data do ultimo envio: {{contact.afiliado__data_ultima_amostra}}

ENDERECO CADASTRADO
{{contact.address1}}
{{contact.bairro}} - CEP {{contact.postal_code}}
WhatsApp: {{contact.whatsapp}}

ANTES DE REENVIAR
1. Ver o motivo da devolucao no rastreio. Endereco errado, ausente
   e recusado exigem tratamentos diferentes.
2. Confirmar o endereco com o criador pelo WhatsApp. Reenviar para
   o mesmo endereco que falhou e jogar frete fora.
3. Se Amostras ja enviadas for 2 ou mais, nao reenviar sem decisao
   sua. Duas amostras perdidas e padrao, nao azar.
4. Corrigir o endereco no contato ANTES de arrastar o card para
   Amostra solicitada.

O criador esta esperando e nao sabe que voltou. Vale um WhatsApp
hoje mesmo, mesmo sem a solucao pronta.
```

### Bloqueio em 3 dias (W3, passo 6) — **nova**
**Assunto:** `Vou bloquear {{contact.first_name}} em 3 dias — confere se ele postou`
```
{{contact.first_name}} recebeu o aviso final. Se o campo URL do
video continuar vazio em 3 dias, ele vai para Inadimplente de
conteudo e leva a tag afil-bloqueado.

Handle: {{contact.afiliado__handle_principal}}
Perfil: {{contact.afiliado__url_do_perfil}}
Kit: {{contact.afiliado__kit_alocado}}
Amostra recebida em: {{contact.afiliado__data_ultima_amostra}}

DUAS COISAS PARA CONFERIR AGORA
1. Abrir o perfil dele. Se o video existe e voce nao colou o link,
   o sistema vai bloquear alguem que cumpriu.
2. Se ele respondeu combinando uma data, aplicar a tag
   afil-conteudo-combinado. Isso tira ele do W3 sem descartar.

Nao fazer nada tambem e uma decisao valida. Em 3 dias o bloqueio
acontece sozinho.
```

### Afiliado respondeu (W8)
**Assunto:** `Afiliado respondeu: {{contact.first_name}} ({{contact.afiliado__seguidores}} seg)`
```
{{contact.first_name}} respondeu ao e-mail.

Handle: {{contact.afiliado__handle_principal}}
Perfil: {{contact.afiliado__url_do_perfil}}
Seguidores: {{contact.afiliado__seguidores}}
Engajamento: {{contact.afiliado__engajamento_}}%
Trilha: {{contact.afiliado__trilha}}
Kit sugerido: {{contact.afiliado__kit_alocado}}
Vitrine: {{contact.afiliado__vitrine}}

Responder em ate 4 horas.
```

### Reenvio detectado (W4)
**Assunto:** `Afiliado recorrente pedindo amostra: {{contact.first_name}}`
```
{{contact.first_name}} voltou para Aceito e ja recebeu amostra nos
ultimos 90 dias.

Amostras enviadas: {{contact.afiliado__qtd_amostras_enviadas}}
Ultima amostra: {{contact.afiliado__data_ultima_amostra}}
GMV acumulado: {{contact.afiliado__gmv_acumulado}}
Tier: {{contact.afiliado__tier}}

Card movido para Recorrente. Segunda amostra so com decisao sua,
e o GMV e o criterio: se ele vendeu, vale. Se nao vendeu, a
segunda amostra e frete jogado fora.
```

### Primeira venda (W6)
**Assunto:** `PRIMEIRA VENDA: {{contact.first_name}}`
```
{{contact.first_name}} fez a primeira venda.

Handle: {{contact.afiliado__handle_principal}}
GMV: {{contact.afiliado__gmv_acumulado}}
Kit: {{contact.afiliado__kit_alocado}}
Video: {{contact.afiliado__url_do_video}}

Tier subiu para Prata. Postar na comunidade.
```

---

# ORDEM DE CONSTRUÇÃO

| # | Workflow | Publicar? |
|---|---|---|
| 1 | **W0** | sim |
| 2 | **W9** | sim |
| 3 | **W1** | só depois de definir a lista de kits |
| 4 | **W4** | **antes do W2b** — ele precisa da trava do passo 1 |
| 5 | **W2** + **W2b** | sim |
| 6 | **W3** | sim |
| 7 | **W5** | sim |
| 8 | **W8** | sim |
| 9 | **W7** | **deixe em Draft** |
| 10 | **W6** | sim |

**A mudança de ordem é importante.** Na versão 1 o W4 vinha depois do W2b. Se você publicar o W2b sem a trava do W4 já no lugar, a primeira amostra extraviada vai para `Recorrente` e você não vai entender por quê.

O W7 é o único que faz promessa para fora. Fica em `Draft` até o frete estar medido.

---

# TAGS NECESSÁRIAS

Você já tem: `afiliado` · `afil-bloqueado` · `amostra-afiliado` · `afil-nitron` · `afil-mundoud` · `afil-teakbr`

| Tag | Usada em | Nova? |
|---|---|---|
| `afil-import` | W0 (é o trigger) | |
| `afil-sem-email` | W7 passo 1 | |
| `afil-revendedor` | W0 passo 1 | |
| `afil-sem-marca` | W9 passo 5 | |
| `afil-cadastro-incompleto` | W9 passo 4 | |
| `afil-teste` | contato de teste, para não contaminar relatório | |
| **`afil-devolvido`** | W1 ramos de rejeição · W2b passo 2 · W4 passo 1 | **sim** |
| **`afil-conteudo-combinado`** | W3, aplicada à mão | **sim** |

**`afil-devolvido` se limpa sozinha** — o W4 remove no passo 1. Você nunca aplica nem remove essa tag à mão.

**`afil-conteudo-combinado` é 100% manual.** Aplique quando alguém combinar uma data. Remova quando o vídeo sair ou quando a data passar sem entrega — se esquecer de remover, o criador nunca é cobrado nem bloqueado.

---

# CAMPOS NECESSÁRIOS

**`Bairro`** — tipo TEXT, sem prefixo de afiliado, serve para a conta toda. Sem ele o W1 e o W9 não conseguem validar endereço, e o Sankhya não emite a nota. **Ainda pendente.**

Conferir as chaves de merge field destes, que usei nos textos por dedução:
- `Afiliado — Marca alocada` → usei `{{contact.afiliado__marca_alocada}}`
- `Bairro` → usei `{{contact.bairro}}`
- `Afiliado — Codigo de rastreio` → usei `{{contact.afiliado__codigo_de_rastreio}}`

---

# TESTE DE PONTA A PONTA

Crie um contato de teste com a tag `afil-teste` e percorra:

| Passo | Esperado |
|---|---|
| Adicionar tag `afil-import` | W0 cria card em `Mapeado` |
| Preencher `CNPJ` e repetir | W0 barra e não cria card |
| Mover para `Qualificado` | W7 dispara (se publicado) |
| Responder o e-mail | W8 move para `Respondeu` e tira do W7 |
| Enviar formulário sem CPF | W9 vai para `Respondeu` com tag de incompleto |
| Enviar formulário completo | W9 vai para `Aceito` |
| Mover para `Amostra solicitada` **com endereço vazio** | W1 devolve para `Aceito`, aplica `afil-devolvido`, e o card **fica em `Aceito`** — não vai para `Recorrente` |
| Preencher endereço e mover de novo | W1 cria card em `Pedidos-Preparacao` |
| Mover o card de Entregas para `Retorno` | W2b devolve para `Aceito` e o card **fica lá** — nenhum pedido novo em `Pedidos-Preparacao`, nenhum card em `Recorrente` |
| Mover para `Amostra solicitada` de novo | W1 cria o pedido normalmente |
| Mover o card de Entregas para `Entregue` | W2 move para `Amostra recebida` e manda WhatsApp 3h depois |
| Esperar (com `Wait` em minutos) | W3 manda os três toques, notifica você, e só então bloqueia |
| Repetir o W3 com a tag `afil-conteudo-combinado` aplicada | nenhuma mensagem sai, nenhum bloqueio acontece |

**As três linhas em negrito são o teste das colisões.** Se qualquer uma falhar, pare e me diga o que aconteceu — é sinal de que a tag `afil-devolvido` não está no lugar certo.

Ao terminar, **apague o contato de teste**. Tag `afil-teste` serve para achá-lo depois.
