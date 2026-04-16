# WM Distribuidora Backend

Backend profissional para o sistema de e-commerce da WM Distribuidora, construido com FastAPI, PostgreSQL, SQLAlchemy 2.0, Alembic, JWT e Docker.

## Stack

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0
- Alembic
- Pydantic v2
- JWT Auth
- Docker

## Fases implementadas

### Fase 1

- autenticacao JWT
- cadastro e login de usuarios
- modelo `User`
- configuracao via `.env`
- conexao assincrona com PostgreSQL
- logging e tratamento global de erros

### Fase 2

- catalogo com `Category`, `Product` e `ProductItem`
- endpoints publicos para consulta de categorias, produtos e itens vendaveis
- endpoints administrativos para criacao, atualizacao, desativacao, ajuste de estoque e atualizacao de preco
- filtros, paginacao e auditoria administrativa basica por log

### Fase 3

- carrinho autenticado por usuario customer
- criacao automatica de carrinho ativo ao consultar ou adicionar item
- itens de carrinho baseados em `ProductItem`
- operacoes de obter carrinho, adicionar item, atualizar quantidade e remover item
- subtotal e total de itens calculados na resposta

### Fase 4

- regras administrativas de frete por faixa de CEP
- calculo publico de frete por CEP normalizado
- suporte a `pickup` com frete zero
- retorno de prazo estimado e regra aplicada

### Fase 5

- criacao de pedidos a partir do carrinho ativo do cliente
- snapshots dos itens comprados em `OrderItem`
- suporte a `pickup` e `delivery`
- calculo de subtotal, frete, desconto e total
- listagem de pedidos do proprio cliente e listagem administrativa
- atribuicao opcional de responsavel interno

### Fase 6

- pagamentos via Mercado Pago com PIX e cartao
- webhook publico para confirmacao de pagamento
- atualizacao automatica de pedido apos confirmacao
- baixa de estoque na aprovacao
- protecao contra duplicidade de webhook e dupla baixa de estoque

## Estrutura

```text
app/
  api/
  core/
  models/
  repositories/
  schemas/
  services/
  utils/
  main.py
alembic/
tests/
docker-compose.yml
Dockerfile
pyproject.toml
README.md
```

## Configuracao

1. Copie `.env.example` para `.env` se quiser recriar o arquivo.
2. Ajuste `SECRET_KEY` antes de qualquer uso fora de desenvolvimento.
3. Para rodar localmente, mantenha `DB_HOST=localhost`.
4. No Docker Compose, o host do banco e sobrescrito para `postgres`.

## Rodando com Docker

```bash
docker compose up --build
```

Aplicacao:

