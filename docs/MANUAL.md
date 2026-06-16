# Manual de Uso — GenIE

**GenIE** (Generic Extractor of Information Engine) extrai informação estruturada
de fontes heterogêneas — PDFs, planilhas, páginas web, bancos de dados, APIs —
usando LLMs, e entrega o resultado no formato e destino que você definir.

Ele opera de duas formas:

| Modo | Para quem | Como |
|---|---|---|
| **Independente** | Pessoas | Interface web em `http://localhost:8000` |
| **Extensão/Plugin** | Outras aplicações (TabEx, scripts, sistemas) | API REST (`/api/v1/...`) |

Nos dois modos o trabalho é feito pelos mesmos três agentes, em sequência:

```
┌──────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────┐
│ CONECTOR │ →  │ LOCALIZADOR │ →  │ ORGANIZADOR │ →  │ CONECTOR │
│ abre a   │    │ extrai o que│    │ formata no  │    │ entrega  │
│ fonte    │    │ foi pedido  │    │ padrão dado │    │ no destino│
└──────────┘    └─────────────┘    └─────────────┘    └──────────┘
   (I/O)           (LLM)              (LLM)              (I/O)
```

- **Conector** — toda a entrada e saída. Nunca chama LLM.
- **Localizador** — lê cada documento e extrai os campos pedidos via LLM.
- **Organizador** — reformata os registros conforme sua instrução. Se você não
  informar formato, os dados passam direto (custo zero de LLM).

---

## 1. Instalação

Requisitos: **Python 3.11+**.

```bash
git clone https://github.com/RMSantista/GenIE.git
cd GenIE
pip install -r requirements.txt

# opcional, recomendado em produção:
cp .env.example .env
# gere a chave-mestre de criptografia:
#   openssl rand -base64 32  →  cole em GENIE_MASTER_KEY no .env
# (sem isso, o GenIE gera uma automaticamente em ./data/.master_key)

uvicorn spec.main:app --port 8000
```

Abra **http://localhost:8000**. A documentação interativa da API fica em
**http://localhost:8000/docs**.

---

## 2. Modo independente (interface web)

A tela é dividida em **Configuração** (esquerda) e **Monitor de agentes** (direita).

### 2.1 Seção 01 — Modelo de IA

Escolha o modelo (Gemini, GPT ou Claude) e clique em **Nova API Key**.

- A chave é enviada **uma única vez** ao servidor, validada com uma chamada
  mínima ao provedor e gravada **cifrada (AES-256-GCM)**. Ela nunca volta ao
  navegador — você verá apenas os 4 primeiros caracteres mascarados.
- A chave é **por provedor**: cadastrar a chave do Google libera todos os
  modelos Gemini.
- Dica de custo: comece com `Gemini 2.5 Flash` ou `GPT-4o mini` (rápidos e
  baratos). Use `Claude Sonnet 4.6` ou `Gemini 2.5 Pro` para documentos
  difíceis.

### 2.2 Seção 02 — Origem dos dados (entrada)

| Tipo | O que informar | Exemplo |
|---|---|---|
| **URL** | Endereço http(s) de página, PDF ou JSON. Links de *arquivo* do Google Drive são convertidos para download direto | `https://lab.com/laudo.pdf` |
| **Pasta local** | Caminho de pasta ou arquivo no servidor onde o GenIE roda (varre subpastas) | `/home/voce/Documents/exames` |
| **Banco de dados** | URL do banco + usuário/senha. SQLite funciona nativamente; Postgres/MySQL exigem `pip install sqlalchemy` + driver | `sqlite:///dados.db` |
| **API REST** | Endpoint GET + Bearer token (opcional) | `https://api.servico.com/v1/exames` |
| **Upload** | Arraste os arquivos para a área indicada | `.pdf .csv .xlsx .json .txt .html` |

Formatos de arquivo aceitos: PDF (com texto), CSV/TSV, XLSX, JSON, TXT, MD,
HTML, XML, YAML, LOG.

### 2.3 Seção 03 — O que extrair

Instrução em linguagem natural para o Localizador. Seja específico sobre os
**campos** e seus **nomes**:

