# GENIE - Generic Extractor of Information Engine
## Especificação Técnica v2.0

---

## 1. VISÃO GERAL

### 1.1 O que é o GENIE
O GENIE é um **framework de extração inteligente de informações** que pode ser conectado a qualquer sistema ou aplicação através de uma API, permitindo a extração automatizada de dados específicos de diversos formatos de arquivo.

**Características principais:**
- Framework Python com API RESTful
- Interoperabilidade total (ex: TABEX em JavaScript pode consumir a API)
- Extração baseada em LLM com fallback para métodos tradicionais
- Biblioteca de busca inteligente para evitar tokenização repetida
- Adaptação automática a mudanças de estrutura

### 1.2 Arquitetura de Alto Nível
```
┌─────────────────────────────────────────────────────────┐
│                    APLICAÇÕES CLIENTES                   │
│              (TABEX, outros apps JS/Python/etc)          │
└───────────────────────┬─────────────────────────────────┘
                        │
                   API REST/GraphQL
                        │
┌───────────────────────▼─────────────────────────────────┐
│                    GENIE CORE (Python)                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Configuration Manager                    │   │
│  │  • Input/Output Format Selection                │   │
│  │  • LLM Conversation Interface                   │   │
│  │  • API Key Management                           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Extraction Engine                        │   │
│  │  • MCP Integration (File Reading)               │   │
│  │  • Layout Recognition                           │   │
│  │  • LLM-based Extraction                         │   │
│  │  • Search Library Lookup                        │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Search Library (JSON/SQLite)             │   │
│  │  • REGEX Patterns                               │   │
│  │  • SQL Queries                                  │   │
│  │  • Extraction Instructions                      │   │
│  │  • Layout Fingerprints                          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Output Manager                           │   │
│  │  • Format Conversion                            │   │
│  │  • Schema Adaptation                            │   │
│  │  • Auto-column Generation                       │   │
│  └─────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        ▼                               ▼
  ┌──────────┐                   ┌──────────┐
  │   LLM    │                   │   OCR    │
  │ Provider │                   │ Fallback │
  └──────────┘                   └──────────┘
```

---

## 2. CONFIGURAÇÃO

### 2.1 Interface de Configuração

A tela de configuração do GENIE permite:

#### 2.1.1 Seleção de Formatos
**Entrada (Input):**
- Arquivos: TXT, PDF, Imagens (JPG, PNG), DOCX, XLSX, CSV
- Estruturados: JSON, XML, YAML
- Bancos de Dados: PostgreSQL, MySQL, MongoDB, SQLite
- Variáveis em memória

**Saída (Output):**
- Arquivos: JSON, XML, YAML, CSV, XLSX
- Bancos de Dados: Tabelas relacionais ou NoSQL
- Variáveis (para integração programática)
- API Response (direto para cliente)

#### 2.1.2 Campo Conversacional com LLM
Interface de chat para definir:
```
Usuário: "Preciso extrair nome do paciente, data do exame, 
         nome do exame e resultado de laudos médicos em PDF"

GENIE: "Entendi. Vou configurar a extração para:
        - Campo: nome_paciente (tipo: string)
        - Campo: data_exame (tipo: date, formato: DD/MM/YYYY)
        - Campo: nome_exame (tipo: string)
        - Campo: resultado (tipo: string)
        
        Qual formato de saída você prefere?"
```

#### 2.1.3 Gerenciamento de API Keys
- Suporte para múltiplos provedores LLM:
  - Anthropic (Claude)
  - OpenAI (GPT)
  - Google (Gemini)
  - Outros compatíveis
- Armazenamento seguro de credenciais
- Rotação de chaves

### 2.2 Estrutura de Configuração
```json
{
  "extraction_id": "medicalReports_v1",
  "input": {
    "type": "pdf",
    "source": "/path/to/folder",
    "access_mode": "local_secure"
  },
  "output": {
    "type": "json",
    "destination": "/path/to/output",
    "schema": {
      "nome_paciente": "string",
      "data_exame": "date",
      "nome_exame": "string",
      "resultado": "string"
    },
    "auto_adapt": true
  },
  "llm": {
    "provider": "anthropic",
    "model": "claude-sonnet-4-20250514",
    "api_key_ref": "key_001",
    "fallback_to_ocr": true
  },
  "behavior": {
    "use_search_library": true,
    "auto_create_patterns": true,
    "layout_independent": true,
    "update_on_change": true
  }
}
```

