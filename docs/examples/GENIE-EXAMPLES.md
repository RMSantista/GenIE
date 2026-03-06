# GENIE - Exemplos Práticos e Casos de Uso

---

## 1. CASO DE USO: INTEGRAÇÃO COM TABEX

### 1.1 Contexto
O TABEX atualmente usa REGEX para extrair dados de laudos médicos. Precisa se tornar mais flexível para aceitar diferentes layouts.

### 1.2 Implementação Atual (TABEX)

```javascript
// tabex-current.js (problema: rígido, específico)
function extractMedicalData(pdfText) {
  const regex = {
    paciente: /Paciente:\s*([A-Za-z\s]+)/,
    data: /Data:\s*(\d{2}\/\d{2}\/\d{4})/,
    glicemia: /Glicemia:\s*(\d+)/,
  };
  
  return {
    paciente: pdfText.match(regex.paciente)?.[1],
    data: pdfText.match(regex.data)?.[1],
    glicemia: pdfText.match(regex.glicemia)?.[1],
  };
}
```

**Problemas:**
- Só funciona com layout específico
- Precisa atualizar código para novos layouts
- Não adapta a novos exames automaticamente

### 1.3 Implementação Nova (TABEX + GENIE)

```javascript
// tabex-with-genie.js
import { GenieClient } from 'genie-sdk';

const genie = new GenieClient({
  apiUrl: 'http://localhost:8000',
  apiKey: process.env.GENIE_API_KEY
});

async function extractMedicalData(pdfPath) {
  const result = await genie.extract('medical_reports_v1', {
    type: 'file',
    path: pdfPath
  });
  
  return result.data;
}

// Uso
const data = await extractMedicalData('/uploads/report.pdf');
console.log(data);
// {
//   nome_paciente: "João Silva",
//   data_exame: "15/02/2026",
//   nome_exame: "Hemograma",
//   resultado: "Normal"
// }
```

**Vantagens:**
- Funciona com qualquer layout
- Aprende novos layouts automaticamente
- Adiciona novos campos sem código

### 1.4 Configuração Inicial (Uma vez)

```javascript
// Criar configuração para extração de laudos médicos
const config = await genie.createConfig({
  config_id: 'medical_reports_v1',
  name: 'Extração de Laudos Médicos',
  input: {
    type: 'pdf',
    description: 'Laudos médicos em PDF de diversos laboratórios'
  },
  output: {
    type: 'json',
    schema: {
      nome_paciente: 'string',
      data_exame: 'date',
      nome_exame: 'string',
      resultado: 'string',
      valores_referencia: 'string'
    },
    auto_adapt: true  // Adiciona novos campos automaticamente
  },
  extraction_instructions: `
    Extrair dos laudos médicos:
    - Nome completo do paciente
    - Data de realização do exame
    - Nome do exame realizado
    - Resultado do exame
    - Valores de referência (se houver)
  `,
  llm: {
    provider: 'anthropic',
    model: 'claude-sonnet-4-20250514'
  }
});
```

---

## 2. CASO DE USO: PLANILHA COM AUTO-ADAPTAÇÃO

### 2.1 Cenário
Sistema de controle de exames que gera planilhas. Novos tipos de exames são adicionados frequentemente.

### 2.2 Fluxo Completo

**Estado Inicial da Planilha:**
```csv
Paciente,Data,Glicemia,Hemoglobina
João,01/02/2026,95,14.2
Maria,02/02/2026,110,13.8
```

**Novo Laudo (com exame adicional):**
```
LABORATÓRIO VIDA SAUDÁVEL
Paciente: Pedro Santos
CPF: 123.456.789-00
Data: 03/02/2026

RESULTADOS:
Glicemia: 88 mg/dL
Hemoglobina: 15.1 g/dL
Colesterol Total: 180 mg/dL  ← NOVO EXAME
```

