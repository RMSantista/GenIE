# GENIE - Arquitetura de Código
## Estrutura de Projeto e Componentes

---

## 1. ESTRUTURA DE PASTAS

```
genie/
├── README.md
├── LICENSE
├── pyproject.toml
├── poetry.lock
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── .calude/
│   ├── CLAUDE.md
│   ├── ORCHESTRATOR.md
├── spec/                          # Package principal
│   ├── __init__.py
│   ├── main.py                     # FastAPI app entry point
│   │
│   ├── api/                        # API REST
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── extraction.py  # POST /extract
│   │   │   │   ├── config.py      # CRUD configs
│   │   │   │   ├── health.py      # Health checks
│   │   │   │   └── library.py     # Search library management
│   │   │   └── dependencies.py    # FastAPI dependencies
│   │   └── middleware/
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       └── rate_limit.py
│   │
│   ├── core/                       # Componentes core
│   │   ├── __init__.py
│   │   ├── config.py              # Settings (Pydantic)
│   │   ├── security.py            # Encryption, API keys
│   │   ├── exceptions.py          # Custom exceptions
│   │   └── logging_config.py      # Logging setup
│   │
│   ├── models/                     # Data models
│   │   ├── __init__.py
│   │   ├── extraction.py          # ExtractionRequest, Response
│   │   ├── config.py              # ConfigModel
│   │   ├── pattern.py             # PatternModel
│   │   └── layout.py              # LayoutFingerprint
│   │
│   ├── extraction/                 # Engine de extração
│   │   ├── __init__.py
│   │   ├── engine.py              # ExtractionEngine (orquestrador)
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # BaseLLMProvider (interface)
│   │   │   ├── anthropic.py       # AnthropicProvider
│   │   │   ├── openai.py          # OpenAIProvider
│   │   │   └── factory.py         # LLMProviderFactory
│   │   ├── ocr/
│   │   │   ├── __init__.py
│   │   │   ├── tesseract.py       # Tesseract OCR
│   │   │   └── preprocessor.py    # Image preprocessing
│   │   ├── parsers/
│   │   │   ├── __init__.py
│   │   │   ├── pdf_parser.py
│   │   │   ├── image_parser.py
│   │   │   ├── xlsx_parser.py
│   │   │   ├── json_parser.py
│   │   │   └── db_parser.py
│   │   └── layout/
│   │       ├── __init__.py
│   │       ├── fingerprint.py     # Layout fingerprinting
│   │       └── detector.py        # Layout detection
│   │
│   ├── search_library/             # Biblioteca de busca
│   │   ├── __init__.py
│   │   ├── base.py                # BaseStorage (interface)
│   │   ├── json_storage.py        # JSON implementation
│   │   ├── sqlite_storage.py      # SQLite implementation
│   │   ├── pattern_generator.py   # Auto-criação de padrões
│   │   └── matcher.py             # Pattern matching
│   │
│   ├── output/                     # Output management
│   │   ├── __init__.py
│   │   ├── manager.py             # OutputManager
│   │   ├── formatters/
│   │   │   ├── __init__.py
│   │   │   ├── json_formatter.py
│   │   │   ├── csv_formatter.py
│   │   │   ├── xlsx_formatter.py
│   │   │   └── db_formatter.py
│   │   └── schema_adapter.py      # Schema auto-adaptation
│   │
│   ├── mcp/                        # MCP Integration
│   │   ├── __init__.py
│   │   ├── file_reader.py         # MCP file reading
│   │   └── db_connector.py        # MCP DB connections
│   │
│   └── utils/                      # Utilidades
│       ├── __init__.py
│       ├── validators.py
│       ├── converters.py
│       └── helpers.py
│
├── sdks/                           # SDKs para clientes
│   ├── javascript/
│   │   ├── package.json
│   │   ├── src/
│   │   │   └── genie-client.js
│   │   └── README.md
│   └── python/
│       ├── pyproject.toml
│       ├── genie_sdk/
│       │   └── client.py
│       └── README.md
│
├── tests/                          # Testes
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_extraction_engine.py
│   │   ├── test_llm_providers.py
│   │   ├── test_search_library.py
│   │   └── test_parsers.py
│   ├── integration/
│   │   ├── test_api.py
│   │   ├── test_end_to_end.py
│   │   └── test_mcp.py
│   └── fixtures/
│       ├── sample_pdfs/
│       ├── sample_images/
│       └── sample_configs.json
│
├── config/                         # Configurações
│   ├── development.yaml
│   ├── production.yaml
│   └── docker.yaml
│
├── data/                           # Dados persistentes
│   ├── search_library/
│   │   ├── patterns.json
│   │   └── patterns.db
│   └── uploads/
│       └── .gitkeep
│
├── docs/                           # Documentação
│   ├── api/
│   │   └── openapi.yaml
│   ├── guides/
│   │   ├── quickstart.md
│   │   ├── configuration.md
│   │   └── deployment.md
│   └── examples/
│       ├── tabex_integration.md
│       └── custom_parser.md
│
└── scripts/                        # Scripts utilitários
    ├── setup.sh
    ├── migrate_library.py
    └── test_llm_connection.py
```

