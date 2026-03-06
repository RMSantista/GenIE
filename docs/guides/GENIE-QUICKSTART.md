# GENIE - Guia de Início Rápido
## Setup e Primeiros Passos

---

## 1. SETUP INICIAL (15 minutos)

### 1.1 Pré-requisitos

```bash
# Verificar versões
python --version  # Deve ser 3.11+
node --version    # 18+ (para SDK JavaScript)
docker --version  # Opcional, mas recomendado

# Instalar Poetry (gerenciador de dependências Python)
curl -sSL https://install.python-poetry.org | python3 -
```

### 1.2 Criar Projeto

```bash
# 1. Criar estrutura do projeto
mkdir genie && cd genie
poetry init --name genie --python "^3.11"

# 2. Adicionar dependências principais
poetry add fastapi uvicorn pydantic anthropic
poetry add --group dev pytest pytest-asyncio black ruff

# 3. Criar estrutura de pastas básica
mkdir -p genie/{api,core,models,extraction,search_library,output}
touch genie/__init__.py
touch genie/main.py
```

### 1.3 Arquivo de Configuração

```bash
# .env.example
cat > .env.example << 'EOF'
# GENIE Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO

# API Keys (nunca commitar .env real!)
ANTHROPIC_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here

# Paths
DATA_DIR=./data
SEARCH_LIBRARY_PATH=./data/search_library/patterns.json

# API
API_HOST=0.0.0.0
API_PORT=8000
EOF

# Copiar para .env real
cp .env.example .env
# Editar .env e adicionar suas API keys
```

---

## 2. IMPLEMENTAÇÃO MVP (Dia 1)

### 2.1 Criar Modelo Base

```python
# genie/models/extraction.py
from pydantic import BaseModel
from typing import Dict, Any, Optional

class ExtractionRequest(BaseModel):
    """Request para extração de dados."""
    config_id: str
    source: Dict[str, Any]
    force_llm: bool = False

class ExtractionResponse(BaseModel):
    """Response da extração."""
    extraction_id: str
    status: str
    method_used: str  # "llm" ou "search_library"
    data: Dict[str, Any]
    confidence: float
    processing_time_ms: int
```

### 2.2 Criar Provider LLM Básico

```python
# genie/extraction/llm/anthropic.py
from anthropic import AsyncAnthropic
import json
import os

class AnthropicProvider:
    """Provider para Claude."""
    
    def __init__(self):
        self.client = AsyncAnthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = "claude-sonnet-4-20250514"
    
    async def extract(self, content: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai dados usando Claude."""
        
        prompt = f"""
Extraia as seguintes informações do documento abaixo.

SCHEMA ESPERADO:
{json.dumps(schema, indent=2, ensure_ascii=False)}

DOCUMENTO:
{content}

Retorne APENAS um objeto JSON válido com os dados extraídos.
Não adicione explicações ou texto extra.
"""
        
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            system="Você é um extrator de dados. Retorne apenas JSON válido."
        )
        
        # Parse response
        text = response.content[0].text.strip()
        
        # Remove markdown se presente
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        return json.loads(text.strip())
```

### 2.3 Criar API Básica

```python
# genie/main.py
from fastapi import FastAPI, HTTPException
from genie.models.extraction import ExtractionRequest, ExtractionResponse
from genie.extraction.llm.anthropic import AnthropicProvider
import time
import uuid

app = FastAPI(title="GENIE API", version="0.1.0")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "genie"}

@app.post("/api/v1/extract", response_model=ExtractionResponse)
async def extract_data(request: ExtractionRequest):
    """
    Extrai dados de um documento.
    
    Exemplo:
    ```json
    {
      "config_id": "test",
      "source": {
        "type": "text",
        "content": "Nome: João Silva\\nIdade: 35 anos"
      }
    }
    ```
    """
    start_time = time.time()
    
    try:
        # Por enquanto, schema hardcoded para teste
        schema = {
            "nome": "string",
            "idade": "integer"
        }
        
        # Extrai conteúdo
        if request.source["type"] == "text":
            content = request.source["content"]
        else:
            raise HTTPException(400, "Tipo não suportado ainda")
        
        # Usa LLM para extrair
        llm = AnthropicProvider()
        data = await llm.extract(content, schema)
        
        # Calcula tempo
        processing_time = int((time.time() - start_time) * 1000)
        
        return ExtractionResponse(
            extraction_id=str(uuid.uuid4()),
            status="success",
            method_used="llm",
            data=data,
            confidence=0.95,
            processing_time_ms=processing_time
        )
    
    except Exception as e:
        raise HTTPException(500, str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2.4 Testar MVP

```bash
# Terminal 1: Rodar servidor
poetry run python -m genie.main

# Terminal 2: Testar endpoint
curl -X POST http://localhost:8000/api/v1/extract \
  -H "Content-Type: application/json" \
  -d '{
    "config_id": "test",
    "source": {
      "type": "text",
      "content": "Nome: João Silva\nIdade: 35 anos\nCPF: 123.456.789-00"
    }
  }'