> Extraia, para cada exame encontrado, os campos: **data** (YYYY-MM-DD),
> **exame** (nome padronizado), **resultado** (valor com unidade) e
> **referencia** (faixa de referência). Ignore cabeçalhos, rodapés e dados de
> contato do laboratório.

O botão **Exemplo** preenche o formulário com um caso realista.

### 2.4 Seção 04 — Destino dos dados (saída)

| Tipo | O que acontece |
|---|---|
| **URL (webhook)** | POST com o JSON dos registros |
| **Pasta local** | Grava `output.json` + `output.csv` na pasta indicada |
| **Banco de dados** | Insere em tabela SQLite (cria a tabela e novas colunas automaticamente) |
| **API REST** | POST autenticado por Bearer token (em lote ou 1 chamada por registro) |
| **Download** | Gera links assinados de `JSON` e `CSV` válidos por 15 minutos |

### 2.5 Seção 05 — Formato da saída

Instrução em linguagem natural para o Organizador. Exemplos:

- `Envie 1 chamada POST por exame, com o body { "data": "YYYY-MM-DD", "exame": "...", "resultado": "..." }`
- `Agrupe os exames por data e gere um objeto por dia`
- *Vazio* → os registros extraídos são entregues como estão (sem custo extra de LLM).

### 2.6 Executando

Clique em **Enviar requisição**. No monitor você acompanha:

- os **3 cards de agentes** com progresso e status;
- o **log de execução** em tempo real (streaming);
- ao final, a **Saída entregue** com visualização em Tabela/JSON, botão de
  copiar e botões de download (quando a saída é Download).

**Interromper** cancela a execução no servidor (inclusive chamadas de LLM em
andamento). **Limpar** reinicia o monitor.

---

## 3. Modo extensão/plugin (API REST)

Qualquer aplicação pode usar o GenIE como serviço de extração. O contrato é:

```
1. (uma vez)  POST /api/v1/keys          → cadastra a chave do provedor LLM
2. (opcional) POST /api/v1/uploads       → envia arquivos, recebe upload_id
3.            POST /api/v1/runs          → cria a execução, recebe job_id
4a.           GET  /api/v1/runs/{id}/events  → acompanha por SSE (tempo real)
4b.           GET  /api/v1/runs/{id}         → ou consulta por polling
5.            resultado em result.records (+ links de download assinados)
```

### 3.1 Entrada `text` — a integração mais simples

Se a sua aplicação **já possui o texto** (ex.: OCR feito por ela), não é
preciso upload: envie o conteúdo inline em um único POST.

```bash
curl -s -X POST http://localhost:8000/api/v1/runs \
  -H 'Content-Type: application/json' \
  -d '{
    "model_id": "gemini-2.5-flash",
    "input":  { "type": "text", "content": "SODIO: 140 mEq/L\nCREATININA: 0,9 mg/dL", "name": "laudo.txt" },
    "prompt": "Extraia exame (minúsculas, sem acento) e resultado (número) de cada análise",
    "output": { "type": "download" }
  }'
# → {"job_id":"genie-ab12cd34ef","status":"queued"}

curl -s http://localhost:8000/api/v1/runs/genie-ab12cd34ef
# → {"status":"done","result":{"records":[{"exame":"sodio","resultado":140}, ...]}}
```

### 3.2 Exemplo em Python

```python
import httpx, time

GENIE = "http://localhost:8000/api/v1"

def extrair(texto: str, prompt: str) -> list[dict]:
    job = httpx.post(f"{GENIE}/runs", json={
        "model_id": "gemini-2.5-flash",
        "input": {"type": "text", "content": texto},
        "prompt": prompt,
        "output": {"type": "download"},
    }).json()

    while True:
        info = httpx.get(f"{GENIE}/runs/{job['job_id']}").json()
        if info["status"] in ("done", "error", "cancelled"):
            break
        time.sleep(1)

    if info["status"] != "done":
        raise RuntimeError(info["error"])
    return info["result"]["records"]
```

### 3.3 Exemplo em JavaScript (Node/browser) com SSE

```javascript
const GENIE = "http://localhost:8000/api/v1";

async function extrair(texto, prompt) {
  const { job_id } = await fetch(`${GENIE}/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model_id: "gemini-2.5-flash",
      input: { type: "text", content: texto },
      prompt,
      output: { type: "download" },
    }),
  }).then((r) => r.json());

  return new Promise((resolve, reject) => {
    const es = new EventSource(`${GENIE}/runs/${job_id}/events`);
    es.onmessage = (m) => {
      const ev = JSON.parse(m.data);
      console.log(`[${ev.agent}] ${ev.message || ""}`);     // log em tempo real
      if (ev.type === "finish") { es.close(); resolve(ev.result.records); }
      if (ev.type === "error")  { es.close(); reject(new Error(ev.message)); }
    };
  });
}
```

### 3.4 Entrega direta na sua aplicação

Em vez de buscar o resultado, a sua aplicação pode **recebê-lo**: configure a
saída como `api` (POST com Bearer token) ou `url` (webhook sem autenticação):

```json
"output": { "type": "api", "target": "https://sua-app.com/v1/importar", "token": "SEU_TOKEN" },
"format": "Envie 1 POST por registro com o body { \"campo\": ... } esperado pela minha API"
```

O Organizador adapta os payloads à sua descrição e o Conector faz as chamadas.

### 3.5 Upload de arquivos via API

```bash
UP=$(curl -s -F "files=@laudo.pdf" -F "files=@resultados.csv" \
     http://localhost:8000/api/v1/uploads | python3 -c "import json,sys;print(json.load(sys.stdin)['upload_id'])")

curl -s -X POST http://localhost:8000/api/v1/runs -H 'Content-Type: application/json' \
  -d "{\"model_id\":\"gemini-2.5-flash\",
       \"input\":{\"type\":\"upload\",\"upload_id\":\"$UP\"},
       \"prompt\":\"Extraia ...\",
       \"output\":{\"type\":\"download\"}}"
```

### 3.6 Referência rápida de endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/v1/models` | Modelos disponíveis + `has_key` |
| `POST` | `/api/v1/keys` | `{provider, key, validate_key}` → cifra e guarda |
| `DELETE` | `/api/v1/keys/{provider}` | Remove a chave |
| `POST` | `/api/v1/uploads` | multipart → `{upload_id, files}` |
| `POST` | `/api/v1/runs` | Cria execução → `{job_id}` |
| `GET` | `/api/v1/runs/{id}` | Estado + resultado final |
| `GET` | `/api/v1/runs/{id}/events` | SSE (suporta `Last-Event-ID` para reconexão) |
| `POST` | `/api/v1/runs/{id}/cancel` | Interrompe a execução |
| `GET` | `/api/v1/downloads/{id}/{arquivo}?exp=&sig=` | Artefatos (link assinado) |

Esquema completo (request/response) em `/docs` (OpenAPI).

---

## 4. Integração com o TabEx

### 4.1 O que o TabEx faz hoje

O [TabEx](https://github.com/RMSantista/TabEx) (Google Apps Script) automatiza
a tabulação de exames de sangue do SUS de Ribeirão Preto:

1. Um gatilho roda `processarNovosExames()` a cada 5 minutos;
2. `extrairTextoPDF()` faz OCR dos PDFs novos da pasta do Drive (Drive API);
3. `extrairData()` e `extrairResultados()` aplicam **regex fixas** para achar a
   data de coleta e **8 exames pré-definidos** (sódio, potássio, cálcio,
   magnésio, fósforo, ureia, creatinina, TFG);
4. `atualizarPlanilha()` grava na Google Sheets conforme o mapa `COLUNAS`;
5. O PDF é arquivado em subpastas por data.

**Onde ele quebra:** o passo 3. As regex assumem um único layout de laudo
(SUS-RP). Laudos de outros laboratórios, variações de formato ou OCR imperfeito
fazem a extração falhar — e cada exame novo exige programar mais regex.

### 4.2 Onde o GenIE entra

O GenIE substitui exatamente o passo 3 (a "inteligência"), mantendo o que o
TabEx já faz bem (monitorar o Drive, OCR nativo do Google e escrever na
planilha):

```
TabEx (Apps Script)                          GenIE (servidor)
───────────────────                          ────────────────
1. detecta PDF novo no Drive
2. OCR via Drive API  ──── texto ────────▶   3. POST /api/v1/runs
                                                 input: { type: "text", content: <texto OCR> }
                                                 prompt: "extraia data, exame, resultado…"
4. polling GET /runs/{id} ◀── records ───    Localizador extrai de QUALQUER layout
5. atualizarPlanilha(records)                Organizador padroniza nomes/números
6. arquiva o PDF
```

Ganhos imediatos:

- **Independência de layout** — laudos de qualquer laboratório/formato;
- **Novos exames sem código** — o Localizador devolve *todos* os exames do
  laudo; o TabEx pode criar colunas novas dinamicamente em vez de limitar-se
  aos 8 fixos;
- **Resiliência a OCR imperfeito** — o LLM entende `S0DIO`, `Sódio:`, quebras
  de linha etc., onde a regex falha.

### 4.3 Código de integração (Apps Script)

Substitua a chamada a `extrairResultados(texto)` por:

```javascript
// URL pública do seu servidor GenIE (ver requisito no item 4.4)
const GENIE_URL = 'https://seu-genie.exemplo.com';

function extrairComGenIE(textoOcr) {
  const criacao = UrlFetchApp.fetch(GENIE_URL + '/api/v1/runs', {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify({
      model_id: 'gemini-2.5-flash',
      input: { type: 'text', content: textoOcr, name: 'laudo-sus.txt' },
      prompt:
        'Este é o texto OCR de um laudo de exames de sangue do SUS. ' +
        'Extraia, para cada análise presente, os campos: ' +
        'data_coleta (YYYY-MM-DD), exame (nome em minúsculas sem acento, ex.: ' +
        'sodio, potassio, calcio, magnesio, fosforo, ureia, creatinina, tfg) ' +
        'e resultado (apenas o número). Inclua também exames fora dessa lista.',
      output: { type: 'download' }
    })
  });
  const jobId = JSON.parse(criacao.getContentText()).job_id;

  // Apps Script não suporta SSE — usar polling:
  for (let i = 0; i < 30; i++) {
    Utilities.sleep(2000);
    const info = JSON.parse(
      UrlFetchApp.fetch(GENIE_URL + '/api/v1/runs/' + jobId).getContentText()
    );
    if (info.status === 'done')  return info.result.records;
    if (info.status === 'error') throw new Error('GenIE: ' + info.error);
  }
  throw new Error('GenIE: tempo esgotado');
}

// Em processarNovosExames(), troque:
//   const resultados = extrairResultados(texto);
// por:
//   const registros = extrairComGenIE(texto);
//   → registros = [{data_coleta:'2025-12-08', exame:'sodio', resultado:140}, …]
```

Para aproveitar os exames novos, faça `atualizarPlanilha()` procurar a coluna
pelo nome do exame e **criar a coluna se não existir** — o GenIE passa a ditar
o schema, e a planilha cresce sozinha (decisão de projeto nº 3 do GenIE,
*Auto Schema Adaptation*).

### 4.4 Requisito de rede

O Apps Script roda nos servidores do Google, então o GenIE precisa estar
acessível por **HTTPS público**: um VPS, Cloud Run, ou um túnel
(`cloudflared tunnel`, `ngrok`) apontando para o seu GenIE local. Para testar
sem expor nada, cole o texto OCR direto na interface web do GenIE (entrada
Upload com um `.txt`) e confira a tabela extraída.

### 4.5 Fallback

Recomenda-se manter as regex atuais do TabEx como *fallback*: se o GenIE
estiver fora do ar (`try/catch` na `UrlFetchApp.fetch`), o TabEx volta ao
comportamento atual — alinhado ao princípio do GenIE de sempre haver
alternativa quando a IA está indisponível.

---

## 5. Outros cenários de uso (plugin ou standalone)

| Cenário | Entrada | Saída |
|---|---|---|
| Tabular exames de qualquer formato (TabEx) | `text` (OCR do app) ou `upload` | `api`/`download` |
| Garimpar dados em uma pasta e gerar base para apresentação | `path` | `path` (CSV/JSON) |
| Migrar dados entre bancos ajustando formato | `db` (origem) | `db` (destino) + *formato da saída* descrevendo o schema alvo |
| Carga em outro sistema a partir de sites | `url` (uma execução por site) | `api` do sistema alvo |
| Extração pontual de um arquivo | `upload` | `download` |

---

## 6. Segurança

- **Chaves de LLM**: cifradas em repouso com AES-256-GCM; chave-mestre via
  `GENIE_MASTER_KEY` (produção) ou arquivo local `data/.master_key` (0600).
  Nenhum endpoint devolve a chave em claro.
- **Credenciais por execução** (senha de banco, token de API): só em memória,
  nunca em logs, eventos ou resultados; URLs exibidas têm credenciais redigidas.
- **Filesystem**: leitura/escrita restritas ao home do usuário, ao diretório do
  projeto e a `ALLOWED_FS_ROOTS` — caminhos fora disso são recusados.
- **Uploads**: allowlist de extensões, nomes sanitizados, limites de tamanho e
  quantidade; lotes antigos são limpos automaticamente após 24 h.
- **Downloads**: links assinados (HMAC-SHA256) com validade de 15 minutos.
- **CORS**: allowlist explícita (`CORS_ORIGINS`).
- **Exposição pública**: o GenIE não tem autenticação de usuários embutida —
  ao publicá-lo na internet (caso TabEx), coloque-o atrás de um proxy com
  autenticação (Basic Auth/Nginx, Cloudflare Access, etc.).

## 7. Configuração (variáveis de ambiente)

| Variável | Padrão | Descrição |
|---|---|---|
| `GENIE_MASTER_KEY` | *(auto)* | Chave-mestre base64 de 32 bytes (`openssl rand -base64 32`) |
| `API_PORT` | `8000` | Porta do servidor |
| `CORS_ORIGINS` | localhost | Origens permitidas, separadas por vírgula |
| `ALLOWED_FS_ROOTS` | *(vazio)* | Raízes extras de filesystem, separadas por `:` |
| `MAX_UPLOAD_MB` | `50` | Tamanho máximo por arquivo |
| `MAX_FILES_PER_UPLOAD` | `20` | Arquivos por lote |
| `GOOGLE_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | *(vazio)* | Fallback por env (prefira cadastrar pela interface) |
| `DATA_DIR`, `UPLOADS_DIR`, `OUTPUTS_DIR`, `DB_PATH` | `./data/...` | Caminhos de dados |

## 8. Solução de problemas

| Sintoma | Causa provável / solução |
|---|---|
| "A chave informada foi recusada pelo provedor" | Chave inválida/expirada. Gere outra no console do provedor |
| "PDF não contém texto extraível (provavelmente digitalizado)" | O GenIE ainda não faz OCR. Use o OCR do Google Drive (como o TabEx) e mande o texto, ou um PDF nativo |
| "Acesso negado ao caminho ..." | Caminho fora das raízes permitidas — ajuste `ALLOWED_FS_ROOTS` |
| "Pastas do Google Drive exigem credenciais..." | Use link direto de arquivo, Upload ou Pasta local |
| "Para conectar a este banco instale sqlalchemy..." | `pip install sqlalchemy psycopg2-binary` (Postgres) ou `pymysql` (MySQL) |
| Extração veio vazia (`records: []`) | Refine o prompt: liste os campos com nomes explícitos e diga o que ignorar |
| Erro 429/503 no log | Limite de taxa do provedor — o GenIE tenta 3x com backoff; aguarde ou troque o modelo |
| Link de download "expirado" | Links valem 15 min — rode novamente ou use saída Pasta local |

## 9. Limitações conhecidas

- OCR de PDFs escaneados ainda não é nativo (planejado; contorno: OCR externo + entrada `text`).
- Arquivos `.docx` não são lidos (converta para PDF/TXT).
- Pastas do Google Drive exigem service account (não configurado).
- Saída direta em banco suporta SQLite nativamente (outros via SQLAlchemy).
- Execuções vivem em memória: reiniciar o servidor limpa o histórico de jobs
  (as chaves cifradas persistem).
