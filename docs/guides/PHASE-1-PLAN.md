# PHASE 1: MVP CORE - PLANO EXECUTÁVEL DETALHADO

Com base na análise completa da documentação do GENIE, aqui está um plano descomposição detalhado e pronto para implementação da Phase 1:

---

## OVERVIEW EXECUTIVO

**Timeline Estimado:** 4-6 semanas (50+ tasks)
**Arquitetura:** Python 3.11+ / FastAPI / Pydantic v2 / Anthropic API
**Dependências Críticas:** Nenhuma (começar do zero)
**Métricas de Sucesso:**
- API REST funcional com health check passando
- Extração com LLM (Anthropic) operacional
- Search Library (JSON) salvando patterns
- End-to-end: text input → LLM → structured output
- Coverage >= 80%

---

## 1.1 PROJECT SETUP (Semana 1)

### 1.1.1 Repository & Tooling
**Objetivo:** Repositório configurado, dependências instaladas, CI/CD pronto

**Critério de Sucesso:**
- `poetry install` executa sem erros
- `pyproject.toml` contém todas as deps
- `.env.example` tem todos os vars
- `git status` mostra apenas files importantes

**Tasks Decompostas:**

1. **Initialize Git & .gitignore** [S]
   - Criar `.gitignore` com patterns Python, IDE, venv, .env
   - Executar `git init`
   - Primeiro commit: "Initialize repository with base gitignore"

2. **Create pyproject.toml with Poetry** [M]
   - Nome: `genie`, versão: `0.1.0`
   - Python: `^3.11`
   - Dependências principais:
     ```
     fastapi==0.110.0
     uvicorn[standard]==0.27.0
     pydantic==2.6.0
     pydantic-settings==2.2.0
     anthropic==0.18.0
     openai==1.12.0
     PyPDF2==3.0.0
     python-multipart==0.0.9
     cryptography==42.0.0
     ```
   - Dev dependencies: pytest, pytest-asyncio, pytest-cov, ruff, mypy, black
   - Build system: poetry-core
   - Black config: line-length=88, target-version=['py311']
   - Ruff config: select=["E", "F", "I", "N", "W"]
   - Pytest config: asyncio_mode="auto", testpaths=["tests"]

3. **Create .env.example** [S]
   - Variáveis: ENVIRONMENT, LOG_LEVEL, ANTHROPIC_API_KEY, OPENAI_API_KEY, DATA_DIR, SEARCH_LIBRARY_PATH, API_HOST, API_PORT
   - Sem valores reais (apenas placeholders)

4. **Create config/development.yaml** [S]
   - Settings para desenvolvimento
   - Debug mode: true
   - Log level: DEBUG
   - Storage type: json

5. **Add core dependencies** [S]
   ```bash
   poetry add fastapi uvicorn pydantic pydantic-settings anthropic
   poetry add --group dev pytest pytest-asyncio black ruff mypy
   ```

6. **Setup ruff & mypy** [S]
   - Ruff configuration em pyproject.toml
   - Mypy configuration em pyproject.toml
   - Criar `.ruff.toml` (opcional)

**Componentes a Criar:**
- `pyproject.toml` (root)
- `.env.example`
- `config/development.yaml`
- `.gitignore` atualizado

**Testes:**
- `tests/unit/test_config.py` - validar settings carregam
- `tests/unit/test_dependencies.py` - validar imports

---

### 1.1.2 Folder Structure
**Objetivo:** Estrutura de pastas completa, todos os `__init__.py` existem

**Critério de Sucesso:**
- Cada diretório tem `__init__.py`
- Estrutura matches GENIE-ARCHITECTURE.md
- Zero import errors ao fazer `from genie import *`

**Tasks Decompostas:**

1. **Create main package directories** [M]
   ```
   mkdir -p genie/{api/v1/{endpoints,middleware},core,models,extraction/{llm,layout,parsers,ocr,agents},
            search_library,output/{adapters},mcp,utils}
   ```

2. **Create test directories** [S]
   ```
   mkdir -p tests/{unit,integration,fixtures/{sample_pdfs,sample_images}}
   ```

3. **Create data directories** [S]
   ```
   mkdir -p data/{search_library,uploads}
   touch data/.gitkeep data/search_library/.gitkeep data/uploads/.gitkeep
   ```

4. **Create docs & scripts** [S]
   ```
   mkdir -p docs/{api,guides,examples}
   mkdir -p scripts
   ```

5. **Add __init__.py to all packages** [S]
   - Todos os diretórios recebem um `__init__.py` vazio ou com docstring

6. **Create module docstrings** [S]
   - `genie/__init__.py` - Package docstring
   - `genie/api/__init__.py`
   - `genie/core/__init__.py`
   - etc.

**Componentes a Criar:**
- Diretório structure completa
- Todos os `__init__.py` files

**Testes:**
- Script para validar import em cada módulo

---

### 1.1.3 Core Infrastructure
**Objetivo:** App FastAPI inicializa, config carrega, logging funciona

**Critério de Sucesso:**
- `uvicorn genie.main:app --reload` inicia sem erro
- GET `/health` retorna `{"status": "healthy"}`
- Logs aparecem em stdout e em arquivo
- Exceções customizadas podem ser lançadas

**Tasks Decompostas:**

