# Seletor de kits no formulario

Arquivo: `forms/seletor-kits.html`. Bloco de HTML customizado para o
formulario de cadastro de afiliado no GHL. Grava dois campos:
`afiliado__kit_alocado` e `afiliado__marca_alocada`.

Hoje traz **tres kits**: Churrasco, Micro-ondas e Frasqueira de Medicamentos.
A tabela com os 20 kits da planilha esta no fim deste arquivo, para copiar de
la quando abrir mais.

## Por que precisa de campo customizado

O bloco de HTML **nao envia nada** por conta propria. Ele nao faz parte do
formulario: e um pedaco de pagina que o GHL desenha no meio dele. Quando o
criador aperta Enviar, o GHL junta o valor dos **campos dele** e manda — e
ignora completamente qualquer HTML que a gente tenha colado ali.

Entao o desenho e este:

```
o criador clica num card
        v
o JS acha o campo REAL do GHL no DOM  (afiliado__kit_alocado)
        v
escreve o valor nele e dispara input + change
        v
o campo real esconde, para nao aparecer duplicado
        v
Enviar  ->  o GHL manda o campo real, como manda qualquer outro
```

Ou seja: os cards sao a interface, e o campo customizado e o que de fato
viaja. Sem o campo no formulario, o clique nao tem onde pousar e nada e
gravado — o criador escolhe, aperta enviar, e o kit chega vazio no contato.

## Instalacao

**1. Crie as duas opcoes no campo, se ainda nao existirem.**
`Settings` -> `Custom Fields` -> `Afiliado — Kit alocado`. Ele esta como TEXT
hoje; mude para `SINGLE_OPTIONS` e cadastre as opcoes **exatamente** assim:

```
KIT CHURRASCO
KIT MICRO-ONDAS
KIT MEDICAMENTO
```

Maiuscula, com acento onde tem, sem espaco sobrando. Estes textos tem que ser
identicos ao `valor` de cada kit no arquivo. Valor que nao existe na picklist
entra vazio, sem erro e sem aviso — e a causa numero um de campo que "nao
grava".

O `Afiliado — Marca alocada` ja e `SINGLE_OPTIONS` e ja tem Nitron, Mundo UD
e Teak Brazil. Nao precisa mexer.

**2. Ponha os dois campos no formulario.**
No editor do formulario, arraste `Afiliado — Kit alocado` e
`Afiliado — Marca alocada` para dentro dele. Podem ficar em qualquer posicao:
o script vai esconde-los assim que achar. Eles precisam **existir** no
formulario, nao ficar visiveis.

**3. Cole o bloco.**
Adicione um elemento `Custom HTML` (ou `Custom Code`, depende da versao) e
cole o arquivo `forms/seletor-kits.html` inteiro. Ponha o bloco **acima** dos
campos de endereco, para o criador escolher o kit antes de digitar CPF e CEP.

**4. Publique e teste.**
Abra o formulario, clique num kit, preencha o resto, envie. No contato criado,
confira `Afiliado — Kit alocado` e `Afiliado — Marca alocada`.

## Se nao gravar

Troque `DEBUG` para `true` no topo do script e recarregue. Aparece um painel
dizendo quantos campos ele achou, com que `name`, e se conseguiu escrever.

Tres leituras possiveis:

| O painel diz | Significa | O que fazer |
|---|---|---|
| `Campos de kit encontrados: 0` | o campo nao esta no formulario, ou a chave e outra | conferir o passo 2; se estiver la, me mandar o print |
| `encontrados: 1` e `Gravou: NÃO` | achou o campo mas o valor nao casa com nenhuma opcao da picklist | conferir o passo 1, caractere por caractere |
| `Gravou: sim` mas chega vazio no contato | o GHL nao esta lendo o campo escondido | por `ESCONDER_ORIGINAL = false` e testar de novo |

O ponto fragil esta isolado numa funcao so: `acharCampos()` procura por
`[name*=chave]`, `[id*=chave]` e `[data-q*=chave]`. Se o GHL mudar a marcacao
do formulario, e ali que se corrige — em um lugar, nao espalhado.

## Decisoes que o codigo carrega

**A marca sai do kit, dentro do proprio seletor.** Cada kit tem `marca` fixa
na lista. Isso elimina o `If/Else` por kit que o W9 precisaria ter: quando o
formulario e enviado, os dois campos ja vem preenchidos e coerentes. A tag
`afil-sem-marca` do W9 passo 5 deixa de ser o caminho normal e volta a ser o
que devia: detector de anomalia.

**`setNativo()` usa o setter do prototype, nao `el.value =`.** Campo
controlado por framework ignora atribuicao direta — o valor aparece na tela e
nao chega no submit. E a causa numero um de "o campo nao grava" em widget
colado dentro de form builder.

**`MutationObserver` reaplica a escolha.** O formulario do GHL monta os campos
depois deste script rodar. Sem o observer, quem clica rapido perde a escolha.
Se em 2,5s os campos nao aparecerem, o painel avisa em vez de falhar calado.

