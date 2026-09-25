# processos/

Um diretório por processo, nomeado pelo número CNJ (`NNNNNNN-DD.AAAA.8.05.OOOO`):

```
processos/0001234-56.2026.8.05.0001/
├── ficha.md       # resumo do caso, histórico de eventos, prazos em aberto
├── autos/         # PDFs baixados do PROJUDI (evento-NN-descricao.pdf) + .txt extraídos
├── analises/      # análises de intimações e contestações
└── minutas/       # peças para revisão e protocolo
```

Use `/novo-processo <número>` para criar a estrutura a partir de `_modelo/`.

**Nada aqui é enviado ao GitHub** (ver `.gitignore`): documentos de clientes são protegidos por sigilo
profissional e pela LGPD. Faça backup desta pasta por outro meio seguro.