**Código de Extração:**
```python
from genie_sdk import GenieClient

client = GenieClient(api_url="http://localhost:8000")

# Extração
result = client.extract(
    config_id="medical_reports_v1",
    source={
        "type": "file",
        "path": "/uploads/laudo_pedro.pdf"
    }
)

print(result["data"])
# {
#   "nome_paciente": "Pedro Santos",
#   "data_exame": "03/02/2026",
#   "glicemia": "88",
#   "hemoglobina": "15.1",
#   "colesterol_total": "180"  ← NOVO CAMPO
# }
```

**GENIE automaticamente:**
1. Detecta novo campo "colesterol_total"
2. Adiciona coluna à planilha existente
3. Preenche valores anteriores com vazio

**Planilha Atualizada:**
```csv
Paciente,Data,Glicemia,Hemoglobina,Colesterol_Total
João,01/02/2026,95,14.2,
Maria,02/02/2026,110,13.8,
Pedro,03/02/2026,88,15.1,180
```

### 2.3 Código Completo do Processo

```python
# medical_processor.py
from genie_sdk import GenieClient
import pandas as pd
from pathlib import Path

class MedicalReportProcessor:
    def __init__(self, genie_api_url: str):
        self.genie = GenieClient(api_url=genie_api_url)
        self.output_file = "resultados_exames.csv"
    
    async def process_report(self, pdf_path: str):
        """
        Processa um laudo médico e atualiza planilha.
        """
        # 1. Extrair dados do PDF
        result = await self.genie.extract(
            config_id="medical_reports_v1",
            source={
                "type": "file",
                "path": pdf_path
            },
            options={
                "output": {
                    "type": "csv",
                    "destination": self.output_file,
                    "auto_adapt": True  # Crucial para adicionar colunas
                }
            }
        )
        
        # GENIE já salvou no CSV com auto-adaptação
        
        print(f"✓ Processado: {result['data']['nome_paciente']}")
        print(f"  Método: {result['method_used']}")
        print(f"  Tempo: {result['processing_time_ms']}ms")
        
        if result['method_used'] == 'search_library':
            print(f"  Economia: Sem uso de LLM!")
        
        return result

# Uso
processor = MedicalReportProcessor("http://localhost:8000")

# Processar vários laudos
laudos = Path("uploads/laudos").glob("*.pdf")
for laudo in laudos:
    await processor.process_report(str(laudo))
```

---

## 3. CASO DE USO: MÚLTIPLOS LAYOUTS

### 3.1 Cenário
Empresa recebe laudos de 5 laboratórios diferentes, cada um com layout próprio.

### 3.2 Layout A (Laboratório Alpha)

```
═════════════════════════════════════
         LABORATÓRIO ALPHA
═════════════════════════════════════
Paciente: João Silva
CPF: 123.456.789-00
Data Nascimento: 15/03/1985
Data Coleta: 10/02/2026

EXAMES REALIZADOS
─────────────────────────────────────
Glicemia em Jejum
Resultado: 95 mg/dL
Referência: 70-100 mg/dL
─────────────────────────────────────
```

### 3.3 Layout B (Laboratório Beta)

```
BETA LAB | Exames Clínicos
Paciente: João Silva | CPF: 123.456.789-00
Nascimento: 15/03/1985 | Coleta: 10/02/2026

GLICEMIA EM JEJUM.........: 95 mg/dL (70-100)
```

### 3.4 Layout C (Laboratório Gamma)

```
┌──────────────────────────────────────┐
│      LABORATÓRIO GAMMA               │
│      Análises Clínicas               │
└──────────────────────────────────────┘

Nome: João Silva
Documento: 123.456.789-00
Nasc: 15/03/1985  |  Coleta: 10/02/2026

┌──────────────┬──────────┬─────────────┐
│ Exame        │ Valor    │ Ref.        │
├──────────────┼──────────┼─────────────┤
│ Glicemia     │ 95       │ 70-100      │
└──────────────┴──────────┴─────────────┘
```

### 3.5 Como GENIE Lida com Isso