---

## 3. COMPORTAMENTO

### 3.1 Fluxo de Extração

```
┌─────────────────────────────────────────────────────────┐
│ 1. ACESSO SEGURO AO ARQUIVO/DATABASE                    │
│    • MCP para leitura de arquivos                       │
│    • Conexão segura a DB (não vai para treinamento)    │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│ 2. VERIFICAÇÃO DE LAYOUT                                │
│    • Calcula fingerprint do documento                   │
│    • Busca na Search Library                            │
└───────────────────┬─────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼ Layout Conhecido      ▼ Layout Novo/Alterado
┌──────────────────┐     ┌──────────────────────────┐
│ 3A. USO DA       │     │ 3B. EXTRAÇÃO COM LLM     │
│ SEARCH LIBRARY   │     │    • OCR se necessário    │
│  • REGEX         │     │    • Interpretação direta │
│  • SQL Query     │     │    • Criação de padrões   │
│  • Instructions  │     │    • Atualiza Library     │
└──────────────────┘     └──────────────────────────┘
        │                       │
        └───────────┬───────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│ 4. VERIFICAÇÃO/CRIAÇÃO DE SAÍDA                         │
│    • Saída existente? → Usa estrutura existente         │
│    • Saída nova? → Cria conforme schema                 │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│ 5. ADAPTAÇÃO AUTOMÁTICA                                 │
│    • Novos campos detectados? → Adiciona colunas        │
│    • Mudança de estrutura? → Ajusta output              │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│ 6. RETORNO/GRAVAÇÃO                                     │
│    • Escreve no formato de saída configurado            │
│    • Retorna via API se solicitado                      │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Exemplo Prático: Planilha de Exames

**Cenário Inicial:**
```csv
Paciente,Data,Glicemia,Hemoglobina
João,01/02/2026,95,14.2
Maria,02/02/2026,110,13.8
```

**Novo documento com exame adicional (Colesterol):**
```
Paciente: Pedro
Data: 03/02/2026
Glicemia: 88
Hemoglobina: 15.1
Colesterol: 180  ← NOVO CAMPO
```

**GENIE detecta e adapta automaticamente:**
```csv
Paciente,Data,Glicemia,Hemoglobina,Colesterol
João,01/02/2026,95,14.2,
Maria,02/02/2026,110,13.8,
Pedro,03/02/2026,88,15.1,180
```

### 3.3 Independência de Layout

O GENIE deve extrair informações independente do layout:

**Layout A (Vertical):**
```
Nome: João Silva
CPF: 123.456.789-00
Idade: 35 anos
```

**Layout B (Horizontal):**
```
Nome: João Silva | CPF: 123.456.789-00 | Idade: 35 anos
```

**Layout C (Tabular):**
```
┌──────────────┬──────────────────┬───────┐
│ Nome         │ CPF              │ Idade │
├──────────────┼──────────────────┼───────┤
│ João Silva   │ 123.456.789-00   │ 35    │
└──────────────┴──────────────────┴───────┘
```

**Resultado esperado (sempre o mesmo):**
```json
{
  "nome": "João Silva",
  "cpf": "123.456.789-00",
  "idade": "35"
}
```

### 3.4 Estratégia OCR vs Interpretação Direta

**Quando usar OCR:**
- PDFs scaneados (imagens)
- Documentos com má qualidade de renderização
- Fallback quando LLM não consegue interpretar diretamente

**Quando usar Interpretação Direta:**
- PDFs nativos (texto selecionável)
- Documentos estruturados (JSON, XML, YAML)
- Planilhas (XLSX, CSV)
- Bancos de dados

**Fluxo de decisão:**
```python
if input_type == "image" or is_scanned_pdf(document):
    text = ocr_engine.extract(document)
    data = llm_extract(text, schema)
