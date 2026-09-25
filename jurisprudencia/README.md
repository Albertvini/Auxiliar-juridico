# jurisprudencia/

Fluxo que garante que **nenhum precedente entra numa peça sem ter sido conferido por você**:

```
pesquisa (agente, na web)  →  a-conferir.md  →  você confere  →  indice.md  →  pode ser citado
```

| Arquivo | Quem escreve | Pode ser citado em peça? |
|---|---|---|
| `a-conferir.md` | O agente, livremente, após pesquisar | **Não.** Na minuta, só como `[A CONFERIR: <link>]` (pendência visível) |
| `indice.md` | O agente, **só com a sua aprovação**: o Claude Code pede confirmação antes de gravar | **Sim**, e o verificador de citações passa a aceitar |
| `decisoes/` | Você (PDFs e textos integrais) | Base para conferência (não versionado) |

## Como conferir um precedente

1. Abra o link registrado em `a-conferir.md`, de preferência no **site oficial** do tribunal (o Jusbrasil
   serve para localizar; a conferência final deve ser na fonte oficial sempre que possível).
2. Confira: número, órgão julgador, relator, data de julgamento e publicação, e se o trecho transcrito é
   **literal**. Confira também se a decisão não foi reformada e se a tese é mesmo a que o agente resumiu.
3. Diga ao agente "confirmo o item X". Ele move o item para `indice.md` com a data da conferência (o Claude Code
   pedirá sua aprovação para gravar).
