# Copilot Instructions — Projeto Balm E-commerce (Backend Django)

## Visão Geral do Projeto

Este é o backend de um **e-commerce de velas artesanais** chamado **Balm**, construído com **Django 6.0** e **Django REST Framework 3.16**. O projeto é uma API REST que serve um frontend Next.js hospedado separadamente (Vercel). O backend está hospedado no **Render** em `balm.onrender.com`.

O projeto Django se chama `balm` (definido em `balm/settings.py`).

---

## Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Framework | Django 6.0.1 |
| API | Django REST Framework 3.16 |
| Autenticação | Simple JWT (cookies HttpOnly) + Djoser |
| Banco de Dados | PostgreSQL (via `dj-database-url` + `psycopg2-binary`) |
| Pagamentos | Mercado Pago SDK (`mercadopago`) |
| Frete | Melhor Envio API (sandbox) |
| Storage (prod) | Supabase Storage (custom backend em `balm/storage_backends.py`) |
| Storage (dev) | FileSystemStorage local (`media/`) |
| Arquivos estáticos | WhiteNoise |
| Background Jobs | Inngest (`django-inngest`) — substituiu Celery (legado em `checkout/tasks.py`) |
| Email | Resend (via `django-anymail`) |
| Admin | Jazzmin |
| Rate Limiting | `django-ratelimit` |
| Filtros | `django-filter` |
| CORS | `django-cors-headers` |
| Variáveis de Ambiente | `python-decouple` + `python-dotenv` |

---

## Estrutura de Apps Django

```
balm/                    → Projeto principal (settings, urls, wsgi, storage_backends)
accounts/                → Usuários customizados (CustomUser com email como login) e endereços
apis/                    → App centralizador de todas as APIs REST
  ├── cart_api/           → CRUD do carrinho
  ├── checkout_api/       → Pagamentos (Mercado Pago), frete, cupons, webhook
  ├── clients_api/        → Registro, login (JWT cookies), perfil, endereços, verificação email
  ├── orders_api/         → Criar/listar/detalhar/cancelar pedidos
  ├── products_api/       → Produtos, categorias, essências, bestsellers (ViewSet)
  ├── site_config_api/    → Hero sections do site (banners)
  ├── utils/              → security_logger.py
  ├── decorators.py       → Rate limit decorators por tipo de ação
  └── middleware.py       → RateLimitMiddleware + JWTAuthCookieMiddleware
cart/                    → Models Cart, CartItem, CartItemCustomization
checkout/                → Models Coupon, Shipping, Payment + utils Melhor Envio
clients/                 → App legado (modelos comentados, não utilizado)
inngest_functions/       → Funções Inngest (process_shipping, send_verification_email)
orders/                  → Models Order, OrderItem
products/                → Models Product, Category, Essence, Size, ProductCustomization
site_config/             → Model HeroSection
```

---

## Padrões de Código e Convenções

### Idioma
- **Código** (variáveis, funções, classes): inglês
- **Verbose names nos models**: português brasileiro
- **Mensagens de erro na API**: português brasileiro
- **Logs**: mistura de português e inglês (manter consistência com o existente)
- **Comentários**: português brasileiro

### Models
- Todos os models usam `verbose_name` e `verbose_name_plural` em português
- Choices são definidos como listas de tuplas dentro do model (ex: `STATUS_CHOICES`)
- Slugs são gerados automaticamente no `save()` via `slugify()`
- `BigAutoField` é o campo de ID padrão (`DEFAULT_AUTO_FIELD`)
- Usar `settings.AUTH_USER_MODEL` para referências ao usuário (`accounts.CustomUser`)
- ForeignKey para o usuário sempre usa `on_delete=models.CASCADE` com `related_name`
- Campos monetários: `DecimalField(max_digits=8, decimal_places=2)`
- Datas de criação: `DateTimeField(auto_now_add=True)`