elif input_type in ["pdf", "docx"]:
    try:
        text = direct_text_extraction(document)
        data = llm_extract(text, schema)
    except:
        text = ocr_engine.extract(document)
        data = llm_extract(text, schema)
else:  # structured data
    data = structured_extract(document, schema)
```

---

## 4. BIBLIOTECA DE BUSCA (Search Library)

### 4.1 Propósito
Evitar tokenização e custos desnecessários com LLM para buscas repetitivas em layouts conhecidos.

### 4.2 Estrutura

**Opção 1: Arquivo JSON (mais leve)**
```json
{
  "patterns": [
    {
      "layout_id": "medical_report_format_A",
      "fingerprint": "hash_of_layout_structure",
      "created_at": "2026-02-16T10:00:00Z",
      "last_used": "2026-02-16T15:30:00Z",
      "success_rate": 0.98,
      "fields": [
        {
          "field_name": "nome_paciente",
          "extraction_method": "regex",
          "pattern": "Nome:\\s*([A-Za-zÀ-ÿ\\s]+)",
          "validation": "^[A-Za-zÀ-ÿ\\s]{3,100}$"
        },
        {
          "field_name": "data_exame",
          "extraction_method": "regex",
          "pattern": "Data:\\s*(\\d{2}/\\d{2}/\\d{4})",
          "post_process": "parse_date_br"
        },
        {
          "field_name": "resultado",
          "extraction_method": "instruction",
          "instruction": "Extract text between 'Resultado:' and 'Observações:'"
        }
      ]
    }
  ],
  "metadata": {
    "version": "1.0",
    "total_patterns": 1,
    "last_updated": "2026-02-16T15:30:00Z"
  }
}
```

**Opção 2: SQLite (mais estruturado)**
```sql
CREATE TABLE layouts (
    layout_id TEXT PRIMARY KEY,
    fingerprint TEXT UNIQUE,
    created_at TIMESTAMP,
    last_used TIMESTAMP,
    success_rate REAL,
    use_count INTEGER
);

CREATE TABLE extraction_patterns (
    pattern_id INTEGER PRIMARY KEY,
    layout_id TEXT,
    field_name TEXT,
    extraction_method TEXT, -- 'regex', 'query', 'instruction'
    pattern TEXT,
    validation TEXT,
    post_process TEXT,
    FOREIGN KEY (layout_id) REFERENCES layouts(layout_id)
);

CREATE INDEX idx_fingerprint ON layouts(fingerprint);
CREATE INDEX idx_layout_field ON extraction_patterns(layout_id, field_name);
```

### 4.3 Criação Automática de Padrões

Quando a LLM extrai dados com sucesso, o GENIE automaticamente:

1. **Identifica o layout** via fingerprint
2. **Gera padrões REGEX/Query** baseado na extração bem-sucedida
3. **Armazena na biblioteca** para uso futuro
4. **Valida** em próxima extração similar

**Exemplo de auto-criação:**
```python
# LLM extrai com sucesso
extracted_data = {
    "nome_paciente": "João Silva",
    "data_exame": "15/02/2026"
}

# GENIE analisa o contexto de onde veio
context = """
Paciente: João Silva
Data do Exame: 15/02/2026
"""

# GENIE cria padrão automaticamente
pattern = {
    "field_name": "nome_paciente",
    "extraction_method": "regex",
    "pattern": "Paciente:\\s*([A-Za-zÀ-ÿ\\s]+)",
    "context": "Found after label 'Paciente:'"
}