---

## 2. COMPONENTES PRINCIPAIS

### 2.1 ExtractionEngine (Orquestrador)

```python
# genie/extraction/engine.py
from typing import Dict, Any, Optional
from genie.models.extraction import ExtractionRequest, ExtractionResponse
from genie.extraction.layout.fingerprint import LayoutFingerprint
from genie.search_library.base import BaseStorage
from genie.extraction.llm.factory import LLMProviderFactory
from genie.output.manager import OutputManager

class ExtractionEngine:
    """
    Orquestrador principal do processo de extração.
    
    Fluxo:
    1. Recebe requisição
    2. Identifica layout
    3. Tenta usar Search Library
    4. Fallback para LLM se necessário
    5. Adapta e retorna saída
    """
    
    def __init__(
        self,
        search_library: BaseStorage,
        llm_factory: LLMProviderFactory,
        output_manager: OutputManager
    ):
        self.search_library = search_library
        self.llm_factory = llm_factory
        self.output_manager = output_manager
        self.fingerprint_generator = LayoutFingerprint()
    
    async def extract(
        self,
        request: ExtractionRequest
    ) -> ExtractionResponse:
        """
        Executa extração completa.
        """
        # 1. Lê conteúdo (via MCP ou parser direto)
        content = await self._read_content(request.source)
        
        # 2. Gera fingerprint do layout
        layout_fp = self.fingerprint_generator.generate(content)
        
        # 3. Busca pattern na library
        pattern = self.search_library.find_pattern(
            layout_fp,
            request.config_id
        )
        
        # 4. Extração
        if pattern and not request.force_llm:
            # Usa pattern existente
            extracted_data = self._extract_with_pattern(
                content,
                pattern
            )
            method = "search_library"
        else:
            # Usa LLM
            llm_provider = self.llm_factory.get_provider(
                request.llm_config
            )
            extracted_data = await llm_provider.extract(
                content,
                request.output_schema
            )
            method = "llm"
            
            # Auto-cria pattern para próximas vezes
            if request.auto_create_patterns:
                new_pattern = self._generate_pattern(
                    content,
                    extracted_data,
                    layout_fp
                )
                self.search_library.save_pattern(
                    layout_fp,
                    request.config_id,
                    new_pattern
                )
        
        # 5. Adapta output
        output = self.output_manager.adapt_and_format(
            extracted_data,
            request.output_config
        )
        
        # 6. Retorna
        return ExtractionResponse(
            extraction_id=self._generate_id(),
            status="success",
            method_used=method,
            data=output,
            confidence=self._calculate_confidence(extracted_data),
            layout_fingerprint=layout_fp
        )
    
    async def _read_content(self, source: Dict[str, Any]) -> str:
        """Lê conteúdo do source via parser apropriado."""
        pass
    
    def _extract_with_pattern(
        self,
        content: str,
        pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Executa extração usando pattern REGEX/Query."""
        pass
    
    def _generate_pattern(
        self,
        content: str,
        extracted_data: Dict[str, Any],
        layout_fp: str
    ) -> Dict[str, Any]:
        """Gera pattern REGEX/Query baseado em extração bem-sucedida."""
        pass
    
    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """Calcula confiança da extração."""
        pass
```

