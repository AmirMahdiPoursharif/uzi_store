# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Django 5.2 + DRF e-commerce backend (API-only; the HTML templates are test pages). PostgreSQL 17, Redis, Celery. All Python lives under `src/`; `doc/ARCHITECTURE.md` is a detailed Persian walkthrough of every model, endpoint, and known defect — read it before any non-trivial change.

## Commands

Everything runs through Docker Compose. **`compose.override.yaml` is auto-loaded by `docker compose`**, so the bare command already gives you the dev stack (`Dockerfile.dev`, `runserver` with auto-reload, `DEBUG=True`, `./src` bind-mounted, including templates).

```sh
docker compose up --build -d          # dev stack (override applies automatically)
docker compose logs -f web
docker compose down                   # keeps volumes; -v also drops the PG data
```

To run the production-shaped stack (Gunicorn, no source mount), opt out of the override explicitly:

```sh
docker compose -f compose.yaml up --build -d
```

Management commands and tests:

```sh
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py migrate
docker compose exec web python manage.py test accounts dashboard product cart
docker compose exec web python manage.py test product.tests.FallbackCacheTests
docker compose exec web python manage.py test product.tests.CacheSignalsTests.test_cache_version_increments_on_product_save
```

Working dir inside the container is `/app/src`, so `manage.py` is on the path. Restart `worker` and `beat` after editing task code — the dev override only auto-reloads `web`.

Note: `README.md` tells you to pass `-f compose.yaml -f compose.dev.yaml`. **That file does not exist** — it was renamed to `compose.override.yaml`. Drop the `-f` flags entirely. The README is otherwise accurate, including the one-time SQLite→PostgreSQL transfer procedure.

There is no linter, formatter, pytest config, `conftest.py`, or CI in this repo.

## Architecture

### Import layout — apps are top-level modules

`src/config/settings.py:24` does `sys.path.insert(0, str(BASE_DIR / "apps"))`. So apps import as `from product.models import Product`, **not** `from apps.product.models import ...`, and `src/apps/__init__.py` deliberately does not exist. Path constants:

- `BASE_DIR` = `src/`, `PROJECT_DIR` = repo root
- `templates/`, `media/`, and the default SQLite export path `database/db.sqlite3` resolve against `BASE_DIR` (inside `src/`)
- `.env` and `staticfiles/` resolve against `PROJECT_DIR` (the repo root)

The `src/apps/*/api/` subpackages have no `__init__.py` and work as namespace packages. Follow that pattern rather than "fixing" it piecemeal.

### App name ≠ app label (do not change this)

Directories were renamed during a refactor but Django labels were kept so existing migrations and data stay valid:

| Python module | AppConfig `label` | DB tables |
|---|---|---|
| `accounts` | `accounts_app` | `accounts_app_user` |
| `dashboard` | `dashboard_app` | `dashboard_app_profile` |
| `product` | `products_app` | `products_app_product` |
| `cart` | `cart_app` | `cart_app_cart` |
| `order` | `order_app` | `order_app_order` |

Consequences when writing code:

- Python imports use the **module** name: `from order.models import OrderStatus`
- String FKs and migrations use the **label**: `models.ForeignKey("products_app.Product", ...)`
- `AUTH_USER_MODEL = 'accounts_app.User'` is correct as written

Unifying the labels would need `AlterModelTable` + `SeparateDatabaseAndState`. Don't attempt it as a side effect of another task.

### Dependency direction between product and order

`product/models.py` imports `InventoryReservation`, `OrderStatus`, `OrderItem` from `order.models` at module level. `order/models.py` therefore must refer to products only by the string label `"products_app.Product"` — adding a real import there creates a cycle.

### Inventory reservation (the distinguishing design)

Placing an order does **not** decrement `Product.stock`. `OrderCreate` creates `InventoryReservation` rows and an `expires_at` 15 minutes out. `Product.available_stock()` returns `stock - Σ(quantity of reservations whose order is PENDING_PAYMENT and not yet expired)`, so expired reservations drop out of the calculation automatically — stock is never permanently locked. Real stock is decremented only in the payment callback after server-side verification succeeds, which also flips reservations to `RELEASED`.

`OrderCreate` is `@transaction.atomic` and takes `SELECT ... FOR UPDATE` on cart products **ordered by id** to avoid deadlocks, and snapshots `price` onto `OrderItem`. Preserve all three properties when touching that flow.

### Product variants are two-level

