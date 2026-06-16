# 🚀 Teste Rápido - GenIE Phase 1

## Roteiro em 5 passos

### **Passo 1: Preparar ambiente**
```bash
cd /home/rodrigo/GenIE

# Se necessário, instale python3-venv (execute 1x)
sudo apt-get install python3.12-venv

# Crie venv se não existir
python3 -m venv venv
source venv/bin/activate

# Instale dependências
pip install -r requirements.txt
```

---

### **Passo 2: Configurar API keys**
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# EDITE .env e adicione sua chave Anthropic:
# ANTHROPIC_API_KEY=sk-ant-xxxxx

# Você pode usar um arquivo fictício para testes iniciais
nano .env
```

---

### **Passo 3: Rodar testes unitários**
```bash
source venv/bin/activate
pytest tests/unit/ -v
```

**Esperado:** Todos os testes devem passar ✓

---

### **Passo 4: Iniciar o servidor**
```bash
source venv/bin/activate
uvicorn spec.main:app --reload --port 8000
```

**Esperado:** Servidor inicia na porta 8000
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

### **Passo 5: Testar API (em outro terminal)**
```bash
# Teste 1: Health Check (sem API key)
curl http://localhost:8000/api/v1/health

# Esperado: {"status":"healthy"}
```

**Com texto simples (requer ANTHROPIC_API_KEY válida):**
```bash
curl -X POST http://localhost:8000/api/v1/extract \
  -H "Content-Type: application/json" \
  -d '{
    "config_id": "test_001",
    "source": {
      "type": "text",
      "content": "Patient Name: John Doe\nAge: 35\nDiagnosis: Diabetes"
    }
  }'
```

**Esperado:** Resposta JSON com dados extraídos
```json
{
  "extraction_id": "uuid-xxx",
  "status": "success",
  "method_used": "llm",
  "data": {
    "Patient Name": "John Doe",
    "Age": 35,
    "Diagnosis": "Diabetes"
  },
  "confidence": 0.95,
  "processing_time_ms": 2500
}
```

---

## 📊 Checklist de Teste

- [ ] Passo 1: Ambiente pronto
- [ ] Passo 2: .env configurado com API key
- [ ] Passo 3: Testes unitários passam
- [ ] Passo 4: Servidor roda sem erros
- [ ] Passo 5: Health check retorna 200
- [ ] Passo 5: Extração com texto funciona

---

## 🐛 Troubleshooting

**Erro: "No module named 'spec'"**
→ Execute `source venv/bin/activate` antes de rodar pytest/uvicorn

**Erro: "ANTHROPIC_API_KEY not found"**
→ Configure `.env` com sua chave Anthropic válida

**Erro: "Connection timeout"**
→ Verifique se uvicorn está rodando: `curl http://localhost:8000/api/v1/health`

---

## 📝 O que será testado

✅ Infrastructure (FastAPI, Pydantic)
✅ Health endpoint
✅ Extraction engine completo
✅ LLM integration (Anthropic Claude)
✅ Layout fingerprinting
✅ Search Library (patterns.json)
✅ Error handling

---

**Status:** Phase 1 pronta para testes
**Próximo passo:** Homologação e feedback