### Serializers
- Usar `ModelSerializer` como padrão
- Imagens são retornadas como URLs absolutas via `SerializerMethodField` + `request.build_absolute_uri()`
- Validações customizadas em métodos `validate_<campo>()` no serializer
- `read_only_fields` para campos que o client não deve alterar
- Padrão de escrita/leitura separados: `write_only=True` para IDs e serializers aninhados para leitura

### Views/APIs
- Usar **Class-Based Views** do DRF (`generics.*`, `viewsets.ModelViewSet`, `APIView`)
- Organização: cada domínio tem sua pasta em `apis/` com `*_api_view.py` e `urls.py`
- Permissões: `IsAuthenticated` para operações de usuário, `IsAdminUser` para admin, `AllowAny`/`IsAuthenticatedOrReadOnly` para endpoints públicos
- Filtragem: `DjangoFilterBackend` + `SearchFilter` + `OrderingFilter`
- Rate limiting via decorators em `apis/decorators.py` com `@method_decorator(decorator, name='dispatch')`
- Respostas de erro seguem o formato: `{"error": "mensagem"}` ou `{"detail": "mensagem"}`
- Operações atômicas com `transaction.atomic()` ao criar pedidos

### Autenticação JWT
- Tokens JWT são enviados via **cookies HttpOnly** (não no body da response)
- `JWTAuthCookieMiddleware` extrai o token do cookie e adiciona ao header `Authorization`
- Access token: 15 minutos / Refresh token: 1 dia
- Rotate refresh tokens habilitado
- Verificação de email obrigatória antes do login

### URL Patterns
- Prefixo base: `/api/`
- Subprefixos: `/api/client/`, `/api/product/`, `/api/cart/`, `/api/order/`, `/api/checkout/`, `/api/site-config/`
- Endpoints de auth: `/api/auth/users/me/`, `/api/auth/jwt/refresh/`
- Inngest: `/api/inngest/`
- Admin Django: `/admin/`

---

## Integrações Externas

### Mercado Pago (Pagamentos)
- SDK: `mercadopago`
- Fluxo: Criar preferência → Redirecionar → Webhook (`/api/checkout/payments/webhook/`)
- Webhook suporta dois formatos: Feed v2.0 (`topic`) e WebHook v1.0 (`type`)
- `external_reference` = ID do pedido
- Ambiente: sandbox (usar `sandbox_init_point`)

### Melhor Envio (Frete)
- API REST com Bearer token
- Endpoint de cotação: `/api/v2/me/shipment/calculate`
- Ambiente: sandbox (`sandbox.melhorenvio.com.br`)
- Serviços: PAC, SEDEX e outros (IDs: 1,2,3,8,13)
- Fluxo completo de etiqueta: cotação → criar carrinho → checkout → gerar → imprimir
- CEP de origem fixo: `93800192` (Sapiranga/RS)
- Retirada na loja disponível para CEPs de Sapiranga e região

### Supabase (Storage em produção)
- Custom storage backend em `balm/storage_backends.py`
- Bucket: `images`
- Sanitização de nomes de arquivo com `slugify()`
- URLs públicas via `get_public_url()`

### Inngest (Background Jobs)
- Client configurado em `ecommerce_inngest.py`
- Funções em `inngest_functions/`:
  - `send-verification-email`: triggered por `auth/send.verification.email`
  - `process-shipping-after-payment`: triggered por `payment/approved`
- Usa `sync_to_async` para chamar código Django síncrono
- Steps para dividir a execução em etapas confiáveis
- Retries: 3 tentativas por padrão
- Eventos disparados via `async_to_sync(inngest_client.send)(inngest.Event(...))`

### Resend (Emails)
- Backend: `anymail.backends.resend.EmailBackend`
- Usado para: verificação de email, reset de senha

---

## Segurança

- **Rate Limiting** granular por tipo de operação (login, registro, pagamento, frete, etc.)
- **Security Logger** (`apis/utils/security_logger.py`) para eventos de segurança
- Logs de segurança em arquivo rotativo (`logs/security.log`)
- Validação de CEP brasileiro (formato, dígitos, sequências inválidas)
- Validação de CPF (algoritmo de dígitos verificadores)
- Validação de propriedade: usuário só acessa seus próprios dados (endereços, pedidos, carrinho)
- CSRF trusted origins configuradas
- Cookies seguros em produção (HttpOnly, Secure, SameSite)
- HSTS, XSS filter, content type nosniff em produção