### 2.2 BaseLLMProvider (Interface para LLMs)

```python
# genie/extraction/llm/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseLLMProvider(ABC):
    """
    Interface abstrata para providers de LLM.
    Permite adicionar novos providers facilmente.
    """
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
    
    @abstractmethod
    async def extract(
        self,
        content: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extrai dados do conteúdo baseado no schema.
        
        Args:
            content: Texto a ser analisado
            schema: Estrutura esperada de saída
        
        Returns:
            Dados extraídos no formato do schema
        """
        pass
    
    @abstractmethod
    def _build_prompt(
        self,
        content: str,
        schema: Dict[str, Any]
    ) -> str:
        """Constrói prompt para a LLM."""
        pass
    
    @abstractmethod
    def _parse_response(self, response: Any) -> Dict[str, Any]:
        """Parse da resposta da LLM para formato estruturado."""
        pass
```

### 2.3 AnthropicProvider (Implementação)

```python
# genie/extraction/llm/anthropic.py
from anthropic import AsyncAnthropic
from genie.extraction.llm.base import BaseLLMProvider
from typing import Dict, Any
import json

class AnthropicProvider(BaseLLMProvider):
    """
    Provider para Claude (Anthropic).
    """
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        super().__init__(api_key, model)
        self.client = AsyncAnthropic(api_key=api_key)
    
    async def extract(
        self,
        content: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extrai dados usando Claude.
        """
        prompt = self._build_prompt(content, schema)
        
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            system="Você é um extrator de informações especializado. "
                   "Retorne APENAS JSON válido, sem explicações."
        )
        
        return self._parse_response(response)
    
    def _build_prompt(
        self,
        content: str,
        schema: Dict[str, Any]
    ) -> str:
        """
        Constrói prompt otimizado para Claude.
        """
        schema_str = json.dumps(schema, indent=2, ensure_ascii=False)
        
        return f"""
Extraia as seguintes informações do documento abaixo.

SCHEMA ESPERADO:
{schema_str}

DOCUMENTO:
{content}

INSTRUÇÕES:
1. Retorne APENAS um objeto JSON válido
2. Use exatamente os nomes de campo do schema
3. Se um campo não for encontrado, use null
4. Mantenha os tipos de dados especificados no schema
5. NÃO adicione explicações ou texto extra

JSON:
"""
    
    def _parse_response(self, response) -> Dict[str, Any]:
        """
        Parse da resposta do Claude.
        """
        text = response.content[0].text.strip()
        
        # Remove markdown code blocks se presentes
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        return json.loads(text.strip())
```

### 2.4 SearchLibrary (JSON Implementation)

