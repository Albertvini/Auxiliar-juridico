---
name: novo-processo
description: Cadastra um novo processo do PROJUDI/TJBA — cria a pasta processos/<numero>, organiza os documentos baixados e preenche a ficha do caso (partes, matéria bancária, pedidos, fase, prazos). Use quando o usuário trouxer um processo novo.
argument-hint: <número CNJ do processo> [caminho dos PDFs]
---

Cadastre o processo `$ARGUMENTS`.

1. Crie `processos/<numero-CNJ>/` copiando a estrutura de `processos/_modelo/` (`autos/`, `analises/`,
   `minutas/`, `ficha.md`). Use o número no formato `NNNNNNN-DD.AAAA.8.05.OOOO`.
2. Se o usuário indicou documentos, mova/copie-os para `autos/`, renomeando como
   `evento-<NN>-<descricao>.pdf` quando o número do evento do PROJUDI for identificável.
3. Rode `python3 ferramentas/extrair_texto.py processos/<n>/autos`.
4. Leia a inicial e demais peças disponíveis e preencha `ficha.md`: partes, juízo, **comarca (para prazos)**, matéria (conforme
   `conhecimento/teses-por-materia.md`), contratos discutidos, pedidos e valores, tutela, fase atual, histórico
   de eventos, prazos em aberto. Campos desconhecidos: `[CONFIRMAR]`.
   Se a comarca não for Salvador e não houver feriados dela em `ferramentas/feriados_extras.txt`, avise o
   advogado e peça as datas (padroeiro, emancipação), sem inventá-las.
5. Se houver intimação pendente ou contestação sem análise, diga ao usuário e sugira `/analisar-intimacao` ou
   `/analisar-contestacao`.

Responda com um resumo do caso em até 12 linhas e a lista de pendências.