---

## Variáveis de Ambiente Necessárias

```
SETTINGS_SECRET_KEY
DEBUG
DATABASE_URL
RESEND_API_KEY
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
DEFAULT_FROM_EMAIL
FRONTEND_URL
MERCADOPAGO_ACCESS_TOKEN
FRETE_API_KEY
FRETE_ACCESS_TOKEN
FRETE_REFRESH_TOKEN
ME_CLIENT_ID
ME_CLIENT_SECRET
SUPABASE_URL
SUPABASE_SERVICE_KEY
INNGEST_SIGNING_KEY
INNGEST_EVENT_KEY
CORS_ALLOWED_ORIGINS
CSRF_TRUSTED_ORIGINS
```

---

## Fluxos Principais

### 1. Registro e Verificação de Email
1. `POST /api/client/register/` → cria usuário
2. Evento Inngest `auth/send.verification.email` é disparado
3. Inngest envia email com link de verificação (token válido por 24h)
4. `POST /api/client/verify-email/` com token → marca `email_verified=True`
5. Só após verificação o login é permitido

### 2. Fluxo de Compra
1. Adicionar itens ao carrinho (`POST /api/cart/items/add/`) com produto, essência e personalizações
2. Calcular frete (`POST /api/cart/calculate-shipping/`) com CEP destino
3. Criar pedido (`POST /api/order/order-create/`) com endereço e dados de frete
4. Criar pagamento (`POST /api/checkout/payments/create/`) → retorna URL do Mercado Pago
5. Webhook do MP confirma pagamento → atualiza status do pedido para `paid`
6. Evento Inngest `payment/approved` → gera etiqueta no Melhor Envio → status `shipped`

### 3. Status do Pedido
- Transições válidas: `pending` → `paid` → `shipped` → `delivered`
- Cancelamento: `pending` ou `paid` → `canceled`
- Admin pode atualizar qualquer status via `OrderStatusUpdateView`

---

## Regras de Negócio Importantes

- **Essências** pertencem a **categorias**, não a produtos diretamente. Ao adicionar ao carrinho, validar se a essência é compatível com a categoria do produto.
- **Personalizações** (`ProductCustomization`) são vinculadas a categorias. Podem ter custo extra que é zerado acima de certa quantidade (`free_above_quantity`).
- **Cupons de desconto** têm validade temporal, limite de uso e valor mínimo de compra.
- **Retirada na loja** está disponível apenas para CEPs da região de Sapiranga/RS.
- Ao criar um pedido, o carrinho é esvaziado e os dados de personalização são "fotografados" (snapshot) no `OrderItem.customization_details` (JSONField).

---

## Comandos Úteis

```bash
# Rodar servidor de desenvolvimento
python manage.py runserver

# Migrações
python manage.py makemigrations
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic

# Rodar com Gunicorn (produção)
gunicorn balm.wsgi:application
```

---

## Ao Gerar Código Novo

1. **Siga os padrões existentes** — CBVs do DRF, serializers com validação, rate limiting.
2. **Use português** para verbose_name, mensagens de erro e comentários.
3. **Sempre valide propriedade** — usuários só acessam/modificam seus próprios dados.
4. **Log de segurança** para ações sensíveis via `log_security_event()`.
5. **Operações complexas** devem usar `transaction.atomic()`.
6. **Novos endpoints** devem ter rate limiting apropriado (veja `apis/decorators.py`).
7. **Imagens** devem ser retornadas como URLs absolutas (`request.build_absolute_uri()`).
8. **Background jobs** devem usar Inngest (não Celery — o Celery em `checkout/tasks.py` é legado).
9. **Testes** devem ser escritos nos arquivos `tests.py` de cada app.
10. **Use `settings.AUTH_USER_MODEL`** ao referenciar o modelo de usuário, nunca `User` diretamente.
