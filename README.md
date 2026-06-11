# GenIE — Generic Extractor of Information Engine

Framework Python para extração inteligente de dados com LLMs, orquestrado por
três agentes cooperativos e operável por uma interface web completa.

```
Conector (I/O)  →  Localizador (extração via LLM)  →  Organizador (formato)  →  Conector (entrega)
```

## Interface Web

A SPA embutida (servida pelo próprio FastAPI em `http://localhost:8000`) permite:

1. **Modelo de IA** — escolher Gemini / GPT / Claude e cadastrar a API Key
   (cifrada com AES-256-GCM no servidor; nunca volta ao navegador).
2. **Entrada** — URL, pasta local, banco de dados, API REST ou upload de arquivos
   (PDF, CSV, XLSX, JSON, TXT, HTML…).
3. **O que extrair** — instrução em linguagem natural para o Localizador.
4. **Saída** — webhook, pasta local, banco SQLite, API REST (ex.: TabEx) ou download.
5. **Formato da saída** — instrução em linguagem natural para o Organizador.

O monitor à direita mostra os 3 agentes com progresso, log em tempo real (SSE)
e a prévia tabular/JSON do resultado, com links de download assinados.

## Quick Start

```bash
# 1. Instalar dependências (Python 3.11+)
pip install -r requirements.txt

# 2. (Opcional) Configurar ambiente
cp .env.example .env
# Gere a chave-mestre para produção: openssl rand -base64 32 → GENIE_MASTER_KEY
# Em desenvolvimento o GenIE gera uma automaticamente em ./data/.master_key

# 3. Rodar
uvicorn spec.main:app --port 8000
```

Abra **http://localhost:8000** — cadastre a API Key do provedor (ex.: Google
Gemini), envie um arquivo, descreva o que extrair e clique em *Enviar requisição*.

- Web app: http://localhost:8000
- Docs da API: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

## Segurança

- **API Keys nunca atravessam o navegador**: são enviadas uma única vez,
  cifradas com **AES-256-GCM** (chave-mestre via `GENIE_MASTER_KEY` ou arquivo
  `./data/.master_key`, modo 0600) e armazenadas em SQLite. Nenhum endpoint
  devolve a chave — apenas `has_key` e um preview mascarado.
- **Credenciais transitórias** (senha de banco, token de API por execução)
  ficam apenas em memória e nunca aparecem em logs, eventos SSE ou resultados.
- **Filesystem com allowlist**: o conector só lê/grava sob o home do usuário,
  o diretório do projeto e raízes extras de `ALLOWED_FS_ROOTS` (anti path traversal).
- **Uploads**: nomes sanitizados, allowlist de extensões, limites de tamanho
  (`MAX_UPLOAD_MB`) e quantidade (`MAX_FILES_PER_UPLOAD`).
- **Downloads assinados**: links HMAC-SHA256 com validade de 15 minutos.
- **CORS** restrito a uma allowlist explícita (`CORS_ORIGINS`).

## API da aplicação web

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/v1/models` | Catálogo de modelos + `has_key` por provedor |
| `GET` | `/api/v1/keys` | Provedores com chave (apenas preview mascarado) |
| `POST` | `/api/v1/keys` | `{provider, key, validate_key}` → valida e cifra |
| `DELETE` | `/api/v1/keys/{provider}` | Remove a chave |
| `POST` | `/api/v1/uploads` | multipart → `{upload_id, files}` |
| `POST` | `/api/v1/runs` | Cria execução → `{job_id}` |
| `GET` | `/api/v1/runs/{id}` | Estado atual + resultado |
| `GET` | `/api/v1/runs/{id}/events` | SSE com eventos dos agentes (suporta `Last-Event-ID`) |
| `POST` | `/api/v1/runs/{id}/cancel` | Interrompe a execução |
| `GET` | `/api/v1/downloads/{id}/{arquivo}` | Artefatos com link assinado |

Endpoints do framework (extração programática): `POST /api/v1/extract`,
`GET/POST /api/v1/providers*` — ver `/docs`.

### Exemplo de execução via API

```bash
# Upload
UP=$(curl -s -F "files=@exames.pdf" localhost:8000/api/v1/uploads | jq -r .upload_id)

# Run
curl -s -X POST localhost:8000/api/v1/runs -H 'Content-Type: application/json' -d "{
  \"model_id\": \"gemini-2.5-flash\",
  \"input\":  {\"type\": \"upload\", \"upload_id\": \"$UP\"},
  \"prompt\": \"Extraia Data, Nome do Exame, Resultado e Valor de Referência\",
  \"output\": {\"type\": \"download\"},
  \"format\": \"Um registro por exame com data ISO-8601\"
}"
```

## Conectores

| Tipo | Entrada | Saída |
|---|---|---|
| URL | HTML/PDF/JSON públicos; links de arquivo do Google Drive | POST webhook |
| Pasta local | varredura recursiva (allowlist de raízes) | `output.json` + `output.csv` |
| Banco de dados | SQLite nativo; Postgres/MySQL via SQLAlchemy opcional | SQLite (cria/evolui tabela) |
| API REST | GET com Bearer token | POST com Bearer (lote ou por registro) |
| Upload / Download | multipart seguro | links assinados (15 min) |

## Integração TabEx

O GenIE opera de forma independente e como serviço para outros apps.
Para entregar dados ao TabEx, use saída **API REST** apontando para o endpoint
do TabEx com o token de acesso, e descreva o body esperado no campo
*Formato da saída* — o Organizador monta os payloads e o Conector entrega.

## Estrutura

```
spec/
├── api/v1/endpoints/   # extract, providers, models, keys, uploads, runs, downloads
├── core/               # config, exceptions, security (AES-256-GCM), logging
├── extraction/
│   ├── agents/         # connector, locator, organizer, orchestrator
│   ├── llm/            # factory + providers (Google, OpenAI, Anthropic)
│   ├── parsers/        # pdf, text, content (csv/xlsx/html/json)
│   └── layout/         # fingerprint
├── models/             # Pydantic v2 (extraction, webapp, …)
├── search_library/     # padrões reutilizáveis (JSON)
├── webapp/             # catálogo de modelos + gestor de jobs/SSE
└── web/                # SPA (index.html, styles.css, app.js)
```

## Testes

```bash
pytest                      # suíte completa
pytest tests/unit -v        # unidade
pytest --cov=spec           # cobertura
```

## Documentação

- [Arquitetura](./docs/guides/GENIE-ARCHITECTURE.md)
- [Especificação v2](./docs/guides/GENIE-SPEC-v2.md)
- [Exemplos](./docs/examples/GENIE-EXAMPLES.md)

## Licença

MIT
