# Sistema de Controle de Estoque Multi-Empresa 📦

Projeto desenvolvido para a disciplina de Projeto Integrador da **Univesp**. O sistema permite o gerenciamento de estoque, vendas, fornecedores e usuários para múltiplas empresas em uma única interface.

## 🚀 Requisitos Atendidos (Checklist Univesp)

- **Framework Web:** Desenvolvido com **FastAPI** (Python).
- **Banco de Dados:** Utilização de **SQLite** com relacionamentos entre Empresas e Produtos.
- **Script Web (JS):** Implementação de gráficos dinâmicos utilizando a biblioteca **Chart.js**.
- **Nuvem:** Preparado para deploy em plataformas como Render/Railway.
- **Acessibilidade:** Uso de tags semânticas HTML5, atributos ARIA e cores de alto contraste via Bootstrap 5.
- **Controle de Versão:** Repositório gerenciado via **Git/GitHub**.
- **Integração Contínua (CI):** Workflow configurado via **GitHub Actions** para automação de testes.
- **Testes Unitários:** Suite de testes automatizados utilizando **Pytest**.
- **Análise de Dados:** Dashboard com indicadores de performance e gráfico de distribuição de estoque.
- **API:** Endpoint disponível em `/api/produtos/{id}` para fornecimento de dados.

## 🛠️ Tecnologias Utilizadas

* Python 3.14
* FastAPI & Uvicorn
* Jinja2 (Templates)
* SQLite
* Bootstrap 5 & Chart.js

## 📉 Como rodar os testes
Para validar a integridade do código, execute:
```bash
python -m pytest