```python
# genie/search_library/json_storage.py
from genie.search_library.base import BaseStorage
from typing import Dict, Any, Optional, List
import json
import hashlib
from pathlib import Path
from datetime import datetime

class JSONStorage(BaseStorage):
    """
    Implementação da Search Library usando JSON.
    Leve, portável, ideal para MVP.
    """
    
    def __init__(self, storage_path: str = "data/search_library/patterns.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_storage_exists()
        self._cache = self._load_storage()
    
    def _ensure_storage_exists(self):
        """Cria arquivo se não existir."""
        if not self.storage_path.exists():
            self._save_storage({
                "patterns": [],
                "metadata": {
                    "version": "1.0",
                    "created_at": datetime.utcnow().isoformat(),
                    "total_patterns": 0
                }
            })
    
    def _load_storage(self) -> Dict[str, Any]:
        """Carrega storage do disco."""
        with open(self.storage_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_storage(self, data: Dict[str, Any]):
        """Salva storage no disco."""
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def find_pattern(
        self,
        layout_fingerprint: str,
        config_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Busca pattern por fingerprint e config.
        """
        for pattern in self._cache["patterns"]:
            if (pattern["fingerprint"] == layout_fingerprint and
                pattern.get("config_id") == config_id):
                
                # Atualiza last_used
                pattern["last_used"] = datetime.utcnow().isoformat()
                pattern["use_count"] = pattern.get("use_count", 0) + 1
                self._save_storage(self._cache)
                
                return pattern
        
        return None
    
    def save_pattern(
        self,
        layout_fingerprint: str,
        config_id: str,
        pattern: Dict[str, Any]
    ):
        """
        Salva novo pattern.
        """
        new_pattern = {
            "layout_id": self._generate_layout_id(),
            "config_id": config_id,
            "fingerprint": layout_fingerprint,
            "created_at": datetime.utcnow().isoformat(),
            "last_used": datetime.utcnow().isoformat(),
            "use_count": 1,
            "success_rate": 1.0,
            "fields": pattern.get("fields", [])
        }
        
        self._cache["patterns"].append(new_pattern)
        self._cache["metadata"]["total_patterns"] = len(self._cache["patterns"])
        self._cache["metadata"]["last_updated"] = datetime.utcnow().isoformat()
        
        self._save_storage(self._cache)
    
    def update_success_rate(
        self,
        layout_fingerprint: str,
        success: bool
    ):
        """
        Atualiza taxa de sucesso de um pattern.
        """
        for pattern in self._cache["patterns"]:
            if pattern["fingerprint"] == layout_fingerprint:
                current_rate = pattern.get("success_rate", 1.0)
                use_count = pattern.get("use_count", 1)
                
                # Média móvel
                new_rate = (
                    (current_rate * (use_count - 1) + (1.0 if success else 0.0))
                    / use_count
                )
                
                pattern["success_rate"] = new_rate
                self._save_storage(self._cache)
                break
    
    def _generate_layout_id(self) -> str:
        """Gera ID único para layout."""
        timestamp = datetime.utcnow().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:12]
```

### 2.5 LayoutFingerprint (Identificação de Layout)

```python
# genie/extraction/layout/fingerprint.py
import hashlib
import re
from typing import Dict, Any

class LayoutFingerprint:
    """
    Gera fingerprint único de um documento baseado em sua estrutura.
    Permite identificar layouts similares mesmo com dados diferentes.
    """
    
    def generate(self, content: str) -> str:
        """
        Gera fingerprint do layout.
        
        Estratégia:
        1. Remove dados variáveis (números, datas, nomes próprios)
        2. Mantém estrutura (labels, formatação, ordem)
        3. Hash da estrutura resultante
        """
        structure = self._extract_structure(content)
        return hashlib.sha256(structure.encode()).hexdigest()[:16]
    
    def _extract_structure(self, content: str) -> str:
        """
        Extrai estrutura do documento, removendo dados variáveis.
        """
        # Remove números (mas mantém labels como "Valor:")
        structure = re.sub(r'\d+', 'N', content)
        
        # Remove possíveis nomes próprios (palavras capitalizadas)
        # mas mantém labels (que geralmente terminam com :)
        lines = []
        for line in structure.split('\n'):
            if ':' in line:
                # Linha com label, mantém
                lines.append(line)
            else:
                # Remove palavras capitalizadas que não sejam labels
                line = re.sub(r'\b[A-Z][a-z]+\b', 'X', line)
                lines.append(line)
        
        structure = '\n'.join(lines)
        
        # Normaliza espaços
        structure = re.sub(r'\s+', ' ', structure)
        
        return structure.strip()
    
    def similarity(self, fp1: str, fp2: str) -> float:
        """
        Calcula similaridade entre dois fingerprints.
        Útil para encontrar layouts "quase iguais".
        """
        if fp1 == fp2:
            return 1.0
        
        # Hamming distance para fingerprints similares
        matches = sum(c1 == c2 for c1, c2 in zip(fp1, fp2))
        return matches / max(len(fp1), len(fp2))
```

### 2.6 OutputManager (Adaptação de Schema)