**`ESCONDER_ORIGINAL` sobe na arvore com freio.** Ele so sobe enquanto o
ancestral contiver apenas aquele campo, entao nao existe o risco de esconder
meio formulario por causa de um seletor generoso.

**Radio de verdade, nao `div` com `onclick`.** Teclado, `Tab`, leitor de tela e
`:focus-visible` funcionam sem codigo extra.

## Ajustes do dia a dia

| Quero | Faco |
|---|---|
| tirar um kit do formulario | `ativo: false` na lista `KITS` |
| por foto num kit | preencher `foto` com a URL |
| trocar a marca de um kit | editar `marca` na lista |
| mudar o agrupamento | editar `grupo` (`mesa`, `cozinha`, `casa`) |

## Fotos

Nao ha foto nenhuma na planilha de origem, entao os tres kits estao com
`foto: ""`. Sem URL, o card mostra um bloco tramado com o nome do kit — parece
intencional em vez de quebrado, e o formulario funciona hoje.

Vale por foto antes de publicar: o kit e a coisa que o criador esta escolhendo,
e nome de SKU nao vende. `KIT TRAVESSA CANELADA OVAL` nao diz nada; a foto diz.

## Os 20 kits da planilha, com custo

Os tres em uso hoje estao em **negrito**. Para abrir mais, copie nome, SKU e
marca daqui para a lista `KITS` do arquivo, e cadastre a opcao na picklist.

Extraido de `NOVOS_PRODUTOS_ECOMMERCE_TIKTOK03.xlsx`, somando os itens de cada
kit na aba `Preços` (coluna CUSTO DIRETO NET).

| Kit | SKU | Marca (inferida) | Custo | Itens |
|---|---|---|---|---|
| Café | 902.K01.M00 | Teak Brazil | 70,67 | 2 |
| Juta Retangular | 903.K01.003 | Teak Brazil | 61,83 | 3 |
| Juta Oval | 904.K01.003 | Teak Brazil | 61,44 | 2 |
| **Churrasco** | 905.K01.999 | Teak Brazil | 64,43 | 2 |
| Lavanderia | 911.K01.003 | Mundo UD | 55,87 | 3 |
| Cozinha Flat | 905.K01.003 | Mundo UD | 48,14 | 4 |
| Ferramenta | 906.K01.999 | Nitron | 43,87 | 2 |
| Cozinha Rattan | 913.K01.003 | Mundo UD | 38,27 | 5 |
| POP | 911.K01.001 | Mundo UD | 37,53 | 2 |
| Make | 907.K01.001 | Mundo UD | 35,01 | 3 |
| Banheiro | 906.K01.003 | Mundo UD | 31,64 | 5 |
| Modular 10 Peças | 909.K01.001 | Mundo UD | 31,07 | 3 |
| UltraForte | 910.K01.002 | Mundo UD | 29,69 | 3 |
| **Medicamento** | 907.K01.999 | Mundo UD | 29,30 | 3 |
| Limpeza | 908.K01.999 | Mundo UD | 25,18 | 4 |
| **Micro-ondas** | 914.K01.002 | Mundo UD | 23,69 | 4 |
| Geladeira | 910.K01.001 | Mundo UD | 23,05 | 3 |
| NitronBox | 912.K01.002 | Nitron | 20,54 | 1 |
| Travessa Canelada Oval | 909.K01.002 | Mundo UD | 15,71 | 3 |
| Guarda-Roupa | 908.K01.001 | Mundo UD | 10,55 | 2 |

**A marca e inferencia minha**, pela regra do guia (`Cafe, Juta, Churrasco =
Teak Brazil; organizacao e cozinha = Mundo UD`) mais o nome dos produtos:
`NITRONFORT` e `NITRONBOX` levaram os dois kits para Nitron. Conferir antes de
publicar — marca errada sai como nota errada no Sankhya.

## Tres coisas que a planilha revelou

**A margem e formula, nao observacao.** Os 20 kits dao 49,0% de margem, iguais
ate a primeira decimal. Isso e `preco = custo / 0,51`, nao preco de mercado.
Entao margem **nao** serve para escolher kit de amostra. O que diferencia e o
custo, que vai de R$ 10,55 a R$ 70,67 — quase 7 vezes.

**A coluna PESO esta vazia nos 20 kits.** E esse o bloqueio do frete, e nao
falta de conta: sem peso nao ha calculo. Sao 20 celulas na aba `Medidas`.

**Um SKU divergente.** `KIT ULTRAFORTE` e `910.K01.002` na aba `Kits` e
`910.K01.003` na aba `Medidas`. Um dos dois esta errado.

Vale notar tambem que a numeracao reinicia: `905` a `911` aparecem duas vezes,
com sufixo diferente (`905.K01.999` Churrasco e `905.K01.003` Cozinha Flat).
Pode ser proposital, se o sufixo codifica variacao. Se nao for, sao sete pares
para conferir.