**Primeira extração de cada layout:**
```python
# Layout A (primeira vez)
result_A = await genie.extract("medical_reports_v1", {...})
# Usa LLM, cria pattern para Layout A
# Fingerprint: "a1b2c3d4e5f6g7h8"

# Layout B (primeira vez)
result_B = await genie.extract("medical_reports_v1", {...})
# Usa LLM, cria pattern para Layout B
# Fingerprint: "x9y8z7w6v5u4t3s2"

# Layout C (primeira vez)
result_C = await genie.extract("medical_reports_v1", {...})
# Usa LLM, cria pattern para Layout C
# Fingerprint: "m1n2o3p4q5r6s7t8"
```

**Extrações subsequentes:**
```python
# Layout A novamente (paciente diferente)
result = await genie.extract("medical_reports_v1", {...})
# Reconhece fingerprint "a1b2c3d4e5f6g7h8"
# Usa Search Library (REGEX), NÃO usa LLM
# Processamento: ~50ms, $0.00

# Layout B novamente
result = await genie.extract("medical_reports_v1", {...})
# Reconhece fingerprint "x9y8z7w6v5u4t3s2"
# Usa Search Library (REGEX), NÃO usa LLM
# Processamento: ~50ms, $0.00
```

**Todos retornam o mesmo formato:**
```json
{
  "nome_paciente": "João Silva",
  "cpf": "123.456.789-00",
  "data_nascimento": "15/03/1985",
  "data_coleta": "10/02/2026",
  "exames": [
    {
      "nome": "Glicemia em Jejum",
      "resultado": "95",
      "unidade": "mg/dL",
      "referencia": "70-100"
    }
  ]
}
```

### 3.6 Visualização da Search Library

Após processar os 3 layouts, a Search Library fica:

```json
{
  "patterns": [
    {
      "layout_id": "lab_alpha_v1",
      "fingerprint": "a1b2c3d4e5f6g7h8",
      "name": "Laboratório Alpha",
      "success_rate": 0.98,
      "use_count": 245,
      "fields": [
        {
          "field_name": "nome_paciente",
          "extraction_method": "regex",
          "pattern": "Paciente:\\s*([A-Za-zÀ-ÿ\\s]+)"
        },
        {
          "field_name": "glicemia",
          "extraction_method": "regex",
          "pattern": "Resultado:\\s*(\\d+)\\s*mg/dL"
        }
      ]
    },
    {
      "layout_id": "lab_beta_v1",
      "fingerprint": "x9y8z7w6v5u4t3s2",
      "name": "Laboratório Beta",
      "success_rate": 0.97,
      "use_count": 189,
      "fields": [
        {
          "field_name": "nome_paciente",
          "extraction_method": "regex",
          "pattern": "Paciente:\\s*([^|]+)"
        },
        {
          "field_name": "glicemia",
          "extraction_method": "regex",
          "pattern": "GLICEMIA[^:]*:\\s*(\\d+)"
        }
      ]
    },
    {
      "layout_id": "lab_gamma_v1",
      "fingerprint": "m1n2o3p4q5r6s7t8",
      "name": "Laboratório Gamma",
      "success_rate": 0.99,
      "use_count": 321,
      "fields": [
        {
          "field_name": "nome_paciente",
          "extraction_method": "regex",
          "pattern": "Nome:\\s*([A-Za-zÀ-ÿ\\s]+)"
        },
        {
          "field_name": "glicemia",
          "extraction_method": "instruction",
          "instruction": "Extract value from table row where first column is 'Glicemia'"
        }
      ]
    }
  ]
}
```

---

## 4. CASO DE USO: BANCO DE DADOS

### 4.1 Cenário
Migração de dados de sistema legado (tabelas mal estruturadas) para novo sistema.

### 4.2 Tabela Legada (Problema)