```python
# genie/output/manager.py
from typing import Dict, Any, List
from genie.output.formatters.json_formatter import JSONFormatter
from genie.output.formatters.csv_formatter import CSVFormatter
from genie.output.schema_adapter import SchemaAdapter

class OutputManager:
    """
    Gerencia adaptação e formatação de saída.
    """
    
    def __init__(self):
        self.schema_adapter = SchemaAdapter()
        self.formatters = {
            "json": JSONFormatter(),
            "csv": CSVFormatter(),
            # ... outros formatters
        }
    
    def adapt_and_format(
        self,
        data: Dict[str, Any],
        output_config: Dict[str, Any]
    ) -> Any:
        """
        Adapta dados ao schema e formata na saída desejada.
        """
        # 1. Verifica se saída existe
        if output_config.get("check_existing"):
            existing_schema = self._load_existing_schema(
                output_config["destination"]
            )
            
            if existing_schema:
                # Usa schema existente
                data = self.schema_adapter.adapt_to_existing(
                    data,
                    existing_schema
                )
            elif output_config.get("auto_adapt"):
                # Cria novo schema baseado nos dados
                new_schema = self.schema_adapter.create_from_data(data)
                self._save_schema(
                    output_config["destination"],
                    new_schema
                )
        
        # 2. Detecta novos campos (auto-adaptação)
        if output_config.get("auto_adapt"):
            data = self.schema_adapter.handle_new_fields(
                data,
                output_config["destination"]
            )
        
        # 3. Formata na saída desejada
        formatter = self.formatters[output_config["type"]]
        return formatter.format(data, output_config)
    
    def _load_existing_schema(self, destination: str) -> Optional[Dict]:
        """Carrega schema existente se houver."""
        pass
    
    def _save_schema(self, destination: str, schema: Dict):
        """Salva schema para uso futuro."""
        pass
```

### 2.7 SchemaAdapter (Adaptação Automática)

```python
# genie/output/schema_adapter.py
from typing import Dict, Any, List, Set
import json
from pathlib import Path

class SchemaAdapter:
    """
    Adapta schemas automaticamente quando novos campos aparecem.
    
    Exemplo:
    Schema existente: [nome, data, glicemia]
    Novos dados: [nome, data, glicemia, colesterol]
    Resultado: Adiciona coluna "colesterol" automaticamente
    """
    
    def adapt_to_existing(
        self,
        new_data: Dict[str, Any],
        existing_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adapta novos dados ao schema existente.
        """
        adapted = {}
        
        for field, field_type in existing_schema.items():
            if field in new_data:
                adapted[field] = new_data[field]
            else:
                # Campo não presente, usa valor padrão
                adapted[field] = self._get_default_value(field_type)
        
        return adapted
    
    def handle_new_fields(
        self,
        data: Dict[str, Any],
        destination: str
    ) -> Dict[str, Any]:
        """
        Detecta e adiciona novos campos ao schema.
        
        Exemplo prático:
        - Planilha tem: [Paciente, Data, Glicemia]
        - Novo exame tem: [Paciente, Data, Glicemia, Colesterol]
        - Adiciona coluna "Colesterol" automaticamente
        """
        existing_schema = self._load_schema(destination)
        
        if not existing_schema:
            return data
        
        new_fields = set(data.keys()) - set(existing_schema.keys())
        
        if new_fields:
            # Novos campos detectados!
            for field in new_fields:
                field_type = self._infer_type(data[field])
                existing_schema[field] = field_type
            
            # Salva schema atualizado
            self._save_schema(destination, existing_schema)
            
            # Adiciona colunas na saída existente (se for arquivo)
            if destination.endswith(('.csv', '.xlsx')):
                self._add_columns_to_file(destination, list(new_fields))
        
        return data
    
    def create_from_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Cria schema baseado nos dados.
        """
        schema = {}
        for field, value in data.items():
            schema[field] = self._infer_type(value)
        return schema
    
    def _infer_type(self, value: Any) -> str:
        """Infere tipo do dado."""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            # Tenta detectar data
            if self._is_date(value):
                return "date"
            return "string"
        elif value is None:
            return "null"
        else:
            return "string"
    
    def _is_date(self, value: str) -> bool:
        """Detecta se string é uma data."""
        import re
        date_patterns = [
            r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        ]
        return any(re.match(pattern, value) for pattern in date_patterns)
    
    def _get_default_value(self, field_type: str) -> Any:
        """Retorna valor padrão para um tipo."""
        defaults = {
            "string": "",
            "integer": 0,
            "number": 0.0,
            "boolean": False,
            "date": None,
            "null": None
        }
        return defaults.get(field_type, None)
    
    def _load_schema(self, destination: str) -> Optional[Dict]:
        """Carrega schema de um arquivo .schema.json ao lado do destino."""
        schema_path = Path(destination).with_suffix('.schema.json')
        if schema_path.exists():
            with open(schema_path) as f:
                return json.load(f)
        return None
    
    def _save_schema(self, destination: str, schema: Dict):
        """Salva schema."""
        schema_path = Path(destination).with_suffix('.schema.json')
        with open(schema_path, 'w') as f:
            json.dump(schema, f, indent=2)
    
    def _add_columns_to_file(self, filepath: str, new_columns: List[str]):
        """Adiciona colunas a um arquivo CSV/XLSX existente."""
        if filepath.endswith('.csv'):
            self._add_columns_to_csv(filepath, new_columns)
        elif filepath.endswith('.xlsx'):
            self._add_columns_to_xlsx(filepath, new_columns)
    
    def _add_columns_to_csv(self, filepath: str, new_columns: List[str]):
        """Adiciona colunas a CSV."""
        import csv
        
        # Lê dados existentes
        with open(filepath, 'r', newline='') as f:
            reader = csv.DictReader(f)
            existing_rows = list(reader)
            existing_fieldnames = reader.fieldnames
        
        # Adiciona novos campos
        new_fieldnames = existing_fieldnames + new_columns
        
        # Reescreve com novos campos
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=new_fieldnames)
            writer.writeheader()
            
            for row in existing_rows:
                # Adiciona valores vazios para novos campos
                for col in new_columns:
                    row[col] = ""
                writer.writerow(row)
    
    def _add_columns_to_xlsx(self, filepath: str, new_columns: List[str]):
        """Adiciona colunas a XLSX."""
        from openpyxl import load_workbook
        
        wb = load_workbook(filepath)
        ws = wb.active
        
        # Encontra próxima coluna vazia
        max_col = ws.max_column
        
        # Adiciona headers para novas colunas
        for i, col_name in enumerate(new_columns, start=1):
            ws.cell(row=1, column=max_col + i, value=col_name)
        
        wb.save(filepath)
```

