---
name: triagem
description: Triagem em lote das intimações do PROJUDI colocadas em entrada/ — identifica o processo de cada arquivo, arquiva nos autos, analisa todas em paralelo e entrega o painel de prazos ordenado por urgência. Use para o expediente diário.
argument-hint: [data de ciência padrão AAAA-MM-DD, se todas foram lidas no mesmo dia]
---

Faça a triagem das intimações em `entrada/`. Argumentos: `$ARGUMENTS`.

1. Liste os arquivos de `entrada/` (exceto README). Nenhum arquivo: avise e pare.
2. Extraia o texto: `python3 ferramentas/extrair_texto.py entrada`.
3. Para cada arquivo, identifique o **número CNJ** no texto (padrão `NNNNNNN-DD.AAAA.8.05.OOOO`), o evento e as
   datas de expedição/ciência que constarem. Arquivos sem número identificável: não adivinhe; liste-os ao final
   como "não identificados".
4. **Data de ciência:** use a informada em `$ARGUMENTS` ou a que constar no documento. Se não houver nenhuma,
   calcule os dois cenários (leitura hoje e intimação tácita pelo envio) e marque `[CONFIRMAR DATA DE CIÊNCIA]`.
5. Para cada processo: se não existir `processos/<n>/`, crie a partir de `processos/_modelo/` (como em
   `/novo-processo`, preenchendo o que der da ficha); mova o PDF e o .txt para `processos/<n>/autos/` com o nome
   `intimacao-<AAAA-MM-DD>-evento-<X>.<ext>`.
6. Acione o subagente **analista-intimacoes** para cada processo, **em paralelo** (várias chamadas na mesma
   mensagem), passando o arquivo, as datas e a instrução de ser conciso (resumo em 30 segundos + prazo +
   providência + pendências).
7. Rode `python3 ferramentas/painel_prazos.py` e apresente:
   - o **painel** (vencidos/hoje/urgentes primeiro);
   - uma linha por intimação: processo · ato · resultado para o consumidor · providência · vencimento;
   - arquivos não identificados e pendências.
8. Ofereça os próximos passos em lote (ex.: "redigir as 3 contrarrazões e os 2 embargos agora?"). Não redija
   sem o advogado escolher.