1. **Implement genie/core/config.py** [M]
   - Classe `Settings` com Pydantic
   - Fields:
     ```python
     environment: str = "development"
     log_level: str = "INFO"
     api_host: str = "0.0.0.0"
     api_port: int = 8000
     data_dir: str = "./data"
     search_library_path: str = "./data/search_library/patterns.json"
     anthropic_api_key: str | None = None
     openai_api_key: str | None = None
     ```
   - Config dict com `env_file = ".env"`
   - Método `get_settings()` como singleton

2. **Implement genie/core/exceptions.py** [M]
   - Base `GenieException(Exception)`
   - `LayoutNotRecognized`
   - `ExtractionFailed`
   - `LLMProviderError`
   - `InvalidConfig`
   - `StorageError`
   - Todos com docstrings

3. **Implement genie/core/logging_config.py** [M]
   - Função `setup_logging(log_level: str) -> logging.Logger`
   - Console handler (stdout)
   - File handler (logs/genie.log)
   - Formato: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
   - Criar `logs/` directory if needed

4. **Implement genie/core/security.py** [S]
   - Classe `SecureKeyStore` (placeholder)
   - Métodos `store_api_key()`, `get_api_key()`
   - (Full implementation em Phase 5)

5. **Implement genie/main.py** [M]
   - FastAPI app instance
   - CORS middleware (allow all for dev)
   - Lifespan context manager:
     - On startup: setup logging, load config
     - On shutdown: cleanup
   - Include router v1
   - Settings como dependency

6. **Implement genie/api/v1/endpoints/health.py** [S]
   - Route: `GET /health`
   - Response: `{"status": "healthy", "version": "0.1.0"}`
   - Type-hinted response model

7. **Implement genie/api/v1/dependencies.py** [M]
   - Função `get_settings()` → Settings singleton
   - Função `get_logger()` → Logger
   - (Outras dependencies added later)

8. **Implement genie/api/v1/router.py** [S]
   - Include health router
   - Agregador de routers (para adicionar depois)

9. **Test integration** [M]
   - `tests/integration/test_health.py`:
     ```python
     def test_health_endpoint():
         client = TestClient(app)
         response = client.get("/health")
         assert response.status_code == 200
         assert response.json()["status"] == "healthy"
     ```

**Componentes a Criar:**
- `genie/main.py`
- `genie/core/config.py`
- `genie/core/exceptions.py`
- `genie/core/logging_config.py`
- `genie/core/security.py` (placeholder)
- `genie/api/v1/endpoints/health.py`
- `genie/api/v1/dependencies.py`
- `genie/api/v1/router.py`

**Testes:**
- `tests/unit/test_config.py`
- `tests/unit/test_exceptions.py`
- `tests/integration/test_health.py`

**Quality Gate 1.1:**
```bash
✓ Server starts: uvicorn genie.main:app --reload
✓ Health check: curl http://localhost:8000/health → {"status": "healthy"}
✓ All tests pass: pytest tests/
✓ Logging works: logs appear in stdout and logs/genie.log
✓ No import errors
```

---

## 1.2 BASE MODELS & LLM EXTRACTION (Semana 2-3)

### 1.2.1 Pydantic Models
**Objetivo:** Modelos de dados validados, type-hinted, pronto para API

**Critério de Sucesso:**
- Todos os modelos passam validação Pydantic
- Type hints em 100% dos fields
- Docstrings em todos
- JSON schema exportável

**Tasks Decompostas:**

1. **Implement genie/models/extraction.py** [M]
   - `ExtractionRequest`:
     ```python
     config_id: str
     source: Dict[str, Any]  # type, content/path, etc.
     force_llm: bool = False
     options: Optional[Dict[str, Any]] = None
     ```
   - `ExtractionResponse`:
     ```python
     extraction_id: str
     status: str  # "success" ou "error"
     method_used: str  # "llm" ou "search_library"
     data: Dict[str, Any]
     confidence: float
     processing_time_ms: int
     layout_fingerprint: Optional[str] = None
     error: Optional[str] = None
     ```
   - Validator para `status` e `method_used` (enums)

2. **Implement genie/models/config.py** [M]
   - `InputConfig`:
     ```python
     type: str  # "pdf", "text", "file", etc.
     source: Optional[str] = None
     access_mode: str = "local_secure"
     ```
   - `OutputConfig`:
     ```python
     type: str  # "json", "csv", "xlsx", etc.
     destination: Optional[str] = None
     schema: Optional[Dict[str, str]] = None
     auto_adapt: bool = True
     ```
   - `LLMConfig`:
     ```python
     provider: str  # "anthropic", "openai"
     model: str
     api_key_ref: Optional[str] = None
     fallback_to_ocr: bool = False
     temperature: float = 0.0
     max_tokens: int = 4096
     ```
   - `BehaviorConfig`:
     ```python
     use_search_library: bool = True
     auto_create_patterns: bool = True
     layout_independent: bool = True
     update_on_change: bool = True
     ```
   - `ExtractionConfig`:
     ```python
     extraction_id: str
     name: Optional[str] = None
     input: InputConfig
     output: OutputConfig
     llm: LLMConfig
     behavior: BehaviorConfig
     extraction_instructions: str
     ```

3. **Implement genie/models/library.py** [S]
   - `PatternField`:
     ```python
     field_name: str
     extraction_method: str  # "regex", "instruction", "query"
     pattern: Optional[str] = None
     instruction: Optional[str] = None
     validation: Optional[str] = None
     post_process: Optional[str] = None
     ```
   - `SearchPattern`:
     ```python
     layout_id: str
     config_id: str
     fingerprint: str
     created_at: datetime
     last_used: datetime
     success_rate: float = 1.0
     use_count: int = 0
     fields: List[PatternField]
     ```
   - `LibraryMetadata`:
     ```python
     version: str
     total_patterns: int
     last_updated: datetime
     ```