# Adiciona à biblioteca
search_library.add_pattern(layout_fingerprint, pattern)
```

### 4.4 Fallback e Manutenção

**Quando usar a Biblioteca:**
- Layout reconhecido (fingerprint match)
- Taxa de sucesso > 95%
- Informação de busca não alterada

**Quando usar LLM:**
- Layout não reconhecido
- Taxa de sucesso < 95%
- Mudança no prompt de extração
- Falha na validação do resultado

**Correção Manual:**
```json
{
  "manual_corrections": [
    {
      "layout_id": "medical_report_format_A",
      "field_name": "resultado",
      "old_pattern": "Resultado:\\s*(.+)",
      "new_pattern": "Resultado:\\s*([^\\n]+)",
      "reason": "Pattern was too greedy, capturing multiple lines",
      "corrected_by": "admin",
      "corrected_at": "2026-02-16T16:00:00Z"
    }
  ]
}
```

### 4.5 Recomendação de Implementação

**Para começar:** JSON (simplicidade, portabilidade)
**Para produção em escala:** SQLite (performance, queries complexas, concorrência)

**Migração futura:**
```python
class SearchLibrary:
    def __init__(self, storage_type="json"):
        if storage_type == "json":
            self.storage = JSONStorage()
        elif storage_type == "sqlite":
            self.storage = SQLiteStorage()
        
    def migrate_to_sqlite(self):
        """Migra dados de JSON para SQLite"""
        pass
```

---

## 5. INTEROPERABILIDADE

### 5.1 API REST

**Endpoint principal:**
```
POST /api/v1/extract
Content-Type: application/json

{
  "config_id": "medical_reports_v1",
  "source": {
    "type": "file",
    "path": "/secure/uploads/report.pdf"
  },
  "options": {
    "use_cache": true,
    "force_llm": false
  }
}

Response:
{
  "extraction_id": "ext_12345",
  "status": "success",
  "method_used": "search_library",
  "data": {
    "nome_paciente": "João Silva",
    "data_exame": "15/02/2026",
    "nome_exame": "Hemograma Completo",
    "resultado": "Normal"
  },
  "confidence": 0.98,
  "processing_time_ms": 45
}
```

### 5.2 Cliente JavaScript (para TABEX)

```javascript
// genie-client.js
class GenieClient {
  constructor(apiUrl, apiKey) {
    this.apiUrl = apiUrl;
    this.apiKey = apiKey;
  }

