# Plataforma de Gestão Estratégica Têxtil — Estoque Fácil MEI

> Projeto Integrador III — UNIVESP (PJI310)  
> Desenvolvimento de um software com framework web utilizando noções de banco de dados e controle de versão.

Sistema web full-stack para controle de estoque e vendas voltado a microempreendedores do setor têxtil e de aviamentos. Substitui controles manuais (livros físicos) por uma gestão digital centralizada em nuvem, com dashboard analítico, alertas de estoque e relatórios exportáveis.

---

## Funcionalidades

- **Dashboard analítico** — cards de resumo, gráficos de vendas e faturamento por empresa, top 10 produtos mais vendidos, evolução de cadastros por mês e alerta de estoque baixo
- **Gestão de produtos** — CRUD completo com atributos de cor, tamanho e fornecedor; paginação e busca; bloqueio de exclusão de produtos com vendas vinculadas
- **Gestão de fornecedores** — CRUD com paginação e busca por nome, CNPJ e e-mail
- **Controle de vendas** — registro de vendas com múltiplos itens, numeração sequencial (`#000001`...), comprovante em PDF e baixa automática de estoque
- **Gestão de empresas e usuários** — suporte multi-empresa, perfis Admin e Operador
- **Banco de horas** — registro de sessões por usuário com estimativa de horas trabalhadas
- **Relatório em CSV** — exportação de resumo mensal de vendas por empresa
- **API REST** — endpoint `/api/produtos/{empresa_id}` para integração externa
- **Log de auditoria** — registro de todas as ações (login, vendas, cadastros, exclusões)
- **Acessibilidade WCAG 2.1 AA** — skip link, atributos ARIA, labels em formulários, roles em modais e canvas

---

## Requisitos Atendidos — Checklist PJI310

| Requisito | Tecnologia |
|---|---|
| Framework web | FastAPI (Python 3.13) |
| Banco de dados | PostgreSQL + SQLAlchemy 2.x |
| Script web (JS) | Chart.js, máscaras, modais Bootstrap |
| Nuvem | Render.com |
| Controle de versão | Git / GitHub |
| API | `GET /api/produtos/{empresa_id}` |
| Integração Contínua | GitHub Actions (lint + pytest + cobertura) |
| Testes automatizados | Pytest — 43 testes, 51% de cobertura |
| Acessibilidade | WCAG 2.1 AA (ARIA, skip link, roles) |
| Análise de dados | Dashboard com 5 gráficos e exportação CSV |

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
| Testes | Pytest + pytest-cov |
| Lint | Ruff |
| CI | GitHub Actions |
| Deploy | Render.com |

---

## Estrutura do Projeto

```
├── main.py                  # Aplicação principal (rotas, modelos, lógica)
├── database.py              # Configuração do engine SQLAlchemy
├── requirements.txt         # Dependências de produção
├── requirements-dev.txt     # Dependências de desenvolvimento (pytest, ruff)
├── test_main.py             # Suite de testes (43 testes)
├── templates/               # Templates Jinja2
│   ├── base.html
│   ├── dashboard.html
│   ├── produtos.html
│   ├── fornecedores.html
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

1. **Lint** — `ruff check .` verifica estilo e qualidade do código
2. **Testes** — `pytest --cov` roda os 43 testes contra um banco PostgreSQL efêmero

[![CI](https://github.com/gustavosdefreitas/Plataforma-de-Gestao-Estrategica-Textil/actions/workflows/python-app.yaml/badge.svg)](https://github.com/gustavosdefreitas/Plataforma-de-Gestao-Estrategica-Textil/actions/workflows/python-app.yaml)

---

## Deploy

A aplicação está configurada para deploy no [Render.com](https://render.com). As variáveis de ambiente necessárias são:

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | URL de conexão PostgreSQL |
| `SECRET_KEY` | Chave para geração de sessões (opcional) |

---

## Equipe

Desenvolvido por estudantes da UNIVESP como requisito do Projeto Integrador III (PJI310).
