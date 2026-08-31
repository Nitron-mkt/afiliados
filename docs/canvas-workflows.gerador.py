# -*- coding: utf-8 -*-
"""Gera docs/canvas-workflows.html reaproveitando o sistema visual do w1-canvas."""
import io, re, os

RAIZ = '/home/user/afiliados'

# ---------- helpers de canvas ----------
def no(num, ic, tit, sub, destaque=False):
    cls = 'no destaque' if destaque else 'no'
    return ('<div class="%s"><span class="num">%s</span>'
            '<span class="ic ic-%s">%s</span><span class="corpo">'
            '<span class="tit">%s</span><span class="sub">%s</span>'
            '</span></div>') % (cls, num, ic[0], ic[1], tit, sub)

TRIGGER = ('trigger', '⇄'); COND = ('cond', '{}'); BRANCH = ('branch', '⑂')
OPP = ('opp', '◎');     TAG = ('tag', '#');  CAMPO = ('campo', '✎')
NOTIF = ('notif', '✉');  MSG = ('msg', '➤');  ESPERA = ('espera', '◷')
REMOVE = ('remove', '⊖')

def lig(mais=True):
    return '<div class="lig"></div><div class="mais">+</div><div class="lig"></div>' if mais \
           else '<div class="lig"></div>'

def fim(txt='FIM'):
    return '<div class="lig"></div><div class="fim">%s</div>' % txt

def idem(html):
    return '<div class="idem">%s</div>' % html

def ramo(*partes):
    return '<div class="ramo"><div class="lig"></div>%s</div>' % ''.join(partes)

def split(*ramos):
    return ('<div class="lig"></div><div class="barra"></div>'
            '<div class="ramos">%s</div>') % ''.join(ramos)

def canvas(*partes, **kw):
    rot = kw.get('rotulo')
    cab = '<div class="canvas-rot">%s</div>' % rot if rot else ''
    return '<div class="canvas">%s<div class="pista">%s</div></div>' % (cab, ''.join(partes))