- API: [http://localhost:8000](http://localhost:8000)
- Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Rodando localmente

1. Crie um ambiente virtual.
2. Instale as dependencias da aplicacao:

```bash
pip install -e .
```

3. Para desenvolvimento e testes:

```bash
pip install -e .[dev]
```

4. Configure as variaveis do Mercado Pago se for usar a fase de pagamentos:

```env
MERCADOPAGO_ACCESS_TOKEN=APP_USR-...
MERCADOPAGO_WEBHOOK_SECRET=seu-segredo-do-webhook
MERCADOPAGO_NOTIFICATION_URL=https://seu-dominio/api/v1/payments/mercadopago/webhook
```

5. Suba o PostgreSQL localmente ou via Docker.
6. Rode as migrations:

```bash
alembic upgrade head
```

7. Inicie a aplicacao:

```bash
uvicorn app.main:app --reload
```

## Testes

```bash
pytest
```

## Migrations

Criar uma nova migration:

```bash
alembic revision --autogenerate -m "descricao_da_migration"
```

Aplicar migrations:

```bash
alembic upgrade head
```

## Autenticacao

### Registro de cliente

`POST /api/v1/auth/register`

```json
{
  "name": "Cliente Teste",
  "email": "cliente@exemplo.com",
  "phone": "69999999999",
  "password": "SenhaForte123"
}
```

### Login

`POST /api/v1/auth/login`

O endpoint segue o fluxo `OAuth2PasswordRequestForm`:

- `username`: email do usuario
- `password`: senha do usuario

### Usuario autenticado

`GET /api/v1/auth/me`

Envie o token Bearer no header `Authorization`.

## Catalogo: Product vs ProductItem

Na WM Distribuidora, o catalogo separa o agrupador comercial do item real vendido:

- `Category`: categoria comercial, como `Carregadores`
- `Product`: agrupador comercial, como `Carregadores Motorola`
- `ProductItem`: item vendavel real com codigo, SKU, estoque e preco

Exemplo:

- `Category`: Carregadores
- `Product`: Carregadores Motorola
- `ProductItem`: Carregador MOTOROLA 16X Turbo, `internal_code=CA007`, `sku=WM-CA007`

## Endpoints publicos

### Carrinho autenticado

- `GET /api/v1/cart`
- `POST /api/v1/cart/items`
- `PUT /api/v1/cart/items/{id}`
- `DELETE /api/v1/cart/items/{id}`

O carrinho exige autenticacao e usa `ProductItem`, nunca `Product`.
Nesta fase, o carrinho nao reserva nem baixa estoque.

### Frete

- `POST /api/v1/shipping/calculate`

O modulo de frete usa faixa de CEP normalizada.
O CEP informado pode conter hifen e espacos, mas sera salvo e comparado apenas com 8 digitos numericos.
Se `fulfillment_type=pickup`, o retorno sera frete `0.00` com regra `Retirada na loja`.

### Pedidos autenticados

- `POST /api/v1/orders`
- `GET /api/v1/orders/me`
- `GET /api/v1/orders/me/{id}`

O pedido nasce a partir do carrinho ativo do cliente autenticado.
O pedido usa snapshots do `ProductItem`.
Na Fase 6, o estoque e baixado apenas quando o pagamento e aprovado.
Para `delivery`, o payload deve referenciar um `address_id` ja persistido do cliente.

### Pagamentos autenticados

- `POST /api/v1/payments/mercadopago/pix`
- `POST /api/v1/payments/mercadopago/card`

O pagamento sempre referencia um pedido do proprio cliente.
Somente pedidos em `waiting_payment` podem receber nova cobranca.
O webhook do Mercado Pago fica em `POST /api/v1/payments/mercadopago/webhook`.

### Categorias

- `GET /api/v1/categories`

### Produtos

- `GET /api/v1/products`
- `GET /api/v1/products/{id}`

Filtros suportados em `GET /api/v1/products`:

- `category_id`
- `brand`
- `search`
- `page`
- `page_size`

### Itens vendaveis

- `GET /api/v1/product-items`
- `GET /api/v1/product-items/{id}`

Filtros suportados em `GET /api/v1/product-items`:

- `product_id`
- `category_id`
- `brand`
- `internal_code`
- `sku`
- `search`
- `low_stock`
- `page`
- `page_size`

## Endpoints administrativos

### Categorias

- `POST /api/v1/admin/categories`
- `PUT /api/v1/admin/categories/{id}`
- `DELETE /api/v1/admin/categories/{id}`

### Produtos

- `POST /api/v1/admin/products`
- `PUT /api/v1/admin/products/{id}`
- `DELETE /api/v1/admin/products/{id}`

### Itens vendaveis

- `POST /api/v1/admin/product-items`
- `PUT /api/v1/admin/product-items/{id}`
- `PATCH /api/v1/admin/product-items/{id}/stock`
- `PATCH /api/v1/admin/product-items/{id}/price`
- `DELETE /api/v1/admin/product-items/{id}`

### Regras de frete

- `GET /api/v1/admin/shipping-rules`
- `POST /api/v1/admin/shipping-rules`
- `PUT /api/v1/admin/shipping-rules/{id}`
- `DELETE /api/v1/admin/shipping-rules/{id}`

### Pedidos

- `GET /api/v1/admin/orders`
- `GET /api/v1/admin/orders/{id}`
- `PATCH /api/v1/admin/orders/{id}/assign-employee`

Os endpoints administrativos usam a politica ja existente de `employee` ou `admin`.

## Exemplos de payload

### Criar categoria

```json
{
  "name": "Carregadores",
  "description": "Linha de carregadores e fontes"
}
```

### Criar produto

```json
{
  "category_id": "UUID_DA_CATEGORIA",
  "name_base": "Carregadores Motorola",
  "brand": "Motorola",
  "description": "Linha de carregadores turbo Motorola",
  "image_url": "https://cdn.exemplo.com/produtos/motorola.png"
}
```

### Criar item vendavel

```json
{
  "product_id": "UUID_DO_PRODUTO",
  "internal_code": "CA007",
  "sku": "WM-CA007",
  "name": "Carregador MOTOROLA 16X Turbo",
  "connector_type": "Tipo C",
  "power": "45W",
  "voltage": "220V",
  "short_description": "carregador turbo motorola tipo c",
  "price": "79.90",
  "stock_current": 20,
  "stock_minimum": 5
}
```

### Ajustar estoque

```json
{
  "quantity": 3,
  "operation": "increment",
  "reason": "entrada manual"
}
```

### Atualizar preco

```json
{
  "price": "89.90"
}
```

### Adicionar item ao carrinho

```json
{
  "product_item_id": "UUID_DO_PRODUCT_ITEM",
  "quantity": 2
}
```

### Atualizar quantidade do item do carrinho

```json
{
  "quantity": 3
}
```

### Criar regra de frete

```json
{
  "zip_code_start": "69900-000",
  "zip_code_end": "69900-999",
  "rule_name": "Centro Rio Branco",
  "shipping_price": "19.90",
  "estimated_time_text": "2 dias uteis"
}
```

### Calcular frete para entrega

```json
{
  "zip_code": "69900-050",
  "fulfillment_type": "delivery"
}
```

### Calcular frete para retirada

```json
{
  "zip_code": "69900-050",
  "fulfillment_type": "pickup"
}
```

### Criar pedido para retirada

```json
{
  "fulfillment_type": "pickup",
  "notes": "retirar no balcao"
}
```

### Criar pedido para entrega

```json
{
  "fulfillment_type": "delivery",
  "address_id": "UUID_DO_ENDERECO",
  "notes": "entregar no horario comercial"
}
```

### Atribuir funcionario ao pedido

```json
{
  "assigned_employee_id": "UUID_DO_FUNCIONARIO"
}
```

### Criar pagamento PIX

```json
{
  "order_id": "UUID_DO_PEDIDO"
}
```

### Criar pagamento cartao

```json
{
  "order_id": "UUID_DO_PEDIDO",
  "card_token": "TOKEN_DO_CARTAO",
  "installments": 1,
  "payment_method_id": "visa"
}
```

### Exemplo de webhook Mercado Pago

```json
{
  "id": "123456789",
  "type": "payment",
  "data": {
    "id": "987654321"
  }
}
```

## Regras de negocio atuais

- `ProductItem` representa o item real vendido
- o carrinho referencia `ProductItem`, nunca `Product`
- cada customer pode ter apenas um carrinho ativo
- o carrinho cria automaticamente um carrinho ativo quando necessario
- itens repetidos no carrinho sao consolidados na mesma linha
- o carrinho captura `unit_price` no momento da adicao do item
- nesta fase o carrinho nao reserva nem baixa estoque
- o frete por entrega usa faixas inclusivas de CEP normalizado
- o calculo de frete compara CEPs com exatamente 8 digitos apos normalizacao
- `pickup` retorna frete zero e prazo `Retirada na loja`
- o pedido nasce do carrinho ativo do cliente autenticado
- `pickup` ignora `address_id` e usa frete zero
- `delivery` exige `address_id` valido do proprio cliente e calcula frete pelo modulo de CEP
- o pedido copia snapshots dos itens comprados e usa o `unit_price` capturado no carrinho
- apos criar o pedido, o carrinho atual e marcado como `converted`
- o pedido valida estoque na criacao e o estoque e baixado na aprovacao do pagamento
- o pagamento via Mercado Pago exige pedido em `waiting_payment`
- o valor da cobranca deve coincidir com o `total` do pedido
- webhook duplicado nao reaplica mudanca de status nem baixa estoque
- quando o pagamento e aprovado, o pedido vai para `paid` e o estoque e baixado
- se o pagamento for rejeitado ou cancelado, o pedido permanece apto a nova tentativa
- o payload de cartao inclui `payment_method_id` porque a API oficial do Mercado Pago exige esse campo
- `price` deve ser maior que zero
- `stock_current` nao pode ser negativo
- `stock_minimum` nao pode ser negativo
- `low_stock` e considerado quando `stock_current <= stock_minimum`
- remocoes administrativas usam desativacao por `is_active`
- acoes administrativas relevantes sao registradas por auditoria basica em log

## Perfis previstos

- `admin`
- `employee`
- `customer`

## Proximos passos recomendados

- CRUD de enderecos para clientes
- conciliacao e reembolso de pagamentos
- historico de status de pedido e pagamento
- observabilidade e monitoramento
- CI/CD e ambientes separados
#   a p p l o j a  
 #   a p p l o j a  
 