```sql
-- Tabela antiga: tudo em uma coluna de texto
CREATE TABLE exames_antigos (
    id INTEGER,
    dados TEXT  -- JSON malformado, estrutura inconsistente
);

SELECT * FROM exames_antigos;
-- id | dados
-- 1  | "Paciente:João|Exame:Glicemia|Res:95"
-- 2  | "{pac: Maria, ex: Hemoglobina, valor: 14.2}"
-- 3  | "Nome: Pedro; Teste: Colesterol; R=180"
```

### 4.3 Extração com GENIE

```python
from genie_sdk import GenieClient
import psycopg2

client = GenieClient(api_url="http://localhost:8000")

# Conecta ao banco legado
conn = psycopg2.connect("dbname=legacy user=admin")
cursor = conn.cursor()

# Busca registros
cursor.execute("SELECT id, dados FROM exames_antigos")

for row_id, dados_texto in cursor.fetchall():
    # GENIE extrai dados do texto bagunçado
    result = client.extract(
        config_id="legacy_migration",
        source={
            "type": "text",
            "content": dados_texto
        },
        options={
            "output": {
                "type": "database",
                "connection": "postgresql://user:pass@localhost/novo_sistema",
                "table": "exames_normalizados"
            }
        }
    )
    
    print(f"✓ Migrado registro {row_id}")

# Resultado: Tabela nova estruturada
# exames_normalizados:
# | id | paciente    | exame        | resultado |
# |  1 | João Silva  | Glicemia     | 95        |
# |  2 | Maria       | Hemoglobina  | 14.2      |
# |  3 | Pedro       | Colesterol   | 180       |
```

---

## 5. CASO DE USO: API PARA MÚLTIPLOS CLIENTES

### 5.1 Cenário
SaaS que oferece extração de dados como serviço para diferentes empresas.

### 5.2 Arquitetura Multi-tenant

```python
# genie_saas.py
from fastapi import FastAPI, Depends, HTTPException
from genie_sdk import GenieClient

app = FastAPI()

# Cada tenant tem sua própria config
TENANT_CONFIGS = {
    "hospital_a": {
        "config_id": "hospital_a_reports",
        "allowed_formats": ["pdf", "image"],
    },
    "clinica_b": {
        "config_id": "clinica_b_exams",
        "allowed_formats": ["pdf", "xlsx"],
    },
}

@app.post("/api/extract/{tenant_id}")
async def extract_for_tenant(
    tenant_id: str,
    file: UploadFile,
    api_key: str = Depends(validate_api_key)
):
    if tenant_id not in TENANT_CONFIGS:
        raise HTTPException(404, "Tenant not found")
    
    config = TENANT_CONFIGS[tenant_id]
    
    # Salva arquivo temporariamente
    temp_path = f"/tmp/{tenant_id}_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())
    
    # GENIE extrai
    genie = GenieClient(api_url="http://genie:8000")
    result = await genie.extract(
        config_id=config["config_id"],
        source={
            "type": "file",
            "path": temp_path
        }
    )
    
    # Limpa arquivo temp
    os.remove(temp_path)
    
    return {
        "tenant": tenant_id,
        "data": result["data"],
        "metadata": {
            "method": result["method_used"],
            "processing_time": result["processing_time_ms"]
        }
    }
```

### 5.3 Cliente (Hospital A)

```javascript
// hospital-a-app.js
const response = await fetch('https://saas.example.com/api/extract/hospital_a', {
  method: 'POST',
  headers: {
    'X-API-Key': 'hospital-a-secret-key'
  },
  body: formData // PDF do laudo
});

const result = await response.json();
console.log(result.data);
// {
//   nome_paciente: "...",
//   data_exame: "...",
//   ...
// }
```

---

## 6. EXEMPLO: CORREÇÃO MANUAL NA BIBLIOTECA

### 6.1 Cenário
Pattern REGEX criado automaticamente está capturando dados errados.

### 6.2 Problema Detectado

```python
# Extração retorna dados errados
result = await genie.extract("medical_reports_v1", {...})
print(result["data"]["resultado"])
# "Normal\nObservações: Paciente em jejum"
# ❌ Capturou além do necessário
```