---

## 3. FLUXO DE DADOS DETALHADO

### 3.1 Requisição de Extração

```
Cliente (TABEX)
    │
    │ POST /api/v1/extract
    │ {
    │   "config_id": "medical_reports_v1",
    │   "source": {"type": "file", "path": "/upload/report.pdf"}
    │ }
    ▼
FastAPI Router (extraction.py)
    │
    │ Valida request
    │ Carrega config do banco
    ▼
ExtractionEngine.extract()
    │
    ├─► 1. Read Content
    │   └─► MCP File Reader → content (string)
    │
    ├─► 2. Generate Fingerprint
    │   └─► LayoutFingerprint.generate() → fingerprint (hash)
    │
    ├─► 3. Search Pattern
    │   └─► SearchLibrary.find_pattern() → pattern or None
    │
    ├─► 4. Extract Data
    │   ├─► If pattern exists:
    │   │   └─► Matcher.extract_with_regex() → data
    │   │
    │   └─► If no pattern (or force_llm):
    │       ├─► LLMProvider.extract() → data
    │       └─► PatternGenerator.create() → new_pattern
    │           └─► SearchLibrary.save_pattern()
    │
    ├─► 5. Adapt Output
    │   └─► OutputManager.adapt_and_format()
    │       ├─► SchemaAdapter.handle_new_fields()
    │       └─► Formatter.format() → formatted_output
    │
    └─► 6. Return Response
        └─► ExtractionResponse
            │
            ▼
Cliente recebe JSON
```

---

## 4. PADRÕES DE CÓDIGO

### 4.1 Dependency Injection