`Product.parent` is a self-FK. `parent IS NULL` = base product; a child carries `variant_name`. `clean()` (invoked from `save()` via `full_clean()`, so it fires even from the shell) forbids a third level. Carts and orders attach to **variants** only; reviews are always re-pointed to the **base** product.

### Payment flow

Two-step by design: `POST /order/payment/<order_id>/` asks the gateway for a link, then the gateway's `GET /order/payment/callback/` (AllowAny) re-verifies server-side via `order/api/payment_verify.py` before marking PAID. Duplicate callbacks are rejected by checking `transaction_id`. Gateway and SMS calls go through `src/apps/common/http.py`, a thin `urllib` wrapper that raises `HttpError` — the project intentionally avoids a `requests` dependency.

### Cache

`CACHES['default']` is `product.custom_cache.FallbackCache`, which reads from the `redis` alias, falls back to `local` (LocMem) on any exception, and dual-writes to both. A Redis outage degrades rather than breaks. LocMem is per-process, so it is not shared across Gunicorn workers.

Product/review list invalidation uses a **version counter**, not key enumeration: `product/signals.py` bumps `products_cache_version` on `post_save`/`post_delete` of `Product` and `Review`, and cache keys embed `v{N}`. If you add a model whose changes should invalidate product listings, bump that counter rather than deleting keys. (`categories_list` is not covered by this and is only cleared manually.)

### Auth

`DEFAULT_AUTHENTICATION_CLASSES` tries `accounts.authentication.CookieJWTAuthentication` first (reads the `access_token` HttpOnly cookie), then falls through to standard header-based `JWTAuthentication` — so browser and Postman/mobile clients both work. Login sets cookies and does not return tokens in the body.

Registration is phone-OTP based: OTP is cached at `otp_<phone>` for 300s and sent via `accounts/utils.py:send_sms`, which only `print`s when `SMS_API_KEY` is unset.

### Throttling

`DEFAULT_THROTTLE_CLASSES` is **commented out** in `settings.py:194`, so only views declaring `throttle_classes`/`throttle_scope` are limited (order, payment, callback, product reads, auth views). Any scope you set must also exist in `DEFAULT_THROTTLE_RATES` or DRF raises `ImproperlyConfigured`.

### Celery

`config/celery.py` with `app = Celery("uzistore")`; `config/__init__.py` re-exports `celery_app`. Worker and beat run as `-A config`. Beat uses `django_celery_beat`'s `DatabaseScheduler`. The only task is `order.api.tasks.delete_expired_orders`, registered in `CELERY_BEAT_SCHEDULE`.

## Known-broken areas

`doc/ARCHITECTURE.md` §19 lists every defect with file:line. Confirmed still broken as of this file's writing:

- **Registration 500s**: `phone` is missing from `RegisterSerializer.Meta.fields` (`accounts/serializers.py:50`) but `create()` reads it (`:104`) → `create_user` raises `ValueError`.
- **Carts are not auto-created**: `cart/apps.py:ready()` has a docstring but no `import cart.signals`, so `create_cart` never registers. `cart/api/views.py` then calls `Cart.objects.get()` unguarded.
- **OTP keys don't match**: `RegisterView` caches under the raw submitted phone; `VerifySerializer` normalizes to `09…` first. The 5-attempt lockout also overwrites its own counter key with `True` (`accounts/views.py:94` vs `:97`), so it never triggers.
- **`ManagerOrderPanelView`** has neither `queryset` nor `serializer_class`, and uses an undefined `manager` throttle scope.
- **Phone format mismatch**: `PhoneNumberField` stores E.164 (`+989…`) but several queries look up `09…`.

(§19's claim that `Profile` has no migration is now stale — `dashboard/migrations/0001_initial.py` exists.)

`order/tests.py` is empty, and `accounts/tests.py` / `cart/tests.py` currently fail: they call `create_user()` without the now-required `phone`, test the old email-based OTP flow, and contain mis-indented test methods nested inside other tests (so those never run). Fix the indentation when you touch those files.

## Secrets

`.env` is untracked and absent from every reachable ref (`origin/main` and `origin/dev` histories are both clean). `.env.example` is the tracked template with the same 16 keys; keep the two in sync by key name and never put a real value in the example. The local `SECRET_KEY` has been rotated, and `PAYMENT_GATEWAY_API_KEY`/`SMS_API_KEY` are empty locally — but the leaked values still live in the abandoned `git.uzicoders.ir` upstream, so they must be rotated provider-side.

`PAYMENT_URLS["payment_gateway_callback_url"]` is hardcoded to `http://127.0.0.1:8000/...` in settings, so payments only complete locally until that is read from env.