4. **Implement genie/models/output.py** [S]
   - `FieldDefinition`:
     ```python
     name: str
     type: str  # "string", "integer", "date", etc.
     required: bool = False
     ```
   - `OutputSchema`:
     ```python
     fields: Dict[str, FieldDefinition]
     primary_key: Optional[str] = None
     ```

5. **Write comprehensive tests** [M]
   - `tests/unit/test_models.py`:
     - Test ExtractionRequest validation
     - Test ExtractionResponse serialization
     - Test ExtractionConfig nested models
     - Test invalid data rejection

**Componentes a Criar:**
- `genie/models/extraction.py`
- `genie/models/config.py`
- `genie/models/library.py`
- `genie/models/output.py`

**Testes:**
- `tests/unit/test_models.py` (comprehensive)

**Quality Gate 1.2.1:**
```bash
✓ All models validate correctly
✓ JSON schema exports without error
✓ Type hints pass mypy check
✓ Test coverage >= 80% for models
```

---

### 1.2.2 LLM Provider Interface & Anthropic
**Objetivo:** Interface para LLMs, implementação Anthropic funcional

**Critério de Sucesso:**
- `AnthropicProvider.extract()` retorna dados estruturados
- Prompt building otimizado para Claude
- JSON parsing robusto (remove markdown, trata erros)
- Mock tests passam (sem chamar API real)

**Tasks Decompostas:**

1. **Implement genie/extraction/llm/base.py** [M]
   - ABC `BaseLLMProvider`:
     ```python
     @abstractmethod
     async def extract(content: str, schema: Dict[str, Any]) -> Dict[str, Any]

     @abstractmethod
     def _build_prompt(content: str, schema: Dict[str, Any]) -> str

     @abstractmethod
     def _parse_response(response) -> Dict[str, Any]
     ```
   - Docstrings detalhadas

2. **Implement genie/extraction/llm/anthropic.py** [L]
   - `AnthropicProvider(BaseLLMProvider)`:
     - Constructor: recebe `api_key` e `model` (default: claude-sonnet-4-20250514)
     - Initializa `AsyncAnthropic` client
     - Método `async extract()`:
       - Chama `_build_prompt()`
       - Faz chamada à API Anthropic com `client.messages.create()`
       - Chama `_parse_response()`
       - Retorna dados ou lança `LLMProviderError`
     - Método `_build_prompt()`:
       - Instrução clara em português
       - Schema em JSON formatado
       - Instruções para retornar APENAS JSON
       - ~200 tokens máximo
     - Método `_parse_response()`:
       - Remove markdown (```json...```)
       - `json.loads()` com error handling
       - Retorna dict ou lança erro
     - Error handling:
       - Timeout → LLMProviderError
       - Invalid JSON → LLMProviderError
       - Missing API key → LLMProviderError

3. **Implement genie/extraction/llm/factory.py** [M]
   - `LLMProviderFactory`:
     - Método `get_provider(config: LLMConfig) -> BaseLLMProvider`
     - Switch case por provider name
     - Fallback → raise `InvalidConfig`
     - Caching de instances (opcional)

4. **Implement placeholder openai.py** [S]
   - `OpenAIProvider` skeleton
   - Abstract methods todo (levanta NotImplementedError)
   - Docstring: "Implementar na Phase 2"

5. **Write mock tests** [M]
   - `tests/unit/test_llm_providers.py`:
     - Mock `AsyncAnthropic` com `patch()`
     - Test `_build_prompt()` format
     - Test `_parse_response()` handling markdown
     - Test error cases (invalid JSON, timeout)
     - Test factory instantiation
     - **SEM** chamar API real

6. **Create test script for real connection** [S]
   - `scripts/test_llm_connection.py`:
     - Usa env var `ANTHROPIC_API_KEY`
     - Faz extraction simples (opcional, só se key disponível)
     - Documenta como usar

**Componentes a Criar:**
- `genie/extraction/llm/base.py`
- `genie/extraction/llm/anthropic.py`
- `genie/extraction/llm/factory.py`
- `genie/extraction/llm/openai.py` (placeholder)
- `scripts/test_llm_connection.py`

**Testes:**
- `tests/unit/test_llm_providers.py` (100% mocked)

**Quality Gate 1.2.2:**
```bash
✓ Mock tests pass without API key
✓ Prompt building produces valid JSON instruction
✓ JSON parsing handles markdown cleanup
✓ Factory creates correct provider instance
✓ Type hints on all methods
```

---

### 1.2.3 Text Parser & Basic Extraction
**Objetivo:** Extrair dados via LLM, endpoint POST /api/v1/extract funcional

**Critério de Sucesso:**
- POST `/api/v1/extract` com text source retorna extracted data
- LLM é chamado e resposta parseada corretamente
- Extraction ID é gerado e timing é calculado
- End-to-end: request → LLM → response

**Tasks Decompostas:**

1. **Implement genie/extraction/parsers/text.py** [M]
   - `TextParser`:
     ```python
     async def extract_text(source: Dict[str, Any]) -> str:
         if source["type"] == "text":
             return source["content"]
         elif source["type"] == "file" and source["path"].endswith(".txt"):
             return Path(source["path"]).read_text()
         else:
             raise InvalidConfig(...)
     ```

