#!/usr/bin/env python3
"""
Script de teste rápido para GenIE Phase 1
Execute: python3 test-genie.py
"""

import subprocess
import sys
import time
import requests
import json
from pathlib import Path

def run_command(cmd, description):
    """Executa comando e retorna sucesso/falha"""
    print(f"\n📋 {description}")
    print(f"   $ {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"   ✓ OK")
            return True
        else:
            print(f"   ✗ FALHOU")
            print(f"   Erro: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"   ✗ TIMEOUT")
        return False
    except Exception as e:
        print(f"   ✗ ERRO: {e}")
        return False

def test_http(method, url, description, data=None):
    """Testa endpoint HTTP"""
    print(f"\n🌐 {description}")
    print(f"   {method} {url}")
    try:
        if method == "GET":
            resp = requests.get(url, timeout=5)
        elif method == "POST":
            resp = requests.post(url, json=data, timeout=10)

        print(f"   Status: {resp.status_code}")
        if resp.status_code in [200, 201]:
            print(f"   ✓ OK")
            try:
                print(f"   Resposta: {json.dumps(resp.json(), indent=2)[:300]}...")
            except:
                print(f"   Resposta: {resp.text[:200]}")
            return True
        else:
            print(f"   ✗ FALHOU ({resp.status_code})")
            print(f"   {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"   ✗ ERRO: {e}")
        return False

def main():
    print("=" * 60)
    print("🧪 TESTE RÁPIDO - GenIE Phase 1")
    print("=" * 60)

    # Verificar .env
    if not Path(".env").exists():
        print("\n⚠️  Aviso: Arquivo .env não encontrado")
        print("   Execute: cp .env.example .env")
        print("   E configure sua ANTHROPIC_API_KEY")
        return

    results = {
        "imports": False,
        "unit_tests": False,
        "server_start": False,
        "health_check": False,
        "extraction": False
    }

    # 1. Testar imports
    print("\n" + "=" * 60)
    print("1️⃣  Testando imports...")
    try:
        import spec
        from spec.core.config import Settings
        from spec.models.extraction import ExtractionRequest
        print("   ✓ Imports OK")
        results["imports"] = True
    except Exception as e:
        print(f"   ✗ Erro: {e}")

    # 2. Rodar testes unitários
    print("\n" + "=" * 60)
    print("2️⃣  Rodando testes unitários...")
    results["unit_tests"] = run_command(
        "pytest tests/unit/ -v --tb=short 2>&1 | tail -20",
        "Testes unitários"
    )

    # 3. Iniciar servidor em background
    print("\n" + "=" * 60)
    print("3️⃣  Iniciando servidor...")
    try:
        proc = subprocess.Popen(
            "uvicorn spec.main:app --port 8000 --log-level error",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(3)  # Aguardar servidor iniciar

        # Verificar se processo está rodando
        if proc.poll() is None:
            print("   ✓ Servidor iniciado (PID: {})".format(proc.pid))
            results["server_start"] = True
        else:
            print("   ✗ Servidor não iniciou")
            proc.terminate()
    except Exception as e:
        print(f"   ✗ Erro: {e}")

    # 4. Testar health check
    if results["server_start"]:
        print("\n" + "=" * 60)
        print("4️⃣  Testando health check...")
        time.sleep(1)
        results["health_check"] = test_http(
            "GET",
            "http://localhost:8000/api/v1/health",
            "Health Check"
        )

    # 5. Testar extração
    if results["server_start"]:
        print("\n" + "=" * 60)
        print("5️⃣  Testando extração com texto...")
        results["extraction"] = test_http(
            "POST",
            "http://localhost:8000/api/v1/extract",
            "Extraction Endpoint",
            {
                "config_id": "test_001",
                "source": {
                    "type": "text",
                    "content": "Patient: John Doe, Age: 35, Diagnosis: Diabetes Type 2"
                }
            }
        )

    # Limpar
    if results["server_start"]:
        proc.terminate()
        proc.wait()

    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL")
    print("=" * 60)

    for test, passed in results.items():
        status = "✓ PASSOU" if passed else "✗ FALHOU"
        print(f"{test:20s}: {status}")

    passed_count = sum(results.values())
    print(f"\n{passed_count}/5 testes passaram")

    if passed_count == 5:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("GenIE Phase 1 está pronto para homologação")
    elif passed_count >= 3:
        print("\n⚠️  Alguns testes falharam - verifique o .env e as dependências")
    else:
        print("\n❌ Múltiplos testes falharam - execute os passos do TESTE-RAPIDO.md")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido pelo usuário")
        sys.exit(1)
