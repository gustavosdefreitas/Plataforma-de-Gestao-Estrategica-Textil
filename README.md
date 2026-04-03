# Plataforma de Gestão Estratégica Têxtil (Estoque Fácil MEI)

Projeto Integrador III - UNIVESP > Uma solução full-stack para transformação digital e controle inteligente de inventário para microempreendedores do setor têxtil e aviamentos.
Este sistema foi desenvolvido para substituir controles manuais (livros físicos) por uma gestão digital centralizada em nuvem. O foco principal é oferecer inteligência de negócio através de dashboards, alertas de estoque baixo e uma arquitetura escalável baseada em APIs.

## Principais Funcionalidades

- **Dashboard Estratégico:** Visualização em tempo real do giro de estoque e métricas de vendas.
- **Gestão de Inventário (CRUD):** Controle detalhado de produtos com atributos específicos (cor, tamanho, fornecedor).
- **Alertas Inteligentes:** Notificações automáticas quando itens atingem o nível crítico de reposição.
- **Arquitetura Multi-tenant:** Suporte para gerenciamento de múltiplas empresas e perfis de acesso (Admin/Operador).
 - **Histórico Auditável:** Registro de movimentações para auxílio na conformidade fiscal (DAS-MEI).


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
