# WM Distribuidora - Backend API

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red?style=for-the-badge)](https://www.sqlalchemy.org/)

Backend profissional e escalável para o ecossistema de e-commerce da **WM Distribuidora**. Desenvolvido com foco em alta performance, processos assíncronos e uma arquitetura robusta para gestão de catálogo, logística e pagamentos.

---

## 🛠️ Tech Stack

* **Linguagem:** Python 3.12
* **Framework:** FastAPI
* **Banco de Dados:** PostgreSQL (Conexão Assíncrona)
* **ORM:** SQLAlchemy 2.0
* **Migrações:** Alembic
* **Validação:** Pydantic v2
* **Segurança:** JWT Authentication
* **Containerização:** Docker & Docker Compose
* **Integração Financeira:** Mercado Pago SDK

---

## 🚀 Roadmap de Desenvolvimento

O projeto foi estruturado em fases incrementais, garantindo a integridade de cada módulo:

### Fase 1: Fundação & Auth
* Autenticação JWT, segurança de senhas e modelos de usuário.
* Tratamento global de erros e logging estruturado.

### Fase 2: Gestão de Catálogo (Product vs ProductItem)
* Implementação de hierarquia: **Categoria** > **Produto** (Agrupador) > **Item** (Unidade Vendável).
* Endpoints administrativos para controle de estoque, SKU e preços.

### Fase 3: Checkout Dinâmico
* Carrinho persistente por usuário com criação automática.
* Cálculo em tempo real de subtotais e consolidação de itens repetidos.

### Fase 4: Inteligência Logística
* Cálculo de frete baseado em faixas de CEP normalizadas (8 dígitos).
* Suporte a modalidades de entrega (`delivery`) e retirada (`pickup`).

### Fase 5: Ciclo de Vida do Pedido
* Conversão de carrinho em pedido com snapshots de preços (segurança financeira).
* Atribuição de funcionários responsáveis e rastreio de status.

### Fase 6: Integração de Pagamentos
* Fluxo de pagamento via PIX e Cartão com Mercado Pago.
* Webhook resiliente para confirmação de pagamento e baixa atômica de estoque.

---

## 🏗️ Estrutura do Projeto

```text
app/
  ├── api/          # Rotas e controladores (v1)
  ├── core/         # Configurações, segurança e constantes
  ├── models/       # Entidades do banco de dados (SQLAlchemy)
  ├── repositories/ # Camada de acesso a dados
  ├── schemas/      # Modelos de entrada/saída (Pydantic)
  ├── services/     # Regras de negócio e integrações
  └── main.py       # Ponto de entrada da aplicação
alembic/            # Scripts de migração de banco
tests/              # Testes automatizados (Pytest)
Configuração e Execução
Via Docker (Recomendado)
Bash
docker compose up --build
API: http://localhost:8000

Docs (Swagger): http://localhost:8000/docs

Instalação Local
Ambiente:

Bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
Banco de Dados:

Bash
# Rodar migrations
alembic upgrade head
Execução:

Bash
uvicorn app.main:app --reload
⚖️ Regras de Negócio Principais
Integridade Financeira: O carrinho captura o unit_price no momento da adição para evitar flutuações durante o checkout.

Gestão de Estoque: A baixa de estoque ocorre de forma atômica apenas após a confirmação do pagamento (paid) via webhook.

Normalização de Frete: CEPs são tratados como strings de 8 dígitos numéricos, ignorando hifens ou espaços.

Idempotência: O sistema protege o banco contra processamentos duplicados de webhooks de pagamento.

👥 Perfis de Sistema
Admin: Gestão total de categorias, funcionários e regras de frete.

Employee: Operação de estoque e acompanhamento de pedidos.

Customer: Experiência de compra, gestão de carrinho e histórico pessoal.

🧪 Testes
Bash
pytest
Desenvolvido por Gabriel Souza Nunes
Graduando em Sistemas para Internet | Advogado