  async extract(configId, source, options = {}) {
    const response = await fetch(`${this.apiUrl}/api/v1/extract`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey
      },
      body: JSON.stringify({
        config_id: configId,
        source: source,
        options: options
      })
    });

    return await response.json();
  }

  async createConfig(config) {
    const response = await fetch(`${this.apiUrl}/api/v1/configs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey
      },
      body: JSON.stringify(config)
    });

    return await response.json();
  }
}

// Uso no TABEX
const genie = new GenieClient('http://localhost:8000', 'your-api-key');

const result = await genie.extract('medical_reports_v1', {
  type: 'file',
  path: '/uploads/patient-report.pdf'
});

console.log(result.data);
```

### 5.3 SDK Python

```python
# genie_sdk.py
from genie import GenieClient

client = GenieClient(
    api_url="http://localhost:8000",
    api_key="your-api-key"
)

result = client.extract(
    config_id="medical_reports_v1",
    source={
        "type": "file",
        "path": "/uploads/patient-report.pdf"
    }
)

print(result["data"])
```

---

## 6. SEGURANÇA E PRIVACIDADE

### 6.1 Proteção de Dados

**Dados não vão para treinamento:**
- Uso de APIs LLM com zero data retention (ZDR)
- Opção de LLM local/on-premise para dados sensíveis
- Criptografia de dados em trânsito e em repouso

**Acesso seguro:**
```python
# Exemplo de acesso seguro a pasta/DB
from genie.security import SecureFileAccess

# Não expõe path completo para LLM
secure_access = SecureFileAccess(
    allowed_paths=["/data/medical"],
    encryption_key=os.environ["GENIE_ENCRYPTION_KEY"]
)

# LLM recebe apenas conteúdo, não paths
content = secure_access.read("/data/medical/report.pdf")
extracted = llm_extract(content, schema)
```

### 6.2 API Key Management

```python
# Armazenamento seguro
from cryptography.fernet import Fernet

class SecureKeyStore:
    def __init__(self, master_key):
        self.cipher = Fernet(master_key)
    
    def store_api_key(self, provider, key):
        encrypted = self.cipher.encrypt(key.encode())
        # Armazena encrypted em DB/arquivo seguro
    
    def get_api_key(self, provider):
        encrypted = self.load_from_storage(provider)
        return self.cipher.decrypt(encrypted).decode()
```

---

## 7. ROADMAP DE DESENVOLVIMENTO

### Fase 1: MVP Core (4-6 semanas)
- [ ] Setup projeto Python com FastAPI
- [ ] Interface básica de configuração
- [ ] Extração com LLM (Anthropic/OpenAI)
- [ ] Suporte a PDF e TXT
- [ ] Search Library em JSON
- [ ] API REST básica

### Fase 2: Biblioteca de Busca (3-4 semanas)
- [ ] Auto-criação de padrões REGEX
- [ ] Sistema de fingerprinting de layouts
- [ ] Fallback inteligente LLM/Library
- [ ] Migração para SQLite
- [ ] Interface de correção manual

### Fase 3: Formatos Múltiplos (4-5 semanas)
- [ ] Suporte a imagens (OCR)
- [ ] Planilhas (XLSX, CSV)
- [ ] Bancos de dados (PostgreSQL, MongoDB)
- [ ] Adaptação automática de schema
- [ ] MCP integration

### Fase 4: Interoperabilidade (3-4 semanas)
- [ ] SDK JavaScript
- [ ] SDK Python
- [ ] Documentação de API
- [ ] Integração com TABEX
- [ ] Testes de carga

### Fase 5: Produção (4-6 semanas)
- [ ] Sistema de autenticação/autorização
- [ ] Monitoramento e logging
- [ ] Otimização de performance
- [ ] Deploy em containers
- [ ] Documentação completa

---

## 8. TECNOLOGIAS E DEPENDÊNCIAS

### 8.1 Backend (Python)
```txt
fastapi>=0.110.0
uvicorn>=0.27.0
anthropic>=0.18.0
openai>=1.12.0
pydantic>=2.6.0
python-multipart>=0.0.9
pytesseract>=0.3.10  # OCR
PyPDF2>=3.0.0
openpyxl>=3.1.0
sqlalchemy>=2.0.0
cryptography>=42.0.0
```

### 8.2 Frontend (Configuração UI)
```txt
React 18+ ou Streamlit (mais rápido para MVP)
TailwindCSS
shadcn/ui components
```

### 8.3 Infraestrutura
- Docker + Docker Compose
- Nginx (reverse proxy)
- PostgreSQL (dados de configuração)
- SQLite (search library)
- Redis (cache, opcional)

---

## 9. MÉTRICAS DE SUCESSO

### 9.1 Performance
- Tempo de extração < 2s para documentos simples
- Tempo de extração < 10s para documentos complexos
- Taxa de acerto > 95% com Search Library
- Taxa de acerto > 90% com LLM (layouts novos)

### 9.2 Economia
- Redução de 80%+ em tokens LLM após construção da Search Library
- 10+ layouts diferentes reconhecidos automaticamente
- Adaptação automática a mudanças em < 5s

### 9.3 Usabilidade
- Configuração de nova extração em < 5 minutos
- Tempo de resposta da API < 100ms (excluindo processamento)
- Zero configuração manual de REGEX pelo usuário final

---

## 10. PRÓXIMOS PASSOS

Para o desenvolvimento do GENIE, vamos seguir esta ordem:

1. **Definição de arquitetura detalhada**
   - Escolha final: JSON vs SQLite para Search Library
   - Definição de estrutura de pastas do projeto
   - Setup inicial do repositório

2. **Implementação do Core**
   - FastAPI + estrutura básica
   - Sistema de configuração
   - Primeiro extrator com LLM

3. **Iteração com TABEX**
   - Usar TABEX como primeiro caso de uso real
   - Validação e ajustes
   - Criação da Search Library inicial

4. **Expansão e generalização**
   - Novos formatos
   - Novos casos de uso
   - Documentação e SDKs

---

**Documento vivo - será atualizado conforme desenvolvimento**