2. **Implement genie/extraction/engine.py - skeleton** [S]
   - `ExtractionEngine` class:
     - Constructor: recebe `search_library`, `llm_factory`, `output_manager`
     - Método `async extract(request: ExtractionRequest) -> ExtractionResponse`:
       - Por enquanto, LLM-only flow (sem Search Library)
       - Chama `_read_content(request.source)` → content
       - Chama LLM `extract(content, schema)`
       - Retorna `ExtractionResponse`
     - Método privado `_read_content()`:
       - Dispatch por source["type"]
       - Para "text" → use TextParser
       - Para outros → NotImplementedError
     - Método `_calculate_confidence()`: retorna 0.95 por enquanto

3. **Implement genie/api/v1/endpoints/extract.py** [M]
   - Route: `POST /api/v1/extract`
   - Endpoint `extract_data(request: ExtractionRequest, engine: ExtractionEngine = Depends(get_extraction_engine))`
   - Lógica:
     - Start timer
     - Chama `engine.extract(request)`
     - Return `ExtractionResponse`
     - Exception handling → 500 error
   - Response model: `ExtractionResponse`

4. **Update genie/api/v1/dependencies.py** [M]
   - Função `get_extraction_engine() -> ExtractionEngine`:
     - Cria instances de search_library, llm_factory, output_manager
     - Retorna ExtractionEngine
     - (Aqui você poderia usar cache/singleton depois)

5. **Update genie/api/v1/router.py** [S]
   - Include extract router

6. **Write integration tests** [M]
   - `tests/integration/test_api.py`:
     ```python
     def test_extract_text(client):
         response = client.post("/api/v1/extract", json={
             "config_id": "test",
             "source": {
                 "type": "text",
                 "content": "Nome: João\nIdade: 35"
             }
         })
         assert response.status_code == 200
         data = response.json()
         assert data["status"] == "success"
         assert data["method_used"] == "llm"
         assert "extraction_id" in data
         assert "data" in data
     ```
   - Mock do LLMProvider

7. **Write unit tests for parsers** [S]
   - `tests/unit/test_parsers.py`:
     - Test TextParser with "text" source
     - Test TextParser with invalid source

**Componentes a Criar:**
- `genie/extraction/parsers/text.py`
- `genie/extraction/engine.py` (skeleton)
- `genie/api/v1/endpoints/extract.py`

**Testes:**
- `tests/unit/test_parsers.py`
- `tests/integration/test_api.py`

**Quality Gate 1.2.3:**
```bash
✓ POST /api/v1/extract returns 200 with valid response
✓ Extraction ID is generated
✓ Processing time is calculated
✓ LLM is called correctly
✓ Response contains extracted data in correct schema
✓ All integration tests pass
```

---

## 1.3 PDF SUPPORT & LAYOUT FINGERPRINTING (Semana 3-4)

### 1.3.1 PDF Parser
**Objetivo:** Extrair texto de PDFs, detectar scanned PDFs

**Critério de Sucesso:**
- PDFParser extrai texto de native PDFs
- Scanned PDF detection funciona
- API aceita `source["type"] == "file"` com PDFs

**Tasks Decompostas:**

1. **Add PyPDF2 dependency** [S]
   - `poetry add PyPDF2`

2. **Implement genie/extraction/parsers/pdf.py** [M]
   - `PDFParser`:
     ```python
     async def extract_text(filepath: str, detect_scanned: bool = True) -> str:
         with open(filepath, 'rb') as f:
             reader = PyPDF2.PdfReader(f)
             text = ""
             for page_num, page in enumerate(reader.pages):
                 page_text = page.extract_text()
                 if not page_text or len(page_text) < 10:
                     # Scanned PDF detection
                     if detect_scanned:
                         raise ScannedPDFDetected(f"Page {page_num}")
                 text += page_text + "\n"
         return text.strip()
     ```
   - Exception: `ScannedPDFDetected` (subclass de `ExtractionError`)
   - Error handling: file not found, corrupt PDF, etc.

3. **Update ExtractionEngine._read_content()** [M]
   - Dispatch por source["type"]:
     - "text" → TextParser
     - "file" ou "pdf" → PDFParser
     - Caminho do arquivo em source["path"]

4. **Update POST /api/v1/extract** [S]
   - Já funciona (só mudou o _read_content)

5. **Add sample PDFs to fixtures** [S]
   - `tests/fixtures/sample_pdfs/simple_text.pdf`
   - `tests/fixtures/sample_pdfs/layout_a.pdf`
   - (Pode ser criados com reportlab ou usar PDFs reais)

6. **Write unit tests** [M]
   - `tests/unit/test_parsers.py`:
     - Test PDF text extraction
     - Test scanned PDF detection
     - Test file not found error

**Componentes a Criar:**
- `genie/extraction/parsers/pdf.py`
- Sample PDFs em fixtures

**Testes:**
- Update `tests/unit/test_parsers.py` com PDF tests

**Quality Gate 1.3.1:**
```bash
✓ PDFParser extracts text from native PDF
✓ Scanned PDF raises exception
✓ API accepts "file" source type
✓ Multiple pages are concatenated
```

---

### 1.3.2 Layout Fingerprint Algorithm
**Objetivo:** Gerar fingerprint único para cada layout, comparar similaridade