### 6.3 Inspeção da Biblioteca

```bash
# API endpoint para debug
GET /api/v1/library/patterns/lab_alpha_v1
```

```json
{
  "layout_id": "lab_alpha_v1",
  "fields": [
    {
      "field_name": "resultado",
      "extraction_method": "regex",
      "pattern": "Resultado:\\s*(.+)",  // ❌ Muito ganancioso
      "success_rate": 0.75  // Baixa taxa de sucesso
    }
  ]
}
```

### 6.4 Correção Manual

**Opção 1: Via API**
```python
# Atualizar pattern
await genie.update_pattern(
    layout_id="lab_alpha_v1",
    field_name="resultado",
    new_pattern="Resultado:\\s*([^\\n]+)"  // ✓ Para na primeira quebra de linha
)
```

**Opção 2: Edição direta do JSON**
```json
{
  "field_name": "resultado",
  "extraction_method": "regex",
  "pattern": "Resultado:\\s*([^\\n]+)",
  "manual_correction": true,
  "corrected_at": "2026-02-16T10:00:00Z"
}
```

### 6.5 Validação

```python
# Testa novamente
result = await genie.extract("medical_reports_v1", {...})
print(result["data"]["resultado"])
# "Normal"
# ✓ Correto!

# Verifica taxa de sucesso
stats = await genie.get_pattern_stats("lab_alpha_v1", "resultado")
print(stats["success_rate"])
# 0.98
# ✓ Melhorou!
```

---

## 7. EXEMPLO: INTEGRAÇÃO COM STREAMLIT

### 7.1 Interface de Configuração

```python
# genie_config_ui.py
import streamlit as st
from genie_sdk import GenieClient

st.title("🧞 GENIE - Configurador de Extração")

# Inicializa cliente
genie = GenieClient(api_url=st.secrets["GENIE_URL"])

# 1. Nome da configuração
config_name = st.text_input("Nome da Configuração", "minha_extracao")

# 2. Formato de entrada
input_type = st.selectbox(
    "Formato de Entrada",
    ["PDF", "Imagem", "Planilha (XLSX)", "Texto", "JSON"]
)

# 3. Campos a extrair (conversacional)
st.subheader("💬 Defina o que extrair")
user_input = st.text_area(
    "Descreva quais informações você precisa extrair:",
    "Preciso extrair nome do cliente, data da compra e valor total de notas fiscais"
)

if st.button("✨ Gerar Schema Automaticamente"):
    # GENIE usa LLM para entender e criar schema
    schema = await genie.generate_schema_from_description(user_input)
    st.session_state["schema"] = schema
    st.success("Schema gerado!")

# 4. Preview do schema
if "schema" in st.session_state:
    st.json(st.session_state["schema"])
    
    # 5. Formato de saída
    output_type = st.selectbox(
        "Formato de Saída",
        ["JSON", "CSV", "Planilha (XLSX)", "Banco de Dados"]
    )
    
    # 6. LLM Provider
    llm_provider = st.selectbox("Provider LLM", ["Anthropic", "OpenAI"])
    api_key = st.text_input("API Key", type="password")
    
    # 7. Criar configuração
    if st.button("💾 Salvar Configuração"):
        config = {
            "config_id": config_name,
            "input": {"type": input_type.lower()},
            "output": {
                "type": output_type.lower(),
                "schema": st.session_state["schema"]
            },
            "llm": {
                "provider": llm_provider.lower(),
                "api_key": api_key
            }
        }
        
        result = await genie.create_config(config)
        st.success(f"✓ Configuração '{config_name}' criada!")
        st.balloons()

# 8. Testar extração
st.divider()
st.subheader("🧪 Testar Extração")

uploaded_file = st.file_uploader("Upload de arquivo para teste")

if uploaded_file and st.button("Extrair"):
    with st.spinner("Extraindo..."):
        # Salva temporariamente
        temp_path = f"/tmp/{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Extrai
        result = await genie.extract(
            config_id=config_name,
            source={"type": "file", "path": temp_path}
        )
        
        # Mostra resultado
        st.success(f"✓ Extraído em {result['processing_time_ms']}ms")
        st.json(result["data"])
        
        # Métricas
        col1, col2 = st.columns(2)
        col1.metric("Método", result["method_used"])
        col2.metric("Confiança", f"{result['confidence']:.0%}")
```