```python
# genie/api/v1/dependencies.py
from fastapi import Depends
from genie.extraction.engine import ExtractionEngine
from genie.search_library.json_storage import JSONStorage
from genie.extraction.llm.factory import LLMProviderFactory
from genie.output.manager import OutputManager

def get_search_library() -> JSONStorage:
    """Singleton da Search Library."""
    return JSONStorage()

def get_llm_factory() -> LLMProviderFactory:
    """Factory de LLM providers."""
    return LLMProviderFactory()

def get_output_manager() -> OutputManager:
    """Manager de output."""
    return OutputManager()

def get_extraction_engine(
    library: JSONStorage = Depends(get_search_library),
    llm_factory: LLMProviderFactory = Depends(get_llm_factory),
    output_manager: OutputManager = Depends(get_output_manager)
) -> ExtractionEngine:
    """Engine de extração com todas as dependências."""
    return ExtractionEngine(library, llm_factory, output_manager)
```

### 4.2 Error Handling

```python
# genie/core/exceptions.py
class GenieException(Exception):
    """Base exception para GENIE."""
    pass

class LayoutNotRecognized(GenieException):
    """Layout não reconhecido na biblioteca."""
    pass

class ExtractionFailed(GenieException):
    """Falha na extração."""
    pass

class LLMProviderError(GenieException):
    """Erro no provider de LLM."""
    pass

class InvalidConfig(GenieException):
    """Configuração inválida."""
    pass

# Usage
try:
    result = await engine.extract(request)
except LayoutNotRecognized:
    # Fallback to LLM automatically
    result = await engine.extract_with_llm(request)
except ExtractionFailed as e:
    logger.error(f"Extraction failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

### 4.3 Logging

```python
# genie/core/logging_config.py
import logging
import sys
from pathlib import Path

def setup_logging(log_level: str = "INFO"):
    """Configura logging do GENIE."""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler(
        log_dir / "genie.log",
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return root_logger

# Usage em qualquer módulo
import logging
logger = logging.getLogger(__name__)

logger.info("Starting extraction")
logger.debug(f"Fingerprint: {fingerprint}")
logger.error("Extraction failed", exc_info=True)
```

---

## 5. CONFIGURAÇÃO E SETUP

### 5.1 pyproject.toml

```toml
[tool.poetry]
name = "genie"
version = "0.1.0"
description = "Generic Extractor of Information Engine"
authors = ["Your Name <you@example.com>"]
readme = "README.md"
license = "MIT"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.110.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
pydantic = "^2.6.0"
pydantic-settings = "^2.2.0"
anthropic = "^0.18.0"
openai = "^1.12.0"
python-multipart = "^0.0.9"
pytesseract = "^0.3.10"
PyPDF2 = "^3.0.0"
openpyxl = "^3.1.0"
sqlalchemy = "^2.0.0"
cryptography = "^42.0.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
pillow = "^10.2.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.23.0"
pytest-cov = "^4.1.0"
black = "^24.2.0"
ruff = "^0.2.0"
mypy = "^1.8.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
```

### 5.2 docker-compose.yml

```yaml
version: '3.8'

services:
  genie-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    depends_on:
      - postgres
      - redis
    command: uvicorn genie.main:app --host 0.0.0.0 --port 8000 --reload

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: genie
      POSTGRES_PASSWORD: genie_password
      POSTGRES_DB: genie_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## 6. PRÓXIMOS PASSOS

1. **Setup inicial do projeto**
   ```bash
   poetry new genie
   cd genie
   poetry install
   ```

2. **Criar estrutura de pastas**
   ```bash
   mkdir -p genie/{api,core,models,extraction,search_library,output,mcp,utils}
   touch genie/{api,core,models,extraction,search_library,output,mcp,utils}/__init__.py
   ```

3. **Implementar componentes core**
   - [ ] ExtractionEngine básico
   - [ ] AnthropicProvider
   - [ ] JSONStorage
   - [ ] LayoutFingerprint

4. **Criar primeira rota da API**
   - [ ] POST /api/v1/extract

5. **Testes iniciais**
   - [ ] Teste com PDF simples
   - [ ] Validação de fingerprint
   - [ ] Criação de pattern

**Este documento será atualizado conforme desenvolvimento.**