**Critério de Sucesso:**
- Same layout + different data = same fingerprint
- Different layouts = different fingerprints
- Similarity score is deterministic

**Tasks Decompostas:**

1. **Implement genie/extraction/layout/fingerprint.py** [L]
   - `LayoutFingerprint`:
     ```python
     def generate(self, content: str) -> str:
         """Gera hash de 16 chars da estrutura."""
         structure = self._extract_structure(content)
         return hashlib.sha256(structure.encode()).hexdigest()[:16]

     def _extract_structure(self, content: str) -> str:
         """Remove dados variáveis, mantém estrutura."""
         # 1. Substitui números por "N"
         # 2. Mantém labels (linhas com :)
         # 3. Substitui nomes próprios (palavras capitalizadas) por "X"
         # 4. Normaliza espaços
         # 5. Retorna string da estrutura
         ...

     def similarity(self, fp1: str, fp2: str) -> float:
         """Hamming distance entre fingerprints (0-1)."""
         if fp1 == fp2:
             return 1.0
         matches = sum(c1 == c2 for c1, c2 in zip(fp1, fp2))
         return matches / max(len(fp1), len(fp2))
     ```
   - Estratégia:
     - Remove números (substitui por N)
     - Remove valores de data/hora (substitui por D)
     - Mantém estrutura (labels, pontuação, quebras de linha)
     - Normaliza múltiplos espaços
     - Hash SHA256 truncado a 16 chars

2. **Update ExtractionEngine.extract()** [M]
   - Chama `fingerprinter.generate(content)` após ler
   - Armazena em `response.layout_fingerprint`
   - Usa para buscar patterns na library (próxima task)

3. **Write comprehensive tests** [L]
   - `tests/unit/test_fingerprint.py`:
     - Same layout, different data → same fingerprint
     - Different layouts → different fingerprints
     - Similarity scoring
     - Edge cases (empty, very short content)
     - Sample documents for testing

**Componentes a Criar:**
- `genie/extraction/layout/fingerprint.py`

**Testes:**
- `tests/unit/test_fingerprint.py` (comprehensive)

**Quality Gate 1.3.2:**
```bash
✓ Fingerprints are deterministic
✓ Similarity score is 0-1 float
✓ Different layouts produce different hashes
✓ Same layout produces consistent hash
```

---

## 1.4 SEARCH LIBRARY & REST API (Semana 4-5)

### 1.4.1 JSON Storage Implementation
**Objetivo:** Search Library em JSON, CRUD pattern, thread-safe

**Critério de Sucesso:**
- JSONStorage salva patterns corretamente
- Patterns são recuperados por fingerprint
- Success rate é rastreado
- Concorrência é segura (locks)

**Tasks Decompostas:**

1. **Implement genie/search_library/base.py** [M]
   - ABC `BaseStorage`:
     ```python
     @abstractmethod
     async def find_pattern(self, fingerprint: str, config_id: str) -> Optional[Dict]:
         pass

     @abstractmethod
     async def save_pattern(self, fingerprint: str, config_id: str, pattern: Dict) -> None:
         pass

     @abstractmethod
     async def update_success_rate(self, fingerprint: str, success: bool) -> None:
         pass

     @abstractmethod
     async def list_patterns(self, config_id: Optional[str] = None) -> List[Dict]:
         pass
     ```

2. **Implement genie/search_library/json_storage.py** [L]
   - `JSONStorage(BaseStorage)`:
     - Constructor: `path: str` (default: "data/search_library/patterns.json")
     - `_ensure_storage_exists()`: cria arquivo se não existe
     - `async find_pattern()`:
       - Carrega JSON (ou from memory cache)
       - Busca por fingerprint + config_id
       - Atualiza `last_used` e `use_count`
       - Salva storage
       - Retorna pattern ou None
     - `async save_pattern()`:
       - Gera `layout_id` único
       - Cria dict com metadata
       - Appenda a patterns array
       - Atualiza metadata.total_patterns
       - Salva no disco
     - `async update_success_rate()`:
       - Busca pattern por fingerprint
       - Calcula média móvel
       - Success: +1.0, Failure: +0.0
       - Salva
     - `async list_patterns()`: retorna todos ou filtered por config_id
     - Thread-safety: use `asyncio.Lock()` para write operations
     - Caching: in-memory cache com invalidation

3. **Implement genie/search_library/matcher.py** [M]
   - `PatternMatcher`:
     ```python
     async def extract_with_pattern(self, content: str, pattern: Dict) -> Dict:
         """Aplica pattern (REGEX) contra conteúdo."""
         extracted = {}
         for field in pattern["fields"]:
             if field["extraction_method"] == "regex":
                 match = re.search(field["pattern"], content)
                 extracted[field["field_name"]] = match.group(1) if match else None
             # "instruction" e "query" methods in Phase 2
         return extracted

     async def validate_extraction(self, data: Dict, pattern: Dict) -> bool:
         """Valida dados contra padrões de validação."""
         for field in pattern["fields"]:
             if field.get("validation"):
                 value = data.get(field["field_name"])
                 if not re.match(field["validation"], str(value)):
                     return False
         return True
     ```

4. **Write comprehensive tests** [M]
   - `tests/unit/test_search_library.py`:
     - Test save_pattern
     - Test find_pattern (hit and miss)
     - Test success_rate updating
     - Test list_patterns filtering
     - Test pattern matching with REGEX
     - Test validation
     - Concurrent operations

