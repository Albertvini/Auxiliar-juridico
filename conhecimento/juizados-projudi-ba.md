# Juizados Especiais Cíveis (Lei 9.099/95) no PROJUDI/TJBA — rito, prazos e recursos

> Base de referência. Regimentos, resoluções e portarias do TJBA e das Turmas Recursais mudam: em caso de
> dúvida sobre prazo ou procedimento local, marque `[VERIFICAR NORMA DO TJBA]`.

## 1. Competência e limites

- Causas até **40 salários mínimos** (art. 3º, I). Acima disso, o autor renuncia ao excedente (art. 3º, §3º),
  salvo conciliação.
- Até **20 salários mínimos** a parte pode atuar sem advogado na 1ª instância (art. 9º). **No recurso,
  advogado é obrigatório** (art. 41, §2º).
- Não se admite intervenção de terceiros nem assistência (art. 10). Litisconsórcio é admitido.
- Pessoa jurídica só pode ser autora nos casos do art. 8º, §1º (ME, EPP, MEI etc.) — irrelevante quando o
  cliente é o consumidor pessoa física.
- **Complexidade da causa** (art. 3º, *caput*): o banco costuma alegar necessidade de perícia grafotécnica
  para extinguir o feito (art. 51, II). Ver rebate em `defesas-dos-bancos.md`.

## 2. Fases do procedimento

1. Petição inicial (art. 14) → citação do banco (art. 18; em regra por via eletrônica/postal).
2. **Audiência de conciliação** (art. 21-22). Ausência do autor = extinção sem mérito e custas (art. 51, I e
   §2º); ausência do réu = **revelia** (art. 20).
3. **Contestação**: em regra até a audiência de instrução, ou no prazo fixado pelo juízo (muito comum no
   PROJUDI a fixação de prazo após a conciliação infrutífera). Verificar o despacho/ata.
4. **Manifestação sobre a contestação (réplica/impugnação)**: não há previsão expressa na Lei 9.099/95;
   decorre do contraditório (CPC, arts. 7º, 9º, 10, 350 e 351, aplicados subsidiariamente). O prazo é o que o
   juízo fixar; se omisso, usar o art. 218, §3º, CPC (**5 dias**) por cautela, salvo designação de audiência
   em que a réplica pode ser oral.
5. Audiência de instrução e julgamento (arts. 27-29) ou julgamento antecipado.
6. **Sentença** (art. 38) — dispensa relatório; frequentemente elaborada por juiz leigo e homologada (art. 40).

## 3. Contagem de prazos

- **Dias úteis** (art. 12-A, incluído pela Lei 13.728/2018), para prazos processuais, inclusive recursais.
- Exclui-se o dia do começo e inclui-se o do vencimento (CPC, art. 224).
- Prazo que começa ou termina em dia sem expediente forense ou com expediente encerrado antes do normal /
  indisponibilidade do sistema é prorrogado para o primeiro dia útil seguinte (CPC, art. 224, §1º).
- **Suspensão de 20 de dezembro a 20 de janeiro** (CPC, art. 220). A aplicação aos Juizados é tratada por ato
  do TJBA — `[VERIFICAR NORMA DO TJBA]` para o ano corrente.
- **Não há prazo em dobro** para litisconsortes com procuradores diferentes nos Juizados (art. 229 CPC é
  inaplicável segundo entendimento corrente — `[VERIFICAR]` se relevante).
- **Não há remessa necessária** nem prazo diferenciado para a instituição financeira privada.

### Intimação eletrônica (Lei 11.419/2006, art. 5º)

- A intimação se considera feita **no dia em que o advogado consultar** o teor no sistema (§1º).
- Se a consulta ocorrer em dia não útil, considera-se feita no primeiro dia útil seguinte (§2º).
- Se não houver consulta em **10 dias corridos** contados da data do envio (disponibilização), a intimação
  considera-se **automaticamente realizada** ao final desse prazo — **intimação tácita** (§3º).
- O prazo processual começa no **primeiro dia útil seguinte** à intimação.
- Intimação pelo **Diário da Justiça Eletrônico (DJe)**: considera-se publicada no primeiro dia útil seguinte à
  disponibilização (Lei 11.419/2006, art. 4º, §3º), e o prazo começa no primeiro dia útil seguinte à publicação
  (§4º). Havendo intimação no sistema e no DJe, prevalece a regra fixada pelo TJBA — `[VERIFICAR]`.
- No PROJUDI, a tela de intimações mostra a **data de expedição** e a **data da leitura (ciência)**. Sempre
  registre as duas na ficha.