# Resposta esperada:
# {
#   "extraction_id": "...",
#   "status": "success",
#   "method_used": "llm",
#   "data": {
#     "nome": "João Silva",
#     "idade": 35
#   },
#   "confidence": 0.95,
#   "processing_time_ms": 1234
# }
```

---

## 3. ADICIONAR SEARCH LIBRARY (Dia 2)

### 3.1 Criar Estrutura JSON

```python
# genie/search_library/json_storage.py
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

class JSONStorage:
    """Storage simples em JSON para patterns."""
    
    def __init__(self, path: str = "data/search_library/patterns.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_exists()
    
    def _ensure_exists(self):
        """Cria arquivo se não existir."""
        if not self.path.exists():
            self._save({"patterns": [], "metadata": {}})
    
    def _load(self) -> Dict:
        """Carrega patterns do disco."""
        with open(self.path, 'r') as f:
            return json.load(f)
    
    def _save(self, data: Dict):
        """Salva patterns no disco."""
        with open(self.path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def find_pattern(self, fingerprint: str, config_id: str) -> Optional[Dict]:
        """Busca pattern por fingerprint."""
        data = self._load()
        for pattern in data["patterns"]:
            if (pattern["fingerprint"] == fingerprint and 
                pattern["config_id"] == config_id):
                return pattern
        return None
    
    def save_pattern(self, fingerprint: str, config_id: str, fields: list):
        """Salva novo pattern."""
        data = self._load()
        
        pattern = {
            "fingerprint": fingerprint,
            "config_id": config_id,
            "created_at": datetime.utcnow().isoformat(),
            "fields": fields
        }
        
        data["patterns"].append(pattern)
        self._save(data)
```

### 3.2 Criar Fingerprinting

```python
# genie/extraction/layout/fingerprint.py
import hashlib
import re

class LayoutFingerprint:
    """Gera fingerprint de layouts."""
    
    def generate(self, content: str) -> str:
        """
        Gera fingerprint removendo dados variáveis.
        
        Estratégia simples:
        - Substitui números por 'N'
        - Mantém estrutura (labels, formatação)
        """
        # Remove números
        structure = re.sub(r'\d+', 'N', content)
        
        # Normaliza espaços
        structure = re.sub(r'\s+', ' ', structure)
        
        # Hash da estrutura
        return hashlib.sha256(structure.encode()).hexdigest()[:16]
```

### 3.3 Integrar na API

```python
# genie/main.py (atualizar)
from genie.search_library.json_storage import JSONStorage
from genie.extraction.layout.fingerprint import LayoutFingerprint

# Adicionar no início
storage = JSONStorage()
fingerprinter = LayoutFingerprint()

@app.post("/api/v1/extract", response_model=ExtractionResponse)
async def extract_data(request: ExtractionRequest):
    start_time = time.time()
    
    try:
        # Esquema hardcoded
        schema = {"nome": "string", "idade": "integer"}
        
        # Extrai conteúdo
        content = request.source["content"]
        
        # Gera fingerprint
        fingerprint = fingerprinter.generate(content)
        
        # Tenta buscar pattern
        pattern = storage.find_pattern(fingerprint, request.config_id)
        
        if pattern and not request.force_llm:
            # Usa pattern (implementar depois)
            data = {"nome": "Pattern não implementado", "idade": 0}
            method = "search_library"
        else:
            # Usa LLM
            llm = AnthropicProvider()
            data = await llm.extract(content, schema)
            method = "llm"
            
            # Salva pattern para próximas vezes
            storage.save_pattern(fingerprint, request.config_id, [])
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return ExtractionResponse(
            extraction_id=str(uuid.uuid4()),
            status="success",
            method_used=method,
            data=data,
            confidence=0.95,
            processing_time_ms=processing_time
        )
    
    except Exception as e:
        raise HTTPException(500, str(e))
```

---

## 4. TESTAR COM DOCUMENTO REAL (Dia 3)

### 4.1 Adicionar Suporte a PDF

```bash
# Adicionar dependência
poetry add PyPDF2
```

```python
# genie/extraction/parsers/pdf_parser.py
import PyPDF2
from pathlib import Path

class PDFParser:
    """Parser para arquivos PDF."""
    
    def extract_text(self, filepath: str) -> str:
        """Extrai texto de um PDF."""
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
```

### 4.2 Atualizar API

```python
# genie/main.py (adicionar no início)
from genie.extraction.parsers.pdf_parser import PDFParser

pdf_parser = PDFParser()

# No endpoint extract_data:
if request.source["type"] == "text":
    content = request.source["content"]
elif request.source["type"] == "pdf":
    content = pdf_parser.extract_text(request.source["path"])
else:
    raise HTTPException(400, "Tipo não suportado")
```

### 4.3 Testar com PDF Real

```python
# test_real_pdf.py
import asyncio
import requests

async def test_pdf():
    # Criar PDF de teste
    # (ou usar um PDF real que você tenha)
    
    response = requests.post(
        "http://localhost:8000/api/v1/extract",
        json={
            "config_id": "medical_reports",
            "source": {
                "type": "pdf",
                "path": "/path/to/your/report.pdf"
            }
        }
    )
    
    print(response.json())

if __name__ == "__main__":
    asyncio.run(test_pdf())
```

---

## 5. PRÓXIMOS PASSOS

### Dia 4-5: Sistema de Configuração
- [ ] Criar endpoint POST /api/v1/configs
- [ ] Permitir criar configs via API
- [ ] Armazenar configs em arquivo JSON
- [ ] Schema dinâmico baseado na config

### Dia 6-7: Auto-criação de Patterns
- [ ] Implementar PatternGenerator
- [ ] Gerar REGEX automaticamente
- [ ] Validar patterns criados
- [ ] Adicionar correção manual

### Dia 8-9: Suporte a Múltiplos Formatos
- [ ] Imagens (OCR)
- [ ] XLSX
- [ ] JSON/XML
- [ ] Bancos de dados

### Dia 10-11: Adaptação Automática
- [ ] SchemaAdapter
- [ ] Detectar novos campos
- [ ] Adicionar colunas automaticamente
- [ ] OutputManager

### Dia 12-14: Integração com TABEX
- [ ] SDK JavaScript
- [ ] Endpoint específico para TABEX
- [ ] Migração de RegEx existente
- [ ] Testes de carga

---

## 6. COMANDOS ÚTEIS

### Desenvolvimento

```bash
# Rodar servidor com auto-reload
poetry run uvicorn genie.main:app --reload --host 0.0.0.0 --port 8000

# Rodar testes
poetry run pytest

# Formatar código
poetry run black genie/

# Verificar code quality
poetry run ruff check genie/

# Ver logs
tail -f logs/genie.log
```

### Docker (Opcional)

```bash
# Build
docker build -t genie:latest .

# Run
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e ANTHROPIC_API_KEY=your-key \
  genie:latest

# Docker Compose
docker-compose up -d
```

---

## 7. CHECKLIST DO MVP

### Funcionalidades Essenciais
- [x] API REST básica
- [x] Extração com LLM (Anthropic)
- [x] Suporte a texto e PDF
- [ ] Search Library (JSON)
- [ ] Fingerprinting de layouts
- [ ] Auto-criação de patterns

### Qualidade
- [ ] Testes unitários básicos
- [ ] Tratamento de erros
- [ ] Logging
- [ ] Documentação da API (OpenAPI)

### DevOps
- [ ] Docker
- [ ] Docker Compose
- [ ] CI/CD básico (GitHub Actions)
- [ ] Monitoramento básico

---

## 8. RECURSOS E AJUDA

### Documentação
- **FastAPI**: https://fastapi.tiangolo.com/
- **Anthropic API**: https://docs.anthropic.com/
- **Pydantic**: https://docs.pydantic.dev/

### Estrutura do Projeto
```
genie/
├── README.md
├── pyproject.toml
├── .env.example
├── genie/
│   ├── __init__.py
│   ├── main.py                    # ← Comece aqui
│   ├── models/
│   │   └── extraction.py          # ← Depois aqui
│   ├── extraction/
│   │   └── llm/
│   │       └── anthropic.py       # ← E aqui
│   └── ...
```

### Primeiros Commits

```bash
# 1. Setup inicial
git init
git add .
git commit -m "Initial setup: FastAPI + Anthropic integration"

# 2. MVP básico
git add genie/main.py genie/models/ genie/extraction/llm/
git commit -m "Add basic extraction endpoint with LLM"

# 3. Search Library
git add genie/search_library/
git commit -m "Add Search Library with JSON storage"
```

---

## 9. DICAS E TRUQUES

### Performance
```python
# Cache de API keys em memória
from functools import lru_cache

@lru_cache(maxsize=1)
def get_llm_client():
    return AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

### Debug
```python
# Adicionar logs detalhados
import logging
logger = logging.getLogger(__name__)

logger.debug(f"Fingerprint: {fingerprint}")
logger.info(f"Using method: {method}")
logger.error(f"Extraction failed", exc_info=True)
```

### Testes
```python
# tests/test_extraction.py
import pytest
from genie.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_extract_text():
    response = client.post("/api/v1/extract", json={
        "config_id": "test",
        "source": {
            "type": "text",
            "content": "Nome: João\nIdade: 35"
        }
    })
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

---

## 10. TROUBLESHOOTING

### Erro: "Module not found"
```bash
# Reinstalar dependências
poetry install
poetry run python -m genie.main
```

### Erro: "API key not found"
```bash
# Verificar .env
cat .env | grep ANTHROPIC_API_KEY

# Export manual
export ANTHROPIC_API_KEY=your-key-here
```

### Servidor não inicia
```bash
# Verificar porta em uso
lsof -i :8000

# Usar porta diferente
poetry run uvicorn genie.main:app --port 8001
```

---

**Pronto para começar? Siga os passos acima e você terá um MVP funcional em 2-3 dias!**

Para dúvidas ou ajustes neste guia, consulte a documentação completa em `GENIE-SPEC-v2.md` e `GENIE-ARCHITECTURE.md`.