---

## 8. MÉTRICAS E MONITORAMENTO

### 8.1 Dashboard de Performance

```python
# genie_metrics.py
from genie_sdk import GenieClient
import pandas as pd
import plotly.express as px

client = GenieClient(api_url="http://localhost:8000")

# Busca métricas
metrics = await client.get_metrics(
    config_id="medical_reports_v1",
    start_date="2026-02-01",
    end_date="2026-02-16"
)

df = pd.DataFrame(metrics)

# Visualizações
fig1 = px.pie(
    df,
    names='method_used',
    title='Distribuição: LLM vs Search Library'
)
# Search Library: 85% (economia!)
# LLM: 15% (layouts novos)

fig2 = px.line(
    df,
    x='date',
    y='processing_time_ms',
    color='method_used',
    title='Tempo de Processamento'
)
# Search Library: ~50ms
# LLM: ~2000ms

fig3 = px.bar(
    df.groupby('layout_id').size().reset_index(),
    x='layout_id',
    y=0,
    title='Layouts Reconhecidos'
)
# 12 layouts diferentes identificados automaticamente
```

---

## 9. TROUBLESHOOTING COMUM

### 9.1 "Layout não reconhecido apesar de ser igual"

**Problema:** Pequenas diferenças no PDF (metadata, formatação)

**Solução:** Ajustar sensibilidade do fingerprint
```python
# genie/extraction/layout/fingerprint.py
class LayoutFingerprint:
    def __init__(self, sensitivity="medium"):
        # "low": Mais tolerante a diferenças
        # "medium": Padrão
        # "high": Estrito
        self.sensitivity = sensitivity
```

### 9.2 "Extração retornando dados errados"

**Diagnóstico:**
```python
result = await genie.extract(..., options={"debug": True})
print(result["debug_info"])
# {
#   "pattern_used": "lab_alpha_v1.resultado",
#   "regex": "Resultado:\s*(.+)",
#   "match": "Normal\nObservações...",
#   "confidence": 0.65
# }
```

**Correção:** Ver exemplo seção 6.

### 9.3 "Muito lento, sempre usa LLM"

**Causa:** Search Library não está sendo populada

**Verificação:**
```python
stats = await genie.get_library_stats()
print(stats)
# {
#   "total_patterns": 0,  # ❌ Vazio!
#   "avg_success_rate": 0
# }
```

**Solução:** Garantir que `auto_create_patterns: true` está configurado.

---

## 10. ROADMAP DE IMPLANTAÇÃO

### Semana 1-2: Setup + Primeiro Caso
- [x] Setup GENIE local
- [ ] Configurar extração de laudos (TABEX)
- [ ] Processar primeiros 100 laudos
- [ ] Validar acurácia

### Semana 3-4: Otimização
- [ ] Analisar patterns criados
- [ ] Correções manuais necessárias
- [ ] Adicionar novos laboratórios
- [ ] Medir economia de tokens

### Semana 5-6: Expansão
- [ ] Novos formatos (XLSX, imagens)
- [ ] Integração com sistema legado
- [ ] API pública para outros apps
- [ ] Documentação completa

### Semana 7-8: Produção
- [ ] Deploy em servidor
- [ ] Monitoramento
- [ ] Backup de Search Library
- [ ] Treinamento de equipe

---

**Estes exemplos cobrem os casos de uso mais comuns. Para casos específicos, consulte a documentação completa ou abra uma issue no repositório.**
