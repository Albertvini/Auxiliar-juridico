---
name: analisar-contestacao
description: Analisa a contestação do banco em ação de consumo no PROJUDI/TJBA — preliminares, prescrição, mérito, documentos (contrato, assinatura, biometria, TED) — e monta o mapa de rebates e as provas a requerer.
argument-hint: <número do processo> [arquivo da contestação]
---

Analise a contestação do processo `$ARGUMENTS`.

- Confirme que a inicial e a contestação **com anexos** estão em `processos/<n>/autos/`. Se faltar algo,
  peça ao usuário para baixar do PROJUDI antes de prosseguir (a análise de contrato sem o anexo é inútil).
- Delegue ao subagente **analista-contestacao**.

Apresente ao usuário:
1. veredito em 3 linhas (a defesa é forte ou fraca? por quê?);
2. os 3 a 5 pontos decisivos para a impugnação;
3. provas a requerer;
4. riscos e perguntas para o cliente.

Ofereça redigir a impugnação com `/impugnacao`.