def tabela(linhas, cab=('Nº', 'Nó', 'Configuração exata')):
    tr = ''.join('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % l for l in linhas)
    return ('<div class="rolagem"><table><thead><tr>%s</tr></thead>'
            '<tbody>%s</tbody></table></div>') % (
            ''.join('<th>%s</th>' % c for c in cab), tr)

def nota(rotulo, *paras, **kw):
    tipo = kw.get('tipo', '')
    cls = 'nota ' + tipo if tipo else 'nota'
    return '<div class="%s"><span class="rotulo">%s</span>%s</div>' % (
        cls, rotulo, ''.join('<p>%s</p>' % p for p in paras))

def c(t):   return '<code>%s</code>' % t
def en(t):  return '<code class="en">%s</code>' % t
def m(t):   return '<span class="mono">%s</span>' % t
def b(t):   return '<b>%s</b>' % t

# ======================================================================
# W9
# ======================================================================
w9_tronco = canvas(
  no(1, TRIGGER, 'Formulário Enviado',
     'Formulário is %s<br>%s <b>ligado</b>' % (b('cadastro de afiliado'), en('Allow Re-Entry')),
     destaque=True),
  lig(),
  no(2, TAG, 'Adicionar tag de contato', b('afiliado')),
  split(
    ramo(no(3, COND, 'Condition', 'Tem algo que barra?')),
  ),
  rotulo=None
)

w9_split = canvas(
  no(3, COND, 'Condition', 'Tem algo que barra? — <b>três</b> Branch'),
  split(
    ramo(
      no(4, BRANCH, 'Branch · Revendedor',
         'If %s is not empty<br><b>OR</b> %s is not empty' % (m('CNPJ'), m('Codigo Representante'))),
      lig(), no(5, CAMPO, 'Atualizar campo de contato',
                'Motivo do descarte = <b>E revendedor Nitron</b>'),
      lig(), no(6, TAG, 'Adicionar tag de contato', b('afil-revendedor')),
      lig(), no(7, OPP, 'Criar ou atualizar oportunidade', 'Status = <b>Lost</b>'),
      lig(), no(8, NOTIF, 'Notificação interna', '"Revendedor tentou se cadastrar"'),
      fim()),
    ramo(
      no(9, BRANCH, 'Branch · Bloqueado', 'If %s incluir %s' % (m('Tags'), b('afil-bloqueado'))),
      lig(), no(10, NOTIF, 'Notificação interna', '"Bloqueado tentou se recadastrar"'),
      fim()),
    ramo(
      no(11, BRANCH, 'Branch · Cadastro incompleto',
         'If %s is empty<br><b>OR</b> %s is empty<br><b>OR</b> %s is empty<br>'
         '<b>OR</b> %s is empty<br><b>OR</b> %s is empty'
         % (m('CPF'), m('WhatsApp'), m('Postal Code'), m('Address'), m('Bairro'))),
      lig(), no(12, TAG, 'Adicionar tag de contato', b('afil-cadastro-incompleto')),
      lig(), no(13, MSG, 'Enviar e-mail', 'pede o dado que falta'),
      lig(), no(14, OPP, 'Criar ou atualizar oportunidade', 'Afiliados Jornada → <b>Respondeu</b>'),
      lig(), no(15, ESPERA, 'Esperar', b('2 dias')),
      lig(), no(16, COND, 'Condition', 'If %s is empty → segundo toque' % m('CPF')),
      fim()),
    ramo(
      no(17, BRANCH, 'None', 'passou pelas três'),
      lig(), no(18, REMOVE, 'Remover tag de contato', b('afil-cadastro-incompleto')),
      lig(), no(19, CAMPO, 'Atualizar campo de contato', 'Tier = <b>Bronze</b>'),
      lig(), no(20, OPP, 'Criar ou atualizar oportunidade', 'Afiliados Jornada → <b>Aceito</b>'),
      lig(), no(21, MSG, 'Enviar e-mail', 'boas-vindas'),
      lig(), idem('continua no canvas abaixo<br><b>nó 22</b>')),
  ),
  rotulo='O tronco e os quatro caminhos'
)

w9_marca = canvas(
  no(22, COND, 'Condition', 'Qual marca? — <b>três</b> Branch'),
  split(
    ramo(
      no(23, BRANCH, 'Branch · Nitron', 'If %s is <b>Nitron</b>' % m('Marca alocada')),
      lig(), no(24, TAG, 'Adicionar tag de contato', b('afil-nitron')),
      fim()),
    ramo(
      no(25, BRANCH, 'Branch · Mundo UD', 'If %s is <b>Mundo UD</b>' % m('Marca alocada')),
      lig(), idem('<b>igual ao nó 24</b><br>tag <b>afil-mundoud</b>'),
      fim()),
    ramo(
      no(27, BRANCH, 'Branch · Teak Brazil', 'If %s is <b>Teak Brazil</b>' % m('Marca alocada')),
      lig(), idem('<b>igual ao nó 24</b><br>tag <b>afil-teakbr</b>'),
      fim()),
    ramo(
      no(29, BRANCH, 'None', 'nenhuma das três'),
      lig(), no(30, TAG, 'Adicionar tag de contato', b('afil-sem-marca')),
      lig(), no(31, NOTIF, 'Notificação interna', '"Formulário sem kit escolhido"'),
      fim()),
  ),
  rotulo='Continuação do ramo None — nós 22 a 31'
)

W9 = dict(
  id='w9', curto='a porta de entrada — todo criador passa aqui', nome='W9', titulo='Formulário recebido',
  papel='A porta de entrada. Todo criador que chega em <code>Aceito</code> passa por aqui.',
  gatilho='%s → formulário de cadastro de afiliado' % en('Form Submitted'),
  config='%s <b>ligado</b>' % en('Allow Re-Entry'),
  nos=31, estado='não existe',
  canvases=[w9_tronco.replace('<div class="lig"></div><div class="barra"></div><div class="ramos"><div class="ramo"><div class="lig"></div>' + no(3, COND, 'Condition', 'Tem algo que barra?') + '</div></div>', ''), w9_split, w9_marca],
  tab=[
    ('1','Formulário Enviado','Formulário is o de cadastro de afiliado. Ligue ' + en('Allow Re-Entry') + ' — criador que corrige o cadastro reenvia'),
    ('2','Adicionar tag',c('afiliado')),
    ('3','Condition','Adicione <strong>três</strong> Branch, nesta ordem. O ' + en('None') + ' o GHL cria sozinho'),
    ('4','Branch 1',c('CNPJ')+' is not empty <strong>OR</strong> '+c('Codigo Representante')+' is not empty'),
    ('5','Atualizar campo',c('Afiliado — Motivo do descarte')+' = '+c('E revendedor Nitron')),
    ('6','Adicionar tag',c('afil-revendedor')),
    ('7','Atualizar oportunidade',en('Status')+' = '+en('Lost')+'. Não mexa no estágio'),
    ('8','Notificação interna','tipo '+en('Email')+'. Assunto: '+c('Revendedor no formulário de afiliado: {{contact.first_name}}')),
    ('9','Branch 2',c('Tags')+' incluir '+c('afil-bloqueado')),
    ('10','Notificação interna','assunto: '+c('Bloqueado tentou recadastro: {{contact.first_name}}')),
    ('11','Branch 3','cinco condições com <strong>OR</strong>, todas <code>is empty</code>: '+c('CPF')+' · '+c('WhatsApp')+' · '+en('Postal Code')+' · '+en('Address')+' · '+c('Bairro')),
    ('12','Adicionar tag',c('afil-cadastro-incompleto')),
    ('13','Enviar e-mail','pede só o que falta. Não repita o formulário inteiro'),
    ('14','Criar ou atualizar oportunidade',c('Afiliados Jornada')+' → '+c('Respondeu')),
    ('15','Esperar',c('2 dias')),
    ('16','Condition','um Branch: '+c('CPF')+' is empty → segundo e-mail. '+en('None')+' → FIM'),
    ('17','None','não configura nada. É quem passou pelas três'),
    ('18','Remover tag',c('afil-cadastro-incompleto')+' — quem corrigiu no reenvio tem que sair da lista'),
    ('19','Atualizar campo',c('Afiliado — Tier')+' = '+c('Bronze')),
    ('20','Criar ou atualizar oportunidade',c('Afiliados Jornada')+' → '+c('Aceito')+'. <strong>Este nó dispara o W4</strong>'),
    ('21','Enviar e-mail','boas-vindas'),
    ('22','Condition','Adicione <strong>três</strong> Branch. O '+en('None')+' vira o ramo "sem marca"'),
    ('23–28','Branch 1, 2 e 3',c('Afiliado — Marca alocada')+' <code>is</code> <code>Nitron</code> / <code>Mundo UD</code> / <code>Teak Brazil</code> → tag '+c('afil-nitron')+' / '+c('afil-mundoud')+' / '+c('afil-teakbr')),
    ('29','None','nenhuma das três'),
    ('30','Adicionar tag',c('afil-sem-marca')),
    ('31','Notificação interna','assunto: '+c('Formulário sem kit: {{contact.first_name}}')+'. É detector de anomalia, não caminho normal'),
  ],
  notas=[
    nota('Por que a tag de marca é o último nó, e não o quinto',
      'O guia numerava a marca como passo 5, no meio. No builder isso não fecha: '
      '<strong>ramo do GHL nunca volta para o tronco.</strong> Se a Condition de marca '
      'estivesse no meio, tudo o que vem depois dela — tier, oportunidade, e-mail — '
      'teria que ser copiado quatro vezes, uma em cada ramo.',
      'Movi para o fim. Nada dentro do W9 lê a tag de marca, então a ordem não muda '
      'comportamento nenhum — muda de 16 nós repetidos para zero.'),
    nota('O passo "fonte de captação vazia → Curadoria" não está no canvas',
      'Ele tem o mesmo problema e não tem o mesmo conserto: seria um segundo '
      '"faça X só se Y, depois continue", e só um pode ser o último.',
      'A saída é tirá-lo do workflow. O seletor de kits já escreve dois campos '
      'ocultos no formulário; escrever um terceiro com <code>Curadoria</code> como '
      'valor padrão resolve na origem e apaga o nó. Se você quiser, eu faço essa '
      'alteração no seletor.', tipo=''),
    nota('O Bairro entra no Branch 3 — mas só depois de estar no formulário',
      'O campo existe no GHL desde 27/08. <strong>Ainda não está no formulário.</strong> '
      'Enquanto não estiver, ele chega vazio para todo mundo — e '
      '<code>Bairro is empty</code> no Branch 3 manda <strong>todos</strong> os '
      'criadores para o ramo de cadastro incompleto.',
      'Ou o campo entra no formulário antes de você publicar o W9, ou o Branch 3 nasce '
      'com quatro condições e a quinta entra depois.', tipo='perigo'),
  ])

# ======================================================================
# W5
# ======================================================================
W5 = dict(
  id='w5', curto='rede de segurança contra revendedor', nome='W5', titulo='Exclusão de revendedor',
  papel='Rede de segurança. Pega card criado por qualquer caminho, inclusive pelo <code>ghl-sync</code>.',
  gatilho='%s → %s / %s' % (en('Pipeline Stage Changed'), b('Afiliados Jornada'), b('Mapeado')),
  config='nada especial',
  nos=9, estado='publicado',
  canvases=[canvas(
    no(1, TRIGGER, 'Etapa Do Funil Alterada',
       'No pipeline is %s<br>Etapa do pipeline is %s' % (b('Afiliados Jornada'), b('Mapeado')),
       destaque=True),
    lig(),
    no(2, COND, 'Condition', 'É revendedor? — <b>um</b> Branch'),
    split(
      ramo(
        no(3, BRANCH, 'Branch · Revendedor',
           'If %s is not empty<br><b>OR</b> %s is not empty' % (m('CNPJ'), m('Codigo Representante'))),
        lig(), no(4, CAMPO, 'Atualizar campo de contato',
                  'Motivo do descarte = <b>E revendedor Nitron</b>'),
        lig(), no(5, TAG, 'Adicionar tag de contato', b('afil-revendedor')),
        lig(), no(6, OPP, 'Criar ou atualizar oportunidade', 'Status = <b>Lost</b>'),
        lig(), no(7, NOTIF, 'Notificação interna', '"Revendedor no pool de afiliados"'),
        fim()),
      ramo(
        no(8, BRANCH, 'None', 'não é revendedor'),
        lig(), no(9, OPP, 'Criar ou atualizar oportunidade',
                  'Afiliados Jornada → <b>Qualificado</b>'),
        fim('FIM · e o W7 acorda')),
    ))],
  tab=[
    ('1','Etapa Do Funil Alterada','No pipeline is '+c('Afiliados Jornada')+' · Etapa is '+c('Mapeado')),
    ('2','Condition','um Branch. O '+en('None')+' é quem passa'),
    ('3','Branch',c('CNPJ')+' is not empty <strong>OR</strong> '+c('Codigo Representante')+' is not empty'),
    ('4','Atualizar campo',c('Afiliado — Motivo do descarte')+' = '+c('E revendedor Nitron')),
    ('5','Adicionar tag',c('afil-revendedor')),
    ('6','Atualizar oportunidade',en('Status')+' = '+en('Lost')),
    ('7','Notificação interna','assunto: '+c('Revendedor no pool: {{contact.first_name}}')),
    ('8','None','não configura nada'),
    ('9','Criar ou atualizar oportunidade',c('Afiliados Jornada')+' → '+c('Qualificado')),
  ],
  notas=[
    nota('O nó 9 é o gatilho do W7 — e o W7 promete comissão',
      'Promover para <code>Qualificado</code> é o que faz o W7 disparar, e o W7 manda '
      'e-mail citando percentual de comissão. Enquanto o frete não estiver medido, '
      '<strong>o W7 tem que estar em <code>Draft</code></strong>. O W5 pode ficar '
      'publicado: sem W7 ativo, o nó 9 só move um card.', tipo='perigo'),
    nota('Key account não passa por aqui, de propósito',
      'O gatilho é <code>Mapeado</code>, e o <code>ghl-sync</code> põe key account '
      'direto em <code>Key Account</code>. Então criador grande nunca é promovido a '
      '<code>Qualificado</code>, nunca entra no W7, e nunca recebe o e-mail automático '
      'de comissão — que seria constrangedor com quem cobra cachê.', tipo='certo'),
  ])

# ======================================================================
# W4
# ======================================================================
W4 = dict(
  id='w4', curto='impede a amostra extraviada de virar recorrente', nome='W4', titulo='Trava de reenvio',
  papel='A trava que impede a amostra extraviada de virar "afiliado recorrente". <strong>Construir antes de publicar o W1.</strong>',
  gatilho='%s → %s / %s' % (en('Pipeline Stage Changed'), b('Afiliados Jornada'), b('Aceito')),
  config='nada especial',
  nos=8, estado='não existe',
  canvases=[canvas(
    no(1, TRIGGER, 'Etapa Do Funil Alterada',
       'No pipeline is %s<br>Etapa do pipeline is %s' % (b('Afiliados Jornada'), b('Aceito')),
       destaque=True),
    lig(),
    no(2, COND, 'Condition', 'Por que ele chegou em Aceito? — <b>dois</b> Branch'),
    split(
      ramo(
        no(3, BRANCH, 'Branch 1 · Voltou por automação',
           'If %s incluir %s' % (m('Tags'), b('afil-devolvido'))),
        lig(), no(4, REMOVE, 'Remover tag de contato', b('afil-devolvido')),
        fim()),
      ramo(
        no(5, BRANCH, 'Branch 2 · Já recebeu amostra',
           'If %s<br>is %s %s %s' % (m('Data ultima amostra'), b('In the Last'), b('90'), b('Dias'))),
        lig(), no(6, NOTIF, 'Notificação interna', '"Reenvio detectado"'),
        lig(), no(7, OPP, 'Criar ou atualizar oportunidade',
                  'Afiliados Jornada → <b>Recorrente</b>'),
        fim()),
      ramo(
        no(8, BRANCH, 'None', 'criador novo, primeira amostra'),
        fim('FIM · segue livre')),
    ))],
  tab=[
    ('1','Etapa Do Funil Alterada','No pipeline is '+c('Afiliados Jornada')+' · Etapa is '+c('Aceito')),
    ('2','Condition','dois Branch, <strong>nesta ordem</strong>. Ver a nota abaixo'),
    ('3','Branch 1',c('Tags')+' incluir '+c('afil-devolvido')),
    ('4','Remover tag',c('afil-devolvido')+'. Encerra e limpa no mesmo movimento — nada acumula'),
    ('5','Branch 2',c('Afiliado — Data ultima amostra')+' <code>is</code> <code class="en">In the Last</code> <code>90</code> <code>Dias</code>'),
    ('6','Notificação interna','texto pronto na secção 7 do '+c('ghl-workflows-v3.md')),
    ('7','Criar ou atualizar oportunidade',c('Afiliados Jornada')+' → '+c('Recorrente')),
    ('8','None','não configura nada. É o caminho normal do criador novo'),
  ],
  notas=[
    nota('O W4 inteiro é uma Condition — e a ordem dos Branch é a invariante',
      'O guia mandava dois <code>If/Else</code> em série. Como os dois encerram no ramo '
      'SIM, viram <strong>um</strong> Condition com dois Branch.',
      'Mas aí a ordem passa a carregar a regra: uma amostra extraviada de quem recebeu '
      'amostra há 10 dias <strong>casa nos dois Branch</strong>. O GHL pega o primeiro. '
      'Se <code>afil-devolvido</code> não for o Branch 1, o card devolvido vai para '
      '<code>Recorrente</code> — que é exatamente a colisão que o W4 existe para evitar.', tipo='perigo'),
    nota('O operador é In the Last, não Before',
      'São opostos. <code class="en">Before</code> pega quem recebeu amostra <em>antes</em> '
      'de 90 dias atrás — ou seja, o afiliado antigo, justamente quem deve passar. '
      'A janela que você quer é "recebeu <strong>dentro</strong> dos últimos 90 dias".',
      '<strong>Teste de sentido:</strong> criador novo, com a data vazia, tem que passar '
      'reto para <code>None</code>. Se ele for para <code>Recorrente</code>, o operador '
      'está invertido.'),
  ])

# ======================================================================
# W2
# ======================================================================
W2 = dict(
  id='w2', curto='o toque depois de a caixa chegar', nome='W2', titulo='Amostra entregue',
  papel='O toque depois da entrega. O gatilho é de <strong>toda entrega da empresa</strong> — o nó 2 é o que separa afiliado de cliente.',
  gatilho='%s → %s / %s' % (en('Pipeline Stage Changed'), b('Entregas'), b('Entregue')),
  config='%s <b>ligado</b>' % en('Stop on Response'),
  nos=7, estado='publicado · 1.223 contatos entraram',
  canvases=[canvas(
    no(1, TRIGGER, 'Etapa Do Funil Alterada',
       'No pipeline is %s<br>Etapa do pipeline is %s' % (b('Entregas'), b('Entregue')),
       destaque=True),
    lig(),
    no(2, COND, 'Condition', 'É amostra de afiliado? — <b>um</b> Branch'),
    split(
      ramo(
        no(3, BRANCH, 'Branch · É afiliado',
           'If %s incluir %s' % (m('Tags'), b('amostra-afiliado'))),
        lig(), no(4, OPP, 'Criar ou atualizar oportunidade',
                  'Afiliados Jornada → <b>Amostra recebida</b>'),
        lig(), no(5, ESPERA, 'Esperar', b('3 horas')),
        lig(), no(6, MSG, 'Enviar WhatsApp',
                  '"chegou tudo certo?"<br><b>sem citar o nome do kit</b>'),
        fim()),
      ramo(
        no(7, BRANCH, 'None', 'entrega comum da empresa'),
        fim('FIM · 1.223 pararam aqui')),
    ))],
  tab=[
    ('1','Etapa Do Funil Alterada','No pipeline is '+c('Entregas')+' · Etapa is '+c('Entregue')),
    ('2','Condition','um Branch. Ligue '+en('Stop on Response')+' na configuração do workflow'),
    ('3','Branch',c('Tags')+' incluir '+c('amostra-afiliado')),
    ('4','Criar ou atualizar oportunidade',c('Afiliados Jornada')+' → '+c('Amostra recebida')+'. <strong>Este nó dispara o W3</strong>'),
    ('5','Esperar',c('3 horas')),
    ('6','Enviar WhatsApp','ou '+en('Send SMS')+'. Pergunta se chegou tudo certo. <strong>Não cite o kit pelo nome</strong> — se veio errado, a pergunta entrega o erro antes de a pessoa abrir'),
    ('7','None','não configura nada'),
  ],
  notas=[
    nota('O nó 2 já foi verificado com 1.223 contatos',
      '1.223 pessoas entraram neste workflow — toda entrega da empresa passa pelo '
      'gatilho. <strong>Nenhuma recebeu mensagem indevida:</strong> zero contatos com a '
      'tag <code>amostra-afiliado</code>, zero cards no pipeline de afiliados, zero '
      'mensagens de saída com o texto do W2.',
      'Isso não é sorte, é o nó 2 funcionando. Se algum dia você mexer neste workflow, '
      'a única coisa que não pode sair é esse Branch.', tipo='certo'),
    nota('As 3 horas de espera não são enfeite',
      '"Entregue" costuma cair quando o pacote chega na portaria, não na mão da pessoa. '
      'Mensagem antes disso soa automática, e a resposta vem pior.'),
  ])

# ======================================================================
# W2b
# ======================================================================
W2B = dict(
  id='w2b', curto='o que fazer quando a caixa volta', nome='W2b', titulo='Amostra extraviada',
  papel='O que fazer quando a caixa volta. Quatro nós, e a ordem entre dois deles é a parte que importa.',
  gatilho='%s → %s / %s' % (en('Pipeline Stage Changed'), b('Entregas'), b('Retorno')),
  config='nada especial',
  nos=7, estado='publicado · 23 contatos entraram',
  canvases=[canvas(
    no(1, TRIGGER, 'Etapa Do Funil Alterada',
       'No pipeline is %s<br>Etapa do pipeline is %s' % (b('Entregas'), b('Retorno')),
       destaque=True),
    lig(),
    no(2, COND, 'Condition', 'É amostra de afiliado? — <b>um</b> Branch'),
    split(
      ramo(
        no(3, BRANCH, 'Branch · É afiliado',
           'If %s incluir %s' % (m('Tags'), b('amostra-afiliado'))),
        lig(), no(4, TAG, 'Adicionar tag de contato',
                  '%s<br><b>tem que vir antes do nó 6</b>' % b('afil-devolvido')),
        lig(), no(5, NOTIF, 'Notificação interna',
                  'endereço · rastreio · quantas amostras já foram'),
        lig(), no(6, OPP, 'Criar ou atualizar oportunidade',
                  'Afiliados Jornada → <b>Aceito</b><br>nunca Amostra solicitada'),
        fim()),
      ramo(
        no(7, BRANCH, 'None', 'devolução comum da empresa'),
        fim()),
    ))],
  tab=[
    ('1','Etapa Do Funil Alterada','No pipeline is '+c('Entregas')+' · Etapa is '+c('Retorno')),
    ('2','Condition','um Branch'),
    ('3','Branch',c('Tags')+' incluir '+c('amostra-afiliado')),
    ('4','Adicionar tag',c('afil-devolvido')+'. <strong>Antes</strong> do nó 6, não depois'),
    ('5','Notificação interna','ponha o endereço inteiro, o código de rastreio e '+c('{{contact.afiliado__qtd_amostras_enviadas}}')+'. Quem lê precisa decidir sem abrir o GHL'),
    ('6','Criar ou atualizar oportunidade',c('Afiliados Jornada')+' → '+c('Aceito')),
    ('7','None','não configura nada'),
  ],
  notas=[
    nota('Duas coisas que parecem detalhe e são o workflow inteiro',
      '<strong>O nó 6 vai para <code>Aceito</code>, nunca para <code>Amostra '
      'solicitada</code>.</strong> Devolver para <code>Amostra solicitada</code> faz o '
      'W1 disparar na hora e gerar um segundo despacho para o endereço que acabou de '
      'falhar. Frete pago duas vezes para o mesmo erro.',
      '<strong>O nó 4 vem antes do nó 6.</strong> A tag é o que faz o W4 encerrar em vez '
      'de mover o card para <code>Recorrente</code>. Se a tag entrar depois do movimento, '
      'o W4 já leu o contato sem ela.', tipo='perigo'),
    nota('Depois do W2b, uma pessoa',
      'O workflow para em <code>Aceito</code> de propósito. Alguém confirma o endereço '
      'com o criador, corrige no contato e arrasta o card de volta para '
      '<code>Amostra solicitada</code>.',
      '<strong>O criador não sabe que a caixa voltou.</strong> Vale um WhatsApp no mesmo '
      'dia, mesmo sem solução pronta.'),
  ])

# ======================================================================
# W3
# ======================================================================
COND_W3 = ('If %s is empty<br><b>AND</b> %s não incluir<br>%s'
           % (m('URL do video'), m('Tags'), b('afil-conteudo-combinado')))

def toque(nc, acoes, wait_txt=None):
    """Um toque do W3. Numera em ordem de leitura: Condition, Branch, acoes,
    Wait, e o None por ultimo. `acoes` e uma lista de (icone, titulo, sub)."""
    n = nc + 1          # o Branch consome nc+1; as acoes comecam em nc+2
    dentro = []
    for ic, tit, sub in acoes:
        n += 1
        dentro += [lig(), no(n, ic, tit, sub)]
    if wait_txt:
        n += 1
        dentro += [lig(), no(n, ESPERA, 'Esperar', b(wait_txt)),
                   lig(), idem('continua — <b>próximo toque</b>')]
    else:
        dentro += [fim()]
    n += 1
    return ''.join([
      no(nc, COND, 'Condition', 'Precisa cobrar? — <b>um</b> Branch'),
      split(
        ramo(no(nc + 1, BRANCH, 'Branch · Precisa', COND_W3), *dentro),
        ramo(no(n, BRANCH, 'None', 'já postou, ou combinado'), fim()),
      )]), n

t1, _ = toque(3, [(MSG, 'Enviar WhatsApp',
                  'toque 1 — "o que você achou do kit?"<br>não cobra vídeo')], '4 dias')
t2, _ = toque(8, [(MSG, 'Enviar e-mail', 'toque 2 — três ideias de roteiro')], '11 dias')
t3, _ = toque(13, [(MSG, 'Enviar WhatsApp', 'toque 3 — aviso final'),
                   (NOTIF, 'Notificação interna',
                    '"vou bloquear em 3 dias"<br><b>não é opcional</b>')], '3 dias')
t4, _ = toque(19, [(OPP, 'Criar ou atualizar oportunidade',
                    'Afiliados Jornada →<br><b>Inadimplente de conteúdo</b>'),
                   (TAG, 'Adicionar tag de contato', b('afil-bloqueado')),
                   (CAMPO, 'Atualizar campo de contato',
                    'Motivo do descarte = <b>Amostra sem video</b>')])

w3_c = canvas(
  no(1, TRIGGER, 'Etapa Do Funil Alterada',
     'No pipeline is %s<br>Etapa do pipeline is %s<br>%s <b>DESLIGADO</b>'
     % (b('Afiliados Jornada'), b('Amostra recebida'), en('Stop on Response')),
     destaque=True),
  lig(),
  no(2, ESPERA, 'Esperar', b('3 dias')),
  lig(), t1,
  rotulo='Toque 1 — dia 3')

w3_c2 = canvas(t2, rotulo='Toque 2 — dia 7')
w3_c3 = canvas(t3, rotulo='Toque 3 — dia 18')
w3_c4 = canvas(t4, rotulo='Corte — dia 21')

W3 = dict(
  id='w3', curto='quatro toques em 21 dias, e o bloqueio', nome='W3', titulo='Cobrança de conteúdo',
  papel='21 dias, quatro toques, e um bloqueio no fim. É o workflow mais longo e o único que pode punir alguém injustamente.',
  gatilho='%s → %s / %s' % (en('Pipeline Stage Changed'), b('Afiliados Jornada'), b('Amostra recebida')),
  config='%s <b>DESLIGADO</b> · %s recomendado' % (en('Stop on Response'), en('Time Window')),
  nos=24, estado='não existe',
  canvases=[w3_c, w3_c2, w3_c3, w3_c4],
  tab=[
    ('1','Etapa Do Funil Alterada','No pipeline is '+c('Afiliados Jornada')+' · Etapa is '+c('Amostra recebida')),
    ('2, 6, 11, 17','Esperar',c('3 dias')+' · '+c('4 dias')+' · '+c('11 dias')+' · '+c('3 dias')+'. <strong>No teste, troque para minutos</strong>'),
    ('3, 8, 13, 19','Condition','a <strong>mesma</strong> condição nas quatro. Monte uma e copie'),
    ('4, 9, 14, 20','Branch',c('Afiliado — URL do video')+' is empty <strong>AND</strong> '+c('Tags')+' não incluir '+c('afil-conteudo-combinado')),
    ('7, 12, 18, 24','None','não configura nada. É quem postou ou combinou. Os quatro encerram em dias diferentes'),
    ('5','Enviar WhatsApp','toque 1. Pergunta o que achou do kit. <strong>Não cobra vídeo</strong>'),
    ('10','Enviar e-mail','toque 2. Três ideias de roteiro, não uma cobrança'),
    ('15','Enviar WhatsApp','toque 3. Aviso final, com prazo explícito'),
    ('16','Notificação interna','"vou bloquear em 3 dias". <strong>Não é opcional</strong> — ver a nota'),
    ('21','Criar ou atualizar oportunidade',c('Afiliados Jornada')+' → '+c('Inadimplente de conteúdo')+'. <strong>Com acento</strong>'),
    ('22','Adicionar tag',c('afil-bloqueado')),
    ('23','Atualizar campo',c('Afiliado — Motivo do descarte')+' = '+c('Amostra sem video')),
  ],
  notas=[
    nota('Stop on Response fica DESLIGADO, e isso é contra-intuitivo',
      'Com ele ligado, o criador que responde <em>"vou gravar sábado"</em> sai da '
      'cobrança — sem nunca ter preenchido <code>URL do video</code>. Ele nunca mais é '
      'cobrado e nunca é bloqueado: some do processo.',
      'Quem quer parar a cobrança de propósito recebe a tag '
      '<code>afil-conteudo-combinado</code> à mão. É uma decisão de pessoa, não um efeito '
      'colateral de ter respondido.', tipo='perigo'),
    nota('A notificação do nó 17 é o que impede o W3 de punir quem cumpriu',
      '<code>URL do video</code> é preenchido <strong>à mão</strong>. Se o criador postar '
      'e ninguém colar o link, o W3 bloqueia alguém que fez tudo certo.',
      'Os três dias entre o aviso e o corte existem para uma pessoa conferir. Sem a '
      'notificação, ninguém confere — e o nó 22 põe <code>afil-bloqueado</code> em quem '
      'entregou.', tipo='perigo'),
    nota('Os quatro None não são o mesmo lugar',
      'Cada um encerra o workflow num dia diferente — dia 3, 7, 18 e 21. Quem postou '
      'depois do toque 2 sai pelo None do nó 12 e nunca vê o aviso final. É o desenho '
      'certo: a cobrança para quando o objetivo é atingido, não quando o calendário '
      'acaba.'),
    nota('Alternância de canal, e a conta que ela esconde',
      'Toques 1 e 3 por WhatsApp, toque 2 por e-mail. Se você puser os dois canais em '
      'cada toque, o criador recebe <strong>seis mensagens em 21 dias</strong> e a última '
      'é um bloqueio. Alternar não é economia de mensagem, é o que mantém o tom.'),
  ])

# ======================================================================
# W8
# ======================================================================
W8 = dict(
  id='w8', curto='tira quem respondeu da sequência automática', nome='W8', titulo='Resposta detectada',
  papel='Quando o criador responde um e-mail, tira ele da sequência automática e avisa uma pessoa.',
  gatilho='%s → canal %s' % (en('Customer Replied'), b('Email')),
  config='nada especial',
  nos=7, estado='não existe',
  canvases=[canvas(
    no(1, TRIGGER, 'Cliente Respondeu', 'Canal is %s' % b('Email'), destaque=True),
    lig(),
    no(2, COND, 'Condition', 'É afiliado? — <b>um</b> Branch'),
    split(
      ramo(
        no(3, BRANCH, 'Branch · É afiliado',
           'If %s incluir %s' % (m('Tags'), b('afiliado'))),
        lig(), no(4, OPP, 'Criar ou atualizar oportunidade',
                  'Afiliados Jornada → <b>Respondeu</b>'),
        lig(), no(5, REMOVE, 'Remover do workflow',
                  'o <b>W7</b>, pelo nome exato'),
        lig(), no(6, NOTIF, 'Notificação interna',
                  'handle · seguidores · engajamento<br>trilha · vitrine · meta 4h'),
        fim()),
      ramo(
        no(7, BRANCH, 'None', 'cliente B2B respondendo'),
        fim()),
    ))],
  tab=[
    ('1','Cliente Respondeu','Canal is '+en('Email')+'. Dispara em toda resposta de e-mail da conta'),
    ('2','Condition','um Branch'),
    ('3','Branch',c('Tags')+' incluir '+c('afiliado')),
    ('4','Criar ou atualizar oportunidade',c('Afiliados Jornada')+' → '+c('Respondeu')),
    ('5','Remover do workflow','selecione o W7 <strong>pelo nome exato</strong>. Ver a nota'),
    ('6','Notificação interna','ponha '+c('{{contact.afiliado__handle_principal}}')+', seguidores, engajamento, trilha e vitrine. Quem lê tem 4h para responder e não pode precisar abrir o GHL'),
    ('7','None','não configura nada'),
  ],
  notas=[
    nota('O nó 5 falha em silêncio se existir mais de um W7',
      'Hoje existe um rascunho de W7 abandonado além do publicado. '
      '<code class="en">Remove From Workflow</code> remove o workflow que você '
      'selecionar — se o contato estiver no <em>outro</em>, ele continua recebendo a '
      'sequência automática enquanto uma pessoa conversa com ele por e-mail.',
      '<strong>Mantenha um W7 só.</strong> Não apague o rascunho sem conferir se algum '
      'contato está dentro dele.', tipo='perigo'),
    nota('O nó 2 existe porque o gatilho é da conta toda',
      'Toda resposta de e-mail entra aqui, inclusive de cliente B2B do Clube Nitron. '
      'Sem o Branch, um comprador respondendo sobre pedido viraria card em '
      '<code>Respondeu</code> no pipeline de afiliados.'),
  ])

# ======================================================================
# W7
# ======================================================================
def cadencia(n0, letra, nome_trilha):
    return [
      lig(), no(n0,   MSG,   'Enviar e-mail', 'template <b>%s1</b>' % letra),
      lig(), no(n0+1, OPP,   'Criar ou atualizar oportunidade', 'Afiliados Jornada → <b>Contatado</b>'),
      lig(), no(n0+2, ESPERA,'Esperar', b('4 dias')),
      lig(), no(n0+3, MSG,   'Enviar e-mail', 'template <b>%s2</b>' % letra),
      lig(), no(n0+4, ESPERA,'Esperar', b('5 dias')),
      lig(), no(n0+5, MSG,   'Enviar e-mail', 'template <b>%s3</b>' % letra),
      lig(), no(n0+6, ESPERA,'Esperar', b('5 dias')),
      lig(), no(n0+7, CAMPO, 'Atualizar campo de contato', 'Motivo do descarte = <b>Sem resposta</b>'),
      lig(), no(n0+8, OPP,   'Criar ou atualizar oportunidade', 'Status = <b>Lost</b>'),
      fim()]

w7_c = canvas(
  no(1, TRIGGER, 'Etapa Do Funil Alterada',
     'No pipeline is %s<br>Etapa do pipeline is %s<br>%s <b>ligado</b>'
     % (b('Afiliados Jornada'), b('Qualificado'), en('Stop on Response')),
     destaque=True),
  lig(),
  no(2, COND, 'Condition', 'Tem e-mail? — <b>um</b> Branch'),
  split(
    ramo(
      no(3, BRANCH, 'Branch · Sem e-mail', 'If %s is empty' % m('Email')),
      lig(), no(4, TAG, 'Adicionar tag de contato', b('afil-sem-email')),
      fim('FIM · fica em Qualificado')),
    ramo(
      no(5, BRANCH, 'None', 'tem e-mail'),
      lig(), idem('continua no canvas abaixo<br><b>nó 6</b>')),
  ),
  rotulo='A porteira'
)

w7_c2 = canvas(
  no(6, COND, 'Condition', 'Qual trilha? — <b>três</b> Branch'),
  split(
    ramo(
      no(7, BRANCH, 'Branch 1 · Curadoria teca', 'If %s is <b>Curadoria teca</b>' % m('Trilha')),
      lig(), no(8, MSG, 'Enviar e-mail', 'template <b>D1</b>'),
      lig(), no(9, OPP, 'Criar ou atualizar oportunidade', 'Afiliados Jornada → <b>Contatado</b>'),
      fim('FIM · só um toque')),
    ramo(
      no(10, BRANCH, 'Branch 2 · Achadinhos', 'If %s is <b>Achadinhos</b>' % m('Trilha')),
      *cadencia(11, 'A', 'Achadinhos')),
    ramo(
      no(20, BRANCH, 'Branch 3 · Mudanca casa nova', 'If %s is <b>Mudanca casa nova</b>' % m('Trilha')),
      lig(), idem('<b>cadência igual aos nós 11–19</b><br>templates <b>B1 B2 B3</b>'),
      fim()),
    ramo(
      no(30, BRANCH, 'None', 'Nicho organizacao<br>e trilha vazia'),
      lig(), idem('<b>cadência igual aos nós 11–19</b><br>templates <b>C1 C2 C3</b>'),
      fim()),
  ),
  rotulo='O roteador de trilha e as três cadências'
)

W7 = dict(
  id='w7', curto='a sequência de e-mail por trilha', nome='W7', titulo='Sequência de e-mail',
  papel='O único workflow que faz promessa para fora: os e-mails citam percentual de comissão. <strong>Fica em <code>Draft</code> até o frete estar medido.</strong>',
  gatilho='%s → %s / %s' % (en('Pipeline Stage Changed'), b('Afiliados Jornada'), b('Qualificado')),
  config='%s <b>ligado</b>' % en('Stop on Response'),
  nos=39, estado='publicado · voltar para Draft',
  canvases=[w7_c, w7_c2],
  tab=[
    ('1','Etapa Do Funil Alterada','No pipeline is '+c('Afiliados Jornada')+' · Etapa is '+c('Qualificado')),
    ('2','Condition','um Branch'),
    ('3','Branch',en('Email')+' is empty'),
    ('4','Adicionar tag',c('afil-sem-email')+'. O card <strong>fica</strong> em '+c('Qualificado')+' e vai para a fila de DM'),
    ('5','None','não configura nada'),
    ('6','Condition','<strong>três</strong> Branch. O '+en('None')+' pega '+c('Nicho organizacao')+' <em>e</em> trilha vazia — de propósito'),
    ('7','Branch 1',c('Afiliado — Trilha')+' <code>is</code> <code>Curadoria teca</code>'),
    ('8','Enviar e-mail','template <strong>D1</strong>'),
    ('9','Criar ou atualizar oportunidade',c('Afiliados Jornada')+' → '+c('Contatado')+'. E encerra'),
    ('10','Branch 2',c('Afiliado — Trilha')+' <code>is</code> <code>Achadinhos</code>'),
    ('11–19','Cadência A','A1 → '+c('Contatado')+' → esperar '+c('4 dias')+' → A2 → esperar '+c('5 dias')+' → A3 → esperar '+c('5 dias')+' → motivo '+c('Sem resposta')+' → '+en('Status')+' '+en('Lost')),
    ('20–29','Branch 3 + cadência B','trilha '+c('Mudanca casa nova')+'. Mesma forma dos nós 11–19, templates B1 B2 B3'),
    ('30–39','None + cadência C','mesma forma, templates C1 C2 C3'),
  ],
  notas=[
    nota('A cadência fica dentro de cada trilha, não depois do roteador',
      'O guia numerava o roteador como passo 2 e a cadência como passos 3 a 10, '
      'como se ela viesse depois. No builder não vem: <strong>ramo do GHL nunca volta '
      'para o tronco.</strong>',
      'Mas aqui isso não custa nada, porque os templates <em>já eram</em> por trilha — '
      'A2, B2, C2, A3, B3, C3. Cada ramo carrega a sua própria cadência e nada se '
      'duplica além dos dois nós de encerramento.', tipo='certo'),
    nota('Curadoria teca sai no primeiro toque, e isso é intencional',
      'Criador de curadoria é negociação com cachê, tratada por pessoa. Insistir por '
      'e-mail automático três vezes com quem cobra cachê queima a conversa antes de ela '
      'começar.'),
    nota('Antes de sair do Draft, duas contas',
      '<strong>O frete.</strong> A coluna de peso dos kits está vazia na planilha — são '
      '20 células. Sem ela, o percentual de comissão dos e-mails é um número inventado.',
      '<strong>O rascunho antigo.</strong> Existe um segundo W7 abandonado. Enquanto os '
      'dois existirem, o nó 5 do W8 pode remover o contato do W7 errado. Resolva antes '
      'de publicar, não depois.', tipo='perigo'),
  ])

# ======================================================================
# W6
# ======================================================================
W6 = dict(
  id='w6', curto='promove tier quando a venda entra', nome='W6', titulo='Primeira venda',
  papel='O último a construir. Hoje ele não teria o que observar: o GMV não volta do Sankhya nem da Shopify para o GHL.',
  gatilho='%s → campo %s' % (en('Contact Changed'), b('Afiliado — GMV acumulado')),
  config='cuidado com re-entrada — ver a nota',
  nos=11, estado='não existe · depende do GMV voltar',
  canvases=[canvas(
    no(1, TRIGGER, 'Contato Alterado',
       'Campo is %s' % b('Afiliado — GMV acumulado'), destaque=True),
    lig(),
    no(2, COND, 'Condition', 'Qual faixa? — <b>dois</b> Branch'),
    split(
      ramo(
        no(3, BRANCH, 'Branch 1 · Ouro',
           'If %s<br>greater than <b>5000</b>' % m('GMV acumulado')),
        lig(), no(4, OPP, 'Criar ou atualizar oportunidade',
                  'Afiliados Jornada → <b>Convertido</b>'),
        lig(), no(5, CAMPO, 'Atualizar campo de contato', 'Tier = <b>Ouro</b>'),
        lig(), no(6, NOTIF, 'Notificação interna', '"Afiliado passou de R$ 5.000"'),
        fim()),
      ramo(
        no(7, BRANCH, 'Branch 2 · Prata',
           'If %s<br>greater than <b>0</b>' % m('GMV acumulado')),
        lig(), no(8, OPP, 'Criar ou atualizar oportunidade',
                  'Afiliados Jornada → <b>Convertido</b>'),
        lig(), no(9, CAMPO, 'Atualizar campo de contato', 'Tier = <b>Prata</b>'),
        lig(), no(10, NOTIF, 'Notificação interna', '"Primeira venda"'),
        fim()),
      ramo(
        no(11, BRANCH, 'None', 'GMV zerado ou vazio'),
        fim()),
    ))],
  tab=[
    ('1','Contato Alterado','filtro no campo '+c('Afiliado — GMV acumulado')),
    ('2','Condition','dois Branch, <strong>Ouro primeiro</strong>. Ver a nota'),
    ('3','Branch 1',c('Afiliado — GMV acumulado')+' <code class="en">greater than</code> <code>5000</code>'),
    ('4, 8','Criar ou atualizar oportunidade',c('Afiliados Jornada')+' → '+c('Convertido')),
    ('5','Atualizar campo',c('Afiliado — Tier')+' = '+c('Ouro')),
    ('6','Notificação interna','assunto: '+c('{{contact.first_name}} passou de R$ 5.000')),
    ('7','Branch 2',c('Afiliado — GMV acumulado')+' <code class="en">greater than</code> <code>0</code>'),
    ('9','Atualizar campo',c('Afiliado — Tier')+' = '+c('Prata')),
    ('10','Notificação interna','assunto: '+c('Primeira venda: {{contact.first_name}}')),
    ('11','None','não configura nada'),
  ],
  notas=[
    nota('Ouro tem que ser o Branch 1, senão nunca acontece',
      'O guia tinha dois <code>If/Else</code> em série, e funcionava porque o segundo '
      '<em>sobrescrevia</em> o primeiro: todo mundo virava Prata, e quem passava de '
      '5.000 virava Ouro depois.',
      'Numa Condition o GHL <strong>para no primeiro Branch que casar</strong>. Se '
      '<code>greater than 0</code> vier primeiro, ele casa com todo mundo e o ramo Ouro '
      'nunca é avaliado. A ordem deixou de ser estética e passou a ser a regra.', tipo='perigo'),
    nota('Contato Alterado dispara em toda escrita, não em toda mudança de faixa',
      'Se o <code>ghl-sync</code> reescrever o mesmo GMV, o gatilho dispara de novo — e '
      'a notificação "Primeira venda" chega uma segunda vez para a mesma venda.',
      'Duas saídas: deixar <code class="en">Allow Re-Entry</code> <strong>desligado</strong>, '
      'ou dar ao Branch 2 uma segunda condição — <code>Afiliado — Tier</code> '
      '<code>is</code> <code>Bronze</code> — para ele só agir em quem ainda não subiu.'),
    nota('Este é o único que não dá para testar hoje',
      'O GMV não volta do Sankhya nem da Shopify para o GHL. Você pode montar o '
      'workflow e conferir a lógica escrevendo o campo à mão num contato de teste, mas '
      'ele não vai disparar sozinho até a ponte existir.'),
  ])

WFS = [W9, W5, W4, W1_PLACEHOLDER] if False else [W9, W5, W4, W2, W2B, W3, W8, W7, W6]

# ----- conserta o W9: junta os nos 1 e 2 no canvas do split -----
W9['canvases'] = [
  canvas(
    no(1, TRIGGER, 'Formulário Enviado',
       'Formulário is %s<br>%s <b>ligado</b>' % (b('cadastro de afiliado'), en('Allow Re-Entry')),
       destaque=True),
    lig(),
    no(2, TAG, 'Adicionar tag de contato', b('afiliado')),
    lig(),
    W9['canvases'][1].split('<div class="pista">',1)[1].rsplit('</div></div>',1)[0],
    rotulo='O tronco e os quatro caminhos'),
  W9['canvases'][2],
]
WFS = [W9, W5, W4, W2, W2B, W3, W8, W7, W6]

# ======================================================================
# montagem da pagina
# ======================================================================
CSS = io.open(os.path.join(RAIZ, 'docs/w1-canvas.html'), encoding='utf-8').read()
CSS = CSS.split('<style>',1)[1].split('</style>',1)[0]

EXTRA_CSS = """
  /* --- acrescentado para a pagina dos nove --- */
  .ic-msg{background:var(--g-roxo)}
  .ic-espera{background:var(--g-cinza)}
  .ic-remove{background:var(--g-laranja)}
  .canvas{position:relative}
  .canvas-rot{
    font:600 10.5px/1 Karla,sans-serif;letter-spacing:.11em;text-transform:uppercase;
    color:var(--g-tinta-2);margin:-12px 0 20px;text-align:center;
  }
  .indice{margin:26px 0 10px}
  .indice a{color:var(--teca);text-decoration:none;border-bottom:1px solid transparent;font-weight:600}
  .indice a:hover,.indice a:focus-visible{border-bottom-color:var(--teca)}
  .chip{
    display:inline-block;font:600 10.5px/1.5 Karla,sans-serif;letter-spacing:.05em;
    padding:1px 8px;border-radius:20px;white-space:nowrap;
  }
  .chip.falta{background:rgba(155,50,38,.12);color:var(--sangue)}
  .chip.pub{background:rgba(47,93,74,.13);color:var(--mata)}
  .chip.rasc{background:rgba(160,100,43,.14);color:var(--teca)}
  .wf{margin-top:clamp(52px,7vw,84px);padding-top:26px;border-top:2px solid var(--borda-forte)}
  .wf:first-of-type{border-top:none;padding-top:0}
  .wf h2{margin-top:0;display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
  .wf h2 .sigla{
    font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.62em;
    color:var(--teca);letter-spacing:.02em;
  }
  .ficha{
    display:grid;grid-template-columns:auto 1fr;gap:5px 16px;margin:16px 0 4px;
    font-size:14.5px;padding:14px 16px;background:var(--superficie);
    border:1px solid var(--borda);border-radius:10px;
  }
  .ficha dt{font:600 10.5px/1.7 Karla,sans-serif;letter-spacing:.09em;text-transform:uppercase;color:var(--tinta-3);white-space:nowrap}
  .ficha dd{margin:0;color:var(--tinta-2)}
  .ficha dd code{font-size:.82em}
  h4{font-family:"Bricolage Grotesque",Karla,sans-serif;font-weight:700;font-size:15px;margin:26px 0 8px;letter-spacing:-.005em;color:var(--tinta-2);text-transform:none}
  a:focus-visible{outline:2px solid var(--teca);outline-offset:2px;border-radius:2px}
"""

def chip(estado):
    if 'não existe' in estado: cl = 'falta'
    elif 'Draft' in estado:    cl = 'rasc'
    else:                      cl = 'pub'
    return '<span class="chip %s">%s</span>' % (cl, estado)

ORDEM = ['W9','W5','W4','W1','W2','W2b','W3','W8','W7','W6']

indice = ['<div class="rolagem"><table><thead><tr>'
          '<th>Ordem</th><th>Workflow</th><th>O que faz</th><th>Nós</th><th>Estado hoje</th>'
          '</tr></thead><tbody>']
for i, sig in enumerate(ORDEM, 1):
    if sig == 'W1':
        indice.append(
          '<tr><td>%d</td><td><strong>W1</strong> · Ponte para logística</td>'
          '<td>o porteiro antes do frete</td><td>15</td>'
          '<td><em>está no canvas do W1, à parte</em></td></tr>' % i)
        continue
    w = [x for x in WFS if x['nome'] == sig][0]
    indice.append(
      '<tr><td>%d</td><td><a href="#%s"><strong>%s</strong> · %s</a></td>'
      '<td>%s</td><td>%d</td><td>%s</td></tr>' % (
        i, w['id'], w['nome'], w['titulo'],
        w['curto'],
        w['nos'], chip(w['estado'])))
indice.append('</tbody></table></div>')
indice = ''.join(indice)

secoes = []
for w in WFS:
    partes = ['<section class="wf" id="%s">' % w['id']]
    partes.append('<h2><span class="sigla">%s</span>%s</h2>' % (w['nome'], w['titulo']))
    partes.append('<p>%s</p>' % w['papel'])
    partes.append(
      '<dl class="ficha">'
      '<dt>Gatilho</dt><dd>%s</dd>'
      '<dt>Configuração</dt><dd>%s</dd>'
      '<dt>Nós</dt><dd>%d</dd>'
      '<dt>Hoje</dt><dd>%s</dd>'
      '</dl>' % (w['gatilho'], w['config'], w['nos'], chip(w['estado'])))
    for cv in w['canvases']:
        partes.append(cv)
    partes.append('<h4>O que digitar em cada nó</h4>')
    partes.append(tabela(w['tab']))
    partes.append('<h4>O que só aparece ao montar</h4>')
    partes.extend(w['notas'])
    partes.append('</section>')
    secoes.append(''.join(partes))

LEGENDA = ('<div class="legenda">'
  '<span><i style="background:var(--g-azul)"></i> gatilho e oportunidade</span>'
  '<span><i style="background:var(--g-cinza)"></i> Condition e espera</span>'
  '<span><i style="background:var(--g-roxo)"></i> Branch e mensagem</span>'
  '<span><i style="background:var(--g-laranja)"></i> tag</span>'
  '<span><i style="background:var(--g-verde)"></i> notificação</span>'
  '<span><i style="background:var(--g-teal)"></i> campo</span>'
  '</div>')

PAGINA = u"""<title>Canvas dos Nove Workflows</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=Karla:wght@400;500;600;700&display=swap">

<style>%(css)s%(extra)s</style>

<div class="pagina">
<main>

<span class="olho">Molde para copiar · W9 W5 W4 W2 W2b W3 W8 W7 W6</span>
<h1>Os outros nove, nó por nó</h1>
<p class="resumo">
  Cada workflow desenhado como o GHL desenha, na ordem de construção, para você
  conferir o que já montou e copiar o que falta. O W1 tem página própria.
</p>

%(legenda)s

<div class="indice">%(indice)s</div>

<div class="nota certo">
  <span class="rotulo">A mesma redução do W1 vale em quatro deles</span>
  <p>
    Um <code>Condition</code> do GHL aceita <strong>vários Branch</strong> e para no
    primeiro que casar. Então onde o guia mandava dois, três ou quatro
    <code>If/Else</code> em série, cada um com um ramo que encerra, cabe
    <strong>uma pergunta só</strong> com vários Branch — e o <code>None</code> é o
    caminho de quem passou por todas.
  </p>
  <p>
    <strong>W9</strong> cai de quatro <code>If/Else</code> para duas
    <code>Condition</code>. <strong>W4</strong> cai de dois para
    <strong>um nó</strong>. <strong>W6</strong> cai de dois para um. E em
    <strong>W7</strong> a mudança não é de tamanho, é de forma: a cadência passa a
    morar dentro de cada trilha.
  </p>
  <p>
    A lógica não muda em nenhum. O que muda é que a ordem dos Branch passa a
    carregar regra — em <strong>W4</strong> e <strong>W6</strong> ela é a diferença
    entre funcionar e não funcionar, e está anotada nos dois.
  </p>
</div>

<div class="nota">
  <span class="rotulo">A regra do builder que explica quase toda decisão desta página</span>
  <p>
    <strong>Ramo do GHL nunca volta para o tronco.</strong> Cada Branch segue sozinho
    até o fim. Não existe "junta tudo de novo aqui embaixo".
  </p>
  <p>
    Consequência prática: todo "faça X só se Y, <em>depois continue</em>" custa uma
    cópia de tudo o que vem depois. É por isso que a tag de marca virou o último nó
    do W9, e por isso que a cadência do W7 mora dentro de cada trilha em vez de
    depois do roteador. Quando você vê um passo do guia fora da ordem original nesta
    página, é sempre por esse motivo — e está dito na nota do workflow.
  </p>
</div>

%(secoes)s

<section class="wf">
<h2>Antes de publicar qualquer um</h2>

<h4>A ordem não é sugestão</h4>
<p>
  <strong>W9 → W5 → W4 → W1 → W2/W2b → W3 → W8 → W7 → W6.</strong> Dois pares
  dentro dessa ordem existem por causa de colisão real, não de organização:
</p>
<ul>
  <li>
    <strong>W4 antes do W1.</strong> O W1 gera amostra, amostra gera extravio,
    extravio devolve o card para <code>Aceito</code> — e é lá que o W4 age. Publicar
    o W1 sem o W4 manda a primeira amostra extraviada para <code>Recorrente</code>.
  </li>
  <li>
    <strong>W4 antes do W2b.</strong> Hoje o W2b está publicado e o W4 não existe.
    Por acaso, seguro: sem W4 ninguém sequestra o card devolvido. O risco aparece no
    minuto em que o W4 nascer — ele precisa já vir com o Branch 1 da tag
    <code>afil-devolvido</code> em primeiro lugar.
  </li>
</ul>

<h4>O que já está pronto para os nove</h4>
<p>
  <strong>As doze tags existem</strong>, com id conferido — inclusive
  <code>afil-devolvido</code>, <code>afil-revendedor</code>,
  <code>afil-cadastro-incompleto</code> e <code>afil-teste</code>. Nenhum nó de tag
  desta página vai ficar sem o que selecionar.
</p>
<p>
  <strong>O campo <code>Bairro</code> existe</strong> — <code>contact.bairro</code>,
  TEXT. Mas ainda <strong>não está no formulário</strong>, e isso muda o W9: ver a
  nota vermelha lá.
</p>

<h4>Os nomes traduzem pela metade</h4>
<p>
  No seu builder <code>Criar ou atualizar oportunidade</code> aparece em português e
  <code>Condition</code>, <code>Branch</code> e <code>None</code> ficam em inglês.
  Se não achar um nó pelo nome que usei, procure o par:
</p>
<div class="rolagem">
<table>
  <thead><tr><th>Nesta página</th><th>Se não achar, procure</th></tr></thead>
  <tbody>
    <tr><td>Adicionar tag de contato</td><td><code class="en">Add Contact Tag</code></td></tr>
    <tr><td>Remover tag de contato</td><td><code class="en">Remove Contact Tag</code></td></tr>
    <tr><td>Atualizar campo de contato</td><td><code class="en">Update Contact Field</code></td></tr>
    <tr><td>Criar ou atualizar oportunidade</td><td><code class="en">Create/Update Opportunity</code></td></tr>
    <tr><td>Notificação interna</td><td><code class="en">Internal Notification</code></td></tr>
    <tr><td>Remover do workflow</td><td><code class="en">Remove From Workflow</code></td></tr>
    <tr><td>Etapa Do Funil Alterada</td><td><code class="en">Pipeline Stage Changed</code></td></tr>
    <tr><td>Contato Alterado</td><td><code class="en">Contact Changed</code></td></tr>
    <tr><td>Cliente Respondeu</td><td><code class="en">Customer Replied</code></td></tr>
    <tr><td>Formulário Enviado</td><td><code class="en">Form Submitted</code></td></tr>
    <tr><td>Esperar</td><td><code class="en">Wait</code></td></tr>
  </tbody>
</table>
</div>

<h4>Nos testes, encurte as esperas</h4>
<p>
  O W3 tem 21 dias e o W7 tem 14. Testar em tempo real é inviável: troque os
  <code class="en">Wait</code> para minutos, rode com um contato marcado
  <code>afil-teste</code>, e só devolva os prazos reais depois de o caminho inteiro
  ter funcionado. <strong>Apague os contatos de teste no fim</strong> — a tag existe
  para você achá-los.
</p>
</section>

<p class="fim-doc">
  O canvas aqui imita o GHL de propósito, com as cores dele — é a única parte desta
  página que não segue a paleta do projeto, porque precisa ser reconhecível ao lado
  da tela do builder. Gerado a partir de
  <code>docs/ghl-workflows-v3.md</code>, que é a especificação; onde os dois
  divergirem, a especificação está desatualizada.
</p>

</main>
</div>
""" % dict(css=CSS, extra=EXTRA_CSS, legenda=LEGENDA, indice=indice,
           secoes=''.join(secoes))

destino = os.path.join(RAIZ, 'docs/canvas-workflows.html')
io.open(destino, 'w', encoding='utf-8').write(PAGINA)
print('escrito %s — %d bytes' % (destino, len(PAGINA)))
