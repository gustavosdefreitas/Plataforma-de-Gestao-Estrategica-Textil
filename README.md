# Plataforma de Gestão Estratégica Têxtil — Estoque Fácil MEI

> **Projeto Integrador III — UNIVESP (PJI310)**
> Desenvolvimento de um software com framework web utilizando noções de banco de dados e controle de versão.

[![CI](https://github.com/gustavosdefreitas/Plataforma-de-Gestao-Estrategica-Textil/actions/workflows/python-app.yaml/badge.svg)](https://github.com/gustavosdefreitas/Plataforma-de-Gestao-Estrategica-Textil/actions/workflows/python-app.yaml)
![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Testes](https://img.shields.io/badge/testes-55%20passando-brightgreen)
![Cobertura](https://img.shields.io/badge/cobertura-47%25-yellow)

Sistema web full-stack para controle de estoque e vendas voltado a microempreendedores do setor têxtil e de aviamentos. Substitui controles manuais (livros físicos) por uma gestão digital centralizada em nuvem, com dashboard analítico, alertas de estoque, consulta automática de CNPJ na Receita Federal e relatórios exportáveis em PDF.

🌐 **[Acesse o sistema em produção](https://plataforma-de-gestao-estrategica-textil.onrender.com)** — login: `univesp_admin` / `univesp_admin`

---

## Funcionalidades

- **Dashboard analítico** — cards de resumo, gráficos de vendas e faturamento por empresa, top 10 produtos mais vendidos, evolução de cadastros por mês e alerta de estoque baixo
- **Gestão de produtos** — CRUD completo com atributos de cor, tamanho e fornecedor; paginação e busca; bloqueio de exclusão de produtos com vendas vinculadas
- **Gestão de fornecedores** — CRUD com paginação e busca; consulta automática de CNPJ via BrasilAPI com preenchimento de campos e exibição de situação cadastral (Receita Federal)
- **Gestão de empresas** — multi-empresa com consulta de CNPJ, situação cadastral em tempo real e badge colorido (ATIVA / INAPTA / SUSPENSA / BAIXADA)
- **Cadastro de usuários** — perfis Admin e Operador, campos nome completo e CPF com validação dos dígitos verificadores no frontend
- **Controle de vendas** — registro com múltiplos itens, numeração sequencial (`#000001`...), comprovante em PDF e baixa automática de estoque
- **Banco de horas** — registro de sessões por usuário com cálculo de tempo por data e total geral; relatório exportável em PDF com nome completo e CPF
- **Relatório em CSV** — exportação de resumo mensal de vendas por empresa
- **API REST** — endpoint `/api/produtos/{empresa_id}` para integração externa
- **Log de auditoria** — registro de todas as ações (login, vendas, cadastros, exclusões)
- **Acessibilidade WCAG 2.1 AA** — skip link, atributos ARIA, labels em formulários, roles em modais e canvas

---

## Requisitos Atendidos — PJI310

| Requisito | Tecnologia / Evidência |
|---|---|
| Framework web | FastAPI (Python 3.13) |
| Banco de dados | PostgreSQL + SQLAlchemy 2.x |
| Script web (JS) | Chart.js, máscaras, validação CPF, modais Bootstrap |
| Nuvem | Render.com — deploy automático via CI/CD |
| Controle de versão | Git / GitHub — histórico com mensagens convencionais |
| API REST | `GET /api/produtos/{empresa_id}` — JSON autenticado |
| Integração Contínua | GitHub Actions — lint + testes + cobertura a cada push |
| Testes automatizados | Pytest — **55 testes, 47% de cobertura** |
| Acessibilidade | WCAG 2.1 AA — ARIA completo em todos os templates |
| Análise de dados | Dashboard com 5 gráficos (Chart.js) e exportação CSV |
| Integração externa | BrasilAPI — CNPJ com situação cadastral Receita Federal |

> 📋 [Issue #1 — Evidência formal de qualidade (CI, testes, cobertura, acessibilidade)](https://github.com/gustavosdefreitas/Plataforma-de-Gestao-Estrategica-Textil/issues/1)

---

## CI/CD — Integração e Entrega Contínua

O pipeline é definido em `.github/workflows/python-app.yaml` e executa automaticamente em todo push ou pull request para o branch `main`. É composto por dois jobs sequenciais — o job de testes só inicia se o lint passar.

```
push → main
  └─ [1] Lint (ruff)          → verifica estilo PEP 8 e erros lógicos
        └─ [2] Testes (pytest) → roda 55 testes contra PostgreSQL 16 efêmero
              └─ Artefato: coverage.xml (retido 30 dias)
              └─ Deploy automático: Render.com detecta o push e reimplanta
```

**Job 1 — Lint**
```bash
ruff check . --select E,F,W --ignore E501
# E = erros PEP 8 | F = erros lógicos (imports, variáveis) | W = avisos
```

**Job 2 — Testes + cobertura** (depende do Job 1)
```bash
pytest test_main.py -v \
  --cov=main \
  --cov-report=term-missing \
  --cov-report=xml \
  --tb=short
```
O banco de testes é um PostgreSQL 16 efêmero provisionado pelo próprio Actions (`services.postgres`), garantindo isolamento total do ambiente de produção.

[![CI](https://github.com/gustavosdefreitas/Plataforma-de-Gestao-Estrategica-Textil/actions/workflows/python-app.yaml/badge.svg)](https://github.com/gustavosdefreitas/Plataforma-de-Gestao-Estrategica-Textil/actions/workflows/python-app.yaml)

---

## Testes Automatizados e Cobertura

**55 testes — todos passando** | Cobertura: **47% de `main.py`**

A suite está em `test_main.py` e usa `pytest` com `TestClient` do FastAPI. Cada teste opera contra um banco PostgreSQL isolado, com limpeza via `TRUNCATE … RESTART IDENTITY CASCADE` antes de cada caso.

```bash
# Executar localmente
export DATABASE_URL="postgresql://usuario:senha@localhost:5432/test_db"
pip install -r requirements-dev.txt
pytest test_main.py -v --cov=main --cov-report=term-missing
```

| Módulo de teste | Casos | O que cobre |
|---|---|---|
| `TestAutenticacao` | 5 | Login, logout, senha errada, usuário inexistente, cookie de sessão |
| `TestProtecaoRotas` | 9 | Redirecionamento para `/login` sem sessão em todas as rotas protegidas |
| `TestEmpresas` | 3 | Criar, listar, deletar empresa |
| `TestFornecedores` | 5 | Criar, editar, listar, buscar, deletar fornecedor |
| `TestSituacaoCadastralEmpresas` | 6 | Persistência de `situacao_cadastral`, normalização maiúsculo, exibição de badge |
| `TestSituacaoCadastralFornecedores` | 6 | Idem para fornecedores |
| `TestProdutos` | 7 | CRUD completo; bloqueio de deleção com vendas vinculadas |
| `TestVendas` | 3 | Registrar venda, baixa de estoque, proteção sem auth |
| `TestAPI` | 3 | `/api/produtos/{id}` autenticado, não autenticado, empresa inexistente |
| `TestRestricaoPerfil` | 4 | Restrição de `/logs` e `/banco-horas` para perfil `admin` |
| `TestDashboard` | 2 | Renderização do dashboard e cards de resumo |
| **Total** | **55** | |

---

## Acessibilidade — WCAG 2.1 AA

Todos os 14 templates HTML foram auditados e corrigidos para atender ao nível AA da WCAG 2.1.

**Navegação e estrutura**
- `<html lang="pt-BR">` — idioma declarado no documento
- Skip link `<a href="#conteudo-principal" class="visually-hidden-focusable">Pular para o conteúdo principal</a>` em `base.html`
- `<main id="conteudo-principal" role="main">` — landmark de conteúdo principal
- `<nav aria-label="Navegação principal">` na barra de navegação

**Formulários**
- Todo `<input>`, `<select>` e `<textarea>` tem `<label for="...">` associado
- Campos obrigatórios marcados com `required` + `aria-required="true"`
- Campos de busca com `role="search"` + `aria-label` no `<form>`
- Todos os formulários de ação com `aria-label` descritivo
- `autocomplete` nos campos de login (`username`, `current-password`)

**Modais e interação**
- Todos os modais Bootstrap com `role="dialog"`, `aria-modal="true"` e `aria-labelledby`
- Botões de fechar com `aria-label="Fechar"`
- Botões de ação nas tabelas (editar/excluir) com `aria-label="Editar [nome]"` / `aria-label="Excluir [nome]"`

**Feedback dinâmico**
- Status de consulta CNPJ com `role="status"` e `aria-live="polite"`
- Mensagens de erro com `role="alert"` e `aria-live="assertive"`
- Toast de flash messages com `aria-live="polite"` e `aria-atomic="true"`

**Tabelas e gráficos**
- `<caption class="visually-hidden">` em todas as tabelas de dados
- `scope="col"` em todos os cabeçalhos de tabela `<th>`
- Canvas Chart.js com `role="img"` e `aria-label` descritivo em todos os gráficos
- Ícones Font Awesome decorativos com `aria-hidden="true"`

**Paginação**
- `<nav aria-label="Paginação de ...">` em todas as páginas com paginação
- Página ativa com `aria-current="page"`
- Links de anterior/próxima com `aria-label` explícito

---

## API REST

**Endpoint:** `GET /api/produtos/{empresa_id}`

Retorna o estoque de produtos de uma empresa em formato JSON. Requer sessão autenticada (cookie `session_id`).

**Autenticação**
```
Cookie: session_id=<hash>
```
Sem autenticação retorna `401 Unauthorized`:
```json
{ "erro": "Não autenticado" }
```

**Resposta com sucesso (`200 OK`)**
```json
{
  "empresa_id": 1,
  "estoque": [
    { "nome": "Camiseta Branca M", "quantidade": 42.0, "preco": 29.90 },
    { "nome": "Calça Jeans 40",    "quantidade": 15.0, "preco": 89.90 }
  ]
}
```

**Exemplo com curl**
```bash
curl -b "session_id=SEU_TOKEN" \
  https://plataforma-de-gestao-estrategica-textil.onrender.com/api/produtos/1
```

---

## Deploy — Render.com

A aplicação está hospedada no [Render.com](https://render.com) com deploy automático ativado no branch `main`. A cada push que passa no CI, o Render detecta a mudança e reimplanta automaticamente.

| Componente | Configuração |
|---|---|
| Plataforma | Render.com (Web Service) |
| Runtime | Python 3.13 |
| Comando de start | `uvicorn main:app --host 0.0.0.0 --port 10000` |
| Banco de dados | PostgreSQL 16 (Render Managed Database) |
| Branch monitorado | `main` |
| Deploy automático | Ativado — a cada push no `main` |

**Variável de ambiente obrigatória**

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | URL de conexão PostgreSQL (`postgresql://...`) |

🌐 **URL de produção:** https://plataforma-de-gestao-estrategica-textil.onrender.com

---

## Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.13 |
| Framework web | FastAPI + Uvicorn |
| Templates | Jinja2 |
| Banco de dados | PostgreSQL |
| ORM | SQLAlchemy 2.x |
| Frontend | Bootstrap 5 + Chart.js |
| Geração de PDF | ReportLab |
| Consulta CNPJ | BrasilAPI |
| Testes | Pytest + pytest-cov |
| Lint | Ruff |
| CI | GitHub Actions |
| Deploy | Render.com |

---

## Estrutura do Projeto

```
├── main.py                  # Aplicação principal (rotas, modelos, lógica)
├── requirements.txt         # Dependências de produção
├── requirements-dev.txt     # Dependências de desenvolvimento (pytest, ruff)
├── test_main.py             # Suite de testes (55 testes)
├── templates/               # Templates Jinja2
│   ├── base.html
│   ├── dashboard.html
│   ├── produtos.html
│   ├── fornecedores.html
│   ├── empresas.html
│   ├── editar_empresa.html
│   ├── usuarios.html
│   ├── vendas.html
│   ├── banco_horas.html
│   └── ...
└── .github/
    └── workflows/
        └── python-app.yaml  # CI: lint (ruff) + testes (pytest --cov)
```

---

## Como Executar Localmente

### Pré-requisitos

- Python 3.13+
- PostgreSQL rodando localmente

### Configuração

```bash
# Clone o repositório
git clone https://github.com/gustavosdefreitas/Plataforma-de-Gestao-Estrategica-Textil.git
cd Plataforma-de-Gestao-Estrategica-Textil

# Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Configure a variável de ambiente
export DATABASE_URL="postgresql://usuario:senha@localhost:5432/nome_do_banco"

# Inicie o servidor
uvicorn main:app --reload
```

Acesse em `http://localhost:8000`. Login padrão: `admin` / `123456`.

---

## Como Executar os Testes

```bash
# Instale as dependências de desenvolvimento
pip install -r requirements-dev.txt

# Configure o banco de testes
export DATABASE_URL="postgresql://usuario:senha@localhost:5432/test_db"

# Execute os testes com cobertura
pytest test_main.py -v --cov=main --cov-report=term-missing
```

---

## Integração Contínua

O workflow `.github/workflows/python-app.yaml` executa automaticamente a cada push em `main`:

1. **Lint** — `ruff check . --select E,F,W --ignore E501` verifica estilo e qualidade do código
2. **Testes** — `pytest test_main.py -v --cov=main --cov-report=xml` roda os **55 testes** contra um banco PostgreSQL efêmero

[![CI](https://github.com/gustavosdefreitas/Plataforma-de-Gestao-Estrategica-Textil/actions/workflows/python-app.yaml/badge.svg)](https://github.com/gustavosdefreitas/Plataforma-de-Gestao-Estrategica-Textil/actions/workflows/python-app.yaml)

---

## Deploy

A aplicação está hospedada no [Render.com](https://render.com) com deploy automático a partir do branch `main`.

| Variável de ambiente | Descrição |
|---|---|
| `DATABASE_URL` | URL de conexão PostgreSQL |

---

## Equipe

Desenvolvido por estudantes da UNIVESP como requisito do **Projeto Integrador III (PJI310)** — Bacharelado em Tecnologia da Informação e Engenharia da Computação.

| Nome | 
|------|
| Allan Christopher Furtunato Silva |
| Cristiane Aureliano da Silva Maia |
| Gustavo Silva de Freitas |
| Gustavo Teixeira Grottone |
| Jorge Luis Sá Guerra |
| Rafael Henrique da Silva |
| Vinicius Figueiredo Dias Nunes |

**Tutor:** Renann de Faria Brandão
**Polos:** Itanhaém · Praia Grande · Santos — SP