**Componentes a Criar:**
- `genie/search_library/base.py`
- `genie/search_library/json_storage.py`
- `genie/search_library/matcher.py`

**Testes:**
- `tests/unit/test_search_library.py`

**Quality Gate 1.4.1:**
```bash
✓ JSONStorage CRUD works
✓ Pattern lookup by fingerprint works
✓ Success rate calculation is correct
✓ File I/O is thread-safe
✓ Concurrent operations handled
```

---

### 1.4.2 ExtractionEngine Full Flow
**Objetivo:** Engine completo: fingerprint → library → LLM fallback → save pattern

**Critério de Sucesso:**
- Library hit: pattern encontrado, extraction sem LLM
- Library miss: LLM usado, pattern salvo
- force_llm: bypassa library
- Pattern auto-save com sucesso

**Tasks Decompostas:**

1. **Complete genie/extraction/engine.py** [L]
   - `async extract(request)`:
     - 1. Read content
     - 2. Generate fingerprint
     - 3. Lookup pattern in library
     - 4. If found → matcher.extract_with_pattern() → data, method="search_library"
     - 5. If not found or force_llm → LLM extract → data, method="llm"
     - 6. If method=="llm" and auto_create_patterns → generate pattern and save
     - 7. Adapt output (placeholder)
     - 8. Return response
   - Error handling por cada stage
   - Logging com extraction_id e fingerprint
   - Confidence calculation:
     - search_library: 0.95
     - llm: 0.90
     - (mais refinado depois)

2. **Implement pattern auto-save** [M]
   - Método `_generate_pattern_from_extraction()`:
     - Analisa content e extracted data
     - Cria pattern dict com fields
     - (Geração automática de REGEX é Phase 2 - por enquanto: placeholder)
     - Retorna pattern dict
   - Chama `library.save_pattern()` com fingerprint, config_id, pattern

3. **Update dependencies.py** [M]
   - `get_extraction_engine()`:
     - Cria search_library
     - Cria llm_factory
     - Cria output_manager (placeholder)
     - Retorna ExtractionEngine

4. **Write unit tests** [L]
   - `tests/unit/test_extraction_engine.py`:
     - Library hit path
     - Library miss path
     - Pattern save after LLM
     - force_llm bypass
     - Error handling
     - Fingerprinting
     - All with mocks

**Componentes a Criar:**
- Atualizar `genie/extraction/engine.py`

**Testes:**
- `tests/unit/test_extraction_engine.py`

**Quality Gate 1.4.2:**
```bash
✓ Library hit returns pattern-based extraction
✓ Library miss triggers LLM
✓ Pattern saved after successful LLM
✓ force_llm bypasses library
✓ Confidence scores are correct
✓ All extraction flows tested
```

---

### 1.4.3 REST API Completion
**Objetivo:** Endpoints para config CRUD e library management

**Critério de Sucesso:**
- POST /api/v1/configs → cria e retorna config
- GET /api/v1/configs/{config_id} → retrieves config
- PUT /api/v1/configs/{config_id} → updates config
- DELETE /api/v1/configs/{config_id} → deletes config
- GET /api/v1/library/patterns → lista patterns
- GET /api/v1/library/stats → estatísticas

**Tasks Decompostas:**

1. **Implement Config Storage** [M]
   - Por enquanto: em-memory dict ou JSON file
   - File: `data/configs/configs.json`
   - Métodos CRUD simples

2. **Implement genie/api/v1/endpoints/config.py** [M]
   - POST /api/v1/configs
     - Request: ExtractionConfig
     - Response: ExtractionConfig + id
   - GET /api/v1/configs/{config_id}
     - Response: ExtractionConfig
   - PUT /api/v1/configs/{config_id}
     - Request: ExtractionConfig (partial update allowed)
     - Response: updated config
   - DELETE /api/v1/configs/{config_id}
     - Response: {"status": "deleted"}

3. **Implement genie/api/v1/endpoints/library.py** [M]
   - GET /api/v1/library/patterns
     - Query params: config_id (optional), layout_id (optional)
     - Response: List[SearchPattern]
   - GET /api/v1/library/patterns/{layout_id}
     - Response: SearchPattern detail
   - GET /api/v1/library/stats
     - Response: {total_patterns, avg_success_rate, last_updated, usage_per_layout}

4. **Implement genie/api/v1/router.py** [M]
   - Include all routers (health, extract, config, library)

5. **Write integration tests** [M]
   - `tests/integration/test_api.py`:
     - Config CRUD tests
     - Library endpoint tests
     - Error handling (404, 400, etc.)

**Componentes a Criar:**
- `genie/api/v1/endpoints/config.py`
- `genie/api/v1/endpoints/library.py`
- Config storage mechanism

**Testes:**
- Update `tests/integration/test_api.py`

**Quality Gate 1.4.3:**
```bash
✓ POST /api/v1/configs creates config
✓ GET /api/v1/configs/{id} retrieves it
✓ PUT updates the config
✓ DELETE removes the config
✓ GET /api/v1/library/patterns lists patterns
✓ GET /api/v1/library/stats works
✓ All error cases handled (404, 400, etc.)
```

---

### 1.4.4 End-to-End Validation
**Objetivo:** Full flow: config → extract → pattern save → re-extract

**Critério de Sucesso:**
- E2E test passes
- Manual validation with real PDF works
- Search Library populated correctly
- Coverage >= 80%

**Tasks Decompostas:**