A ferramenta `ferramentas/prazo.py` implementa essas regras.

## 4. Recursos e meios de impugnação no Juizado

| Medida | Cabimento | Prazo | Observações |
|---|---|---|---|
| **Embargos de declaração** | Obscuridade, contradição, omissão ou erro material na sentença/acórdão (art. 48) | **5 dias** (art. 49) | **Interrompem** o prazo do recurso (art. 50, na redação do CPC/2015). Podem ser opostos por escrito ou oralmente. |
| **Recurso inominado** | Contra a sentença, exceto a homologatória de conciliação ou laudo arbitral (art. 41) | **10 dias** da ciência da sentença (art. 42) | Julgado por Turma Recursal (art. 41, §1º). Advogado obrigatório. Efeito em regra só devolutivo; o juiz pode dar efeito suspensivo (art. 43). |
| **Preparo do recurso inominado** | — | **48 horas seguintes à interposição, independentemente de intimação** (art. 42, §1º) | Compreende custas do processo em 1º grau + custas recursais (art. 54, parágrafo único). Sem preparo = **deserção**. Pedir gratuidade na própria petição recursal quando cabível (CPC, arts. 98-99). |
| **Contrarrazões ao recurso inominado** | Resposta ao recurso do banco | **10 dias** da intimação (art. 42, §2º) | Momento de pedir a majoração/condenação do recorrente vencido em honorários (art. 55). |
| **Agravo de instrumento** | Em regra **não cabe** contra decisões interlocutórias no Juizado | — | Rever enunciados do FONAJE e da Turma Recursal. Questões interlocutórias são impugnadas no recurso inominado. |
| **Mandado de segurança** | Contra ato judicial teratológico no Juizado, dirigido à Turma Recursal | 120 dias (Lei 12.016/2009, art. 23) | O STF (RE 576.847, Tema 77) afastou o MS contra decisão interlocutória em regra. Uso excepcional. |
| **Embargos de declaração do acórdão** | Contra acórdão da Turma Recursal | 5 dias | Mesmas hipóteses do art. 48. |
| **Recurso extraordinário** | Contra acórdão da Turma Recursal que ofenda a Constituição (CF, art. 102, III) | 15 dias úteis (CPC, art. 1.003, §5º) | Exige repercussão geral. **Não cabe recurso especial** contra acórdão de Turma Recursal (**Súmula 203/STJ**). |
| **Pedido de uniformização / reclamação** | Divergência entre Turmas Recursais ou com súmula/tema do STJ | Conforme regimento | Disciplina local (Turma de Uniformização do TJBA / Res. STJ 3/2016). `[VERIFICAR NORMA DO TJBA]` |

### Honorários e custas

- Em 1º grau **não há custas nem honorários**, salvo litigância de má-fé (art. 55, *caput*).
- Em 2º grau, o **recorrente vencido** paga custas e honorários de 10% a 20% sobre o valor da condenação ou,
  não havendo condenação, do valor corrigido da causa (art. 55). Se o consumidor recorrer e perder, ele arca —
  avaliar risco e gratuidade antes de recorrer.
- A gratuidade pode ser pedida no próprio recurso; o preparo fica dispensado até decisão (CPC, art. 99, §7º).

## 5. Execução / cumprimento de sentença

- Cumprimento no próprio Juizado (art. 52). Multa do art. 523, §1º, CPC aplicável (entendimento prevalente) —
  `[VERIFICAR]` enunciado do FONAJE vigente.
- Pedir **bloqueio via SISBAJUD** diretamente quando o banco não paga no prazo.
- Astreintes: atenção ao limite de alçada — entendimento prevalente é que a multa pode superar 40 SM, mas
  pode ser reduzida (CPC, art. 537, §1º). `[VERIFICAR]` posição atual da Turma.

## 6. Checklist de peça para Juizado

- [ ] Endereçamento correto (Juízo do __º Juizado Especial Cível / de Defesa do Consumidor da Comarca de ___;
      no recurso, peça de interposição ao juízo *a quo* + razões à Turma Recursal).
- [ ] Número do processo no formato CNJ (NNNNNNN-DD.AAAA.8.05.OOOO — "8.05" = Justiça Estadual/TJBA).
- [ ] Tempestividade demonstrada (data da ciência e do termo final).
- [ ] Preparo ou pedido de gratuidade (recurso inominado).
- [ ] Referência aos eventos do PROJUDI.
- [ ] Pedidos certos e determinados; valores atualizados.
