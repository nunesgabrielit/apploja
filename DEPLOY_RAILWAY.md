# Deploy no Railway

Este projeto sobe melhor com dois servicos:

- `backend`: API FastAPI
- `web`: app Next.js unificada com loja e painel em `/admin`

## Backend

- Root Directory: repositorio raiz
- Dockerfile: `Dockerfile`
- Variaveis minimas:
  - `ENVIRONMENT=production`
  - `DEBUG=false`
  - `SECRET_KEY=<valor-forte>`
  - `DB_HOST=<host>`
  - `DB_PORT=<porta>`
  - `DB_NAME=<database>`
  - `DB_USER=<usuario>`
  - `DB_PASSWORD=<senha>`
  - `CORS_ORIGINS=http://localhost:3001,http://localhost:3005,http://localhost:8000`

Observacoes:

- O container executa `alembic upgrade head` automaticamente no start.
- A raiz `/` responde com status amigavel.
- O health check fica em `/api/v1/health`.

## Web

- Root Directory: `storefront`
- Dockerfile: `storefront/Dockerfile`
- Variaveis:
  - `NEXT_PUBLIC_API_BASE_URL=/api/v1`
  - `API_PROXY_TARGET=https://SEU_BACKEND.up.railway.app`

Observacoes:

- A app publica a loja em `/`.
- O painel administrativo fica em `/admin/login`.
- As chamadas para `/api/v1/*` sao encaminhadas para o backend via rewrite do Next.js.

## URLs esperadas

- Loja: `https://SEU_WEB.up.railway.app/`
- Painel: `https://SEU_WEB.up.railway.app/admin/login`
- Docs da API: `https://SEU_BACKEND.up.railway.app/docs`
- Health: `https://SEU_BACKEND.up.railway.app/api/v1/health`
