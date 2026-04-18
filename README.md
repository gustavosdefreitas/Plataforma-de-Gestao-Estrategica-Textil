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

🌐 **[Acesse o sistema em produção](https://plataforma-de-gestao-estrategica-textil.onrender.com)** — login: `admin` / `123456`

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

## Requisitos Atendidos — Checklist PJI310

| Requisito | Tecnologia / Evidência |
|---|---|
| Framework web | FastAPI (Python 3.13) |
| Banco de dados | PostgreSQL + SQLAlchemy 2.x |
| Script web (JS) | Chart.js, máscaras, validação CPF, modais Bootstrap |
| Nuvem | Render.com |
| Controle de versão | Git / GitHub |
| API | `GET /api/produtos/{empresa_id}` |
| Integração Contínua | GitHub Actions (lint ruff + pytest + cobertura) |
| Testes automatizados | Pytest — **55 testes, 47% de cobertura** |
| Acessibilidade | WCAG 2.1 AA (ARIA, skip link, roles, contraste AA) |
| Análise de dados | Dashboard com 5 gráficos e exportação CSV |
| Integração externa | BrasilAPI — consulta CNPJ com situação cadastral Receita Federal |

> 📋 [Issue #1 — Evidência formal de qualidade (CI, testes, cobertura, acessibilidade)](https://github.com/gustavosdefreitas/Plataforma-de-Gestao-Estrategica-Textil/issues/1)

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