1. **Write end-to-end test** [L]
   - `tests/integration/test_end_to_end.py`:
     ```python
     async def test_extraction_flow_with_library():
         # 1. Create config
         config = await client.post("/api/v1/configs", json={...})
         config_id = config["extraction_id"]

         # 2. Extract from text (LLM, no library yet)
         result1 = await client.post("/api/v1/extract", json={
             "config_id": config_id,
             "source": {"type": "text", "content": "..."}
         })
         assert result1["method_used"] == "llm"

         # 3. Verify pattern saved
         patterns = await client.get("/api/v1/library/patterns",
                                      params={"config_id": config_id})
         assert len(patterns) == 1

         # 4. Re-extract same layout (should use library)
         result2 = await client.post("/api/v1/extract", json={
             "config_id": config_id,
             "source": {"type": "text", "content": "... (similar data)"}
         })
         assert result2["method_used"] == "search_library"
     ```

2. **Manual validation script** [S]
   - `scripts/validate_e2e.py`:
     - Lê PDF real ou cria simples
     - Faz extraction
     - Verifica output
     - Verifica library populated
     - Documenta resultado

3. **Run full test suite** [M]
   - `pytest tests/ --cov=genie --cov-report=html`
   - Verificar coverage >= 80%
   - Fix missing coverage

4. **Verify performance targets** [S]
   - Execution time de extractions
   - Library hit latency (< 100ms target)
   - LLM latency (< 3s target)

**Componentes a Criar:**
- E2E test

**Testes:**
- `tests/integration/test_end_to_end.py`
- Coverage report

**Quality Gate 1.4.4 (FINAL GATE PARA PHASE 1):**
```bash
✓ E2E test passes
✓ Complete extraction flow works (config → extract → library → re-extract)
✓ Pattern saved and reused correctly
✓ Test coverage >= 80%
✓ All unit tests pass
✓ All integration tests pass
✓ No type errors (mypy clean)
✓ Code formatted (ruff format, black)
✓ Manual PDF extraction works
✓ Performance targets met
```

---

## ARQUITETURA DE COMPONENTES (Diagrama de Dependências)

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI App                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  POST /api/v1/extract                           │   │
│  │  GET  /api/v1/configs/{config_id}              │   │
│  │  POST /api/v1/configs                          │   │
│  │  GET  /api/v1/library/patterns                 │   │
│  └────────────┬──────────────────────────────────┬┘   │
│               │                                   │    │
│         ┌─────▼─────┐                    ┌──────▼──┐  │
│         │ Extract   │                    │ Config  │  │
│         │ Endpoint  │                    │ Manager │  │
│         └─────┬─────┘                    └────────┘   │
│               │                                       │
│         ┌─────▼──────────────────────────────────┐   │
│         │                                         │   │
│         │  ExtractionEngine (Orchestrator)       │   │
│         │  ┌─────────────────────────────────┐  │   │
│         │  │ 1. Read Content (Parser)        │  │   │
│         │  │ 2. Generate Fingerprint         │  │   │
│         │  │ 3. Search Library Lookup        │  │   │
│         │  │ 4. LLM Extraction (Fallback)    │  │   │
│         │  │ 5. Save Pattern (Auto)          │  │   │
│         │  │ 6. Adapt Output                 │  │   │
│         │  └────────┬──────────┬───────────┬┘  │   │
│         │           │          │           │   │   │
│    ┌────▼────┐ ┌───▼──┐ ┌────▼────┐ ┌──▼─┐  │   │
│    │ Parsers │ │ LLM  │ │ Search  │ │Out-│  │   │
│    │         │ │Factory│ │ Library │ │put │  │   │
│    │ • Text  │ │      │ │         │ │Mgr │  │   │
│    │ • PDF   │ │ Anth-│ │JSONStor-│ │    │  │   │
│    │ • Image │ │ropic │ │ age     │ │    │  │   │
│    │ (Phase) │ │OpenAI│ │Matcher  │ │    │  │   │
│    │         │ │(P2)  │ │PatGen(2)│ │    │  │   │
│    └────────┘ │      │ │         │ │    │  │   │
│               └──────┘ └────────┘ └───┘  │   │
│                                          │   │
│  ┌──────────────────────────────────────▼┐  │
│  │          Core Infrastructure          │  │
│  │ • Config (Pydantic Settings)          │  │
│  │ • Logging                             │  │
│  │ • Exception Hierarchy                 │  │
│  │ • Security (Keys)                     │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │        Models (Pydantic v2)          │  │
│  │ • ExtractionRequest/Response         │  │
│  │ • ExtractionConfig                   │  │
│  │ • SearchPattern                      │  │
│  │ • OutputSchema                       │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │                    │
         ▼                    ▼
    ┌────────────┐       ┌──────────────┐
    │ Anthropic  │       │ JSONStorage  │
    │   API      │       │ (patterns)   │
    │ (LLM)      │       │              │
    └────────────┘       └──────────────┘
