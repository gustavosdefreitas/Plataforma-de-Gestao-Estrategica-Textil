import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Teste 1: Verificar se a página de Login abre corretamente
def test_read_login():
    response = client.get("/login")
    assert response.status_code == 200
    assert "Login" in response.text

# Teste 2: Verificar se o redirecionamento funciona ao tentar acessar o dashboard sem logar
def test_dashboard_no_auth():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303 # Redirecionamento para login

# Teste 3: Simular o banco de dados (Teste de API)
def test_api_status():
    # Testa se a rota de verificação (se você tiver uma) está ativa
    response = client.get("/login")
    assert response.status_code == 200

# Teste 4: Verificar se a página de empresas (Admin) está protegida
def test_empresas_protection():
    response = client.get("/empresas", follow_redirects=False)
    assert response.status_code == 303