```

---

## CHECKLIST DE CONCLUSÃO PHASE 1

### Stage 1.1 Project Setup
- [ ] Git repository initialized with .gitignore
- [ ] pyproject.toml created with all dependencies
- [ ] .env.example with all required variables
- [ ] Folder structure complete with __init__.py everywhere
- [ ] FastAPI app starts without errors
- [ ] Health endpoint returns 200
- [ ] Logging works to file and stdout

### Stage 1.2 Base Models
- [ ] All Pydantic models defined (extraction, config, library, output)
- [ ] Type hints on 100% of fields
- [ ] Docstrings on all models
- [ ] Unit tests for model validation pass
- [ ] JSON schema exports correctly

### Stage 1.2 LLM Extraction
- [ ] BaseLLMProvider interface defined
- [ ] AnthropicProvider implements interface
- [ ] Prompt building optimized for Claude
- [ ] JSON parsing handles markdown cleanup
- [ ] LLMProviderFactory creates instances
- [ ] Unit tests (all mocked, no API calls)
- [ ] test_llm_connection.py script works

### Stage 1.2 Basic Extraction
- [ ] TextParser extracts text from content
- [ ] ExtractionEngine skeleton complete
- [ ] POST /api/v1/extract endpoint works
- [ ] Integration tests pass
- [ ] LLM is called correctly
- [ ] Response contains extracted data

### Stage 1.3 PDF Support
- [ ] PDFParser extracts text from PDFs
- [ ] Scanned PDF detection implemented
- [ ] Sample PDFs in fixtures
- [ ] API accepts "file" source type
- [ ] Unit tests for PDF parsing

### Stage 1.3 Fingerprinting
- [ ] LayoutFingerprint generates deterministic hashes
- [ ] Similarity scoring works (0-1 float)
- [ ] Different layouts produce different hashes
- [ ] Unit tests comprehensive
- [ ] ExtractionEngine uses fingerprints

### Stage 1.4 Search Library
- [ ] BaseStorage ABC defined
- [ ] JSONStorage CRUD works
- [ ] PatternMatcher extracts with regex
- [ ] Validation works
- [ ] Thread-safe operations
- [ ] Unit tests complete

### Stage 1.4 Engine Full Flow
- [ ] Library hit path works (pattern found)
- [ ] Library miss path works (LLM fallback)
- [ ] Pattern auto-save works
- [ ] force_llm bypasses library
- [ ] Confidence scores calculated
- [ ] Unit tests for all flows

### Stage 1.4 API Completion
- [ ] Config CRUD endpoints work
- [ ] Library endpoints work
- [ ] All routers integrated
- [ ] Integration tests pass
- [ ] Error handling (404, 400, etc.)

### Stage 1.4 End-to-End
- [ ] E2E test passes (config → extract → library → re-extract)
- [ ] Manual PDF extraction works
- [ ] Test coverage >= 80%
- [ ] All tests pass
- [ ] No type errors
- [ ] Code formatted (ruff, black)

---

## RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Chamadas reais à API Anthropic durante teste | Média | Alto | Usar mocks com `patch()`, apenas script manual opcional |
| PDF parsing falha em PDFs complexos | Baixa | Médio | Testar com múltiplos PDFs reais, graceful degradation |
| Fingerprint não é determinístico | Baixa | Alto | Testes extensivos, fixtures específicas |
| Race conditions em JSON storage | Baixa | Alto | Use locks, async-safe patterns, test with concurrent ops |
| Performance inadequada | Médio | Médio | Profile early, optimize patterns, add caching |
| TypeErrors in production | Médio | Médio | Enforce type hints, mypy strict mode, test typing |
| LLM JSON parsing fails | Médio | Médio | Robust JSON cleanup, fallback to structured prompt |

---

## PRÓXIMOS PASSOS APÓS PHASE 1

1. **Phase 2 — Search Library Enhancement**
   - Auto pattern generation (REGEX, Query)
   - Advanced fingerprinting
   - SQLite migration
   - Manual correction API

2. **Phase 3 — Multiple Formats**
   - Image & OCR support
   - Spreadsheet parsers
   - Database support
   - Auto schema adaptation

3. **Phase 4 — Interoperability**
   - JavaScript SDK
   - Python SDK
   - TABEX integration
   - Load testing

4. **Phase 5 — Production**
   - Auth & Rate limiting
   - Monitoring & Metrics
   - Docker deployment
   - Documentation

---

## CRÍTICAS ARQUITETURAIS

A Phase 1 foi projetada para ser **minimalmente viável mas robusta**:

✅ **Fortes:**
- Arquitetura extensível (Abstract Base Classes)
- Dependency Injection desde o início
- Type hints em 100%
- Comprehensive testing from start
- Clear separation of concerns
- Logging built-in

⚠️ **Trade-offs:**
- JSON storage é simples (SQLite vem em Phase 2)
- Sem autenticação (Phase 5)
- Pattern generation é placeholder (Phase 2)
- Sem OCR (Phase 3)

---

## Critical Files for Implementation

Baseado na análise completa, estes são os arquivos mais críticos:

- `/home/rodrigo/GenIE/spec/extraction/engine.py` - Orquestrador principal, coração do sistema
- `/home/rodrigo/GenIE/spec/extraction/llm/anthropic.py` - Integração com Claude, fluxo LLM
- `/home/rodrigo/GenIE/spec/search_library/json_storage.py` - Persistência de patterns, principal vantagem de custo
- `/home/rodrigo/GenIE/spec/extraction/layout/fingerprint.py` - Identificação de layout, crucial para reconhecer patterns
- `/home/rodrigo/GenIE/spec/main.py` - FastAPI app, entry point e configuração central

---

**Este plano está pronto para execução imediata. Cada task tem estimativa de esforço, critério de sucesso claro, e componentes bem definidos. Recomenda-se seguir ordem sequencial, respeitando dependências entre stages.**
