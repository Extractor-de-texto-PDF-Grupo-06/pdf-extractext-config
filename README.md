# pdf-extractext-config

Microservicio de **configuración centralizada** de
[pdf-extractext](https://github.com/Extractor-de-texto-PDF-Grupo-06/pdf-extractext-orchestration).
Expone un CRUD por HTTP sobre el KV de Consul y es el único servicio que habla con Consul
(ADR 0003). Los demás servicios piden sus valores acá y, si no responde, usan sus variables
de entorno.

## Contrato

Traefik publica el servicio bajo `/config` y quita el prefijo antes de reenviar.

| Método y ruta | Entrada | Respuesta |
|---|---|---|
| `POST /` | JSON `{key, value}` | `201` entrada · `409` ya existe · `422` |
| `GET /?prefix=` | — | `200` `{entries, total}` |
| `GET /{key}` | — | `200` · `404` |
| `PUT /{key}` | JSON `{value, index?}` | `200` · `404` · `409` si otro la cambió |
| `DELETE /{key}` | — | `204` · `404` |
| `GET /health` | — | `200` si Consul tiene líder; `503` si no |

Una entrada es `{key, value, index}`. Las claves tienen la forma `<servicio>/<nombre>` en
minúsculas (por ejemplo `web/max_file_size_mb`) y se guardan en Consul bajo
`pdf-extractext/`. Los valores son siempre texto y **nunca secretos**: Consul los guarda
en texto plano.

`index` cambia con cada escritura. Si `PUT` lo recibe, solo escribe cuando el valor no
cambió desde que se leyó (check-and-set); si no lo recibe, usa el índice que lee en ese
momento. Cualquier error responde `{"detail": "…"}`, y si Consul no responde, `503`.

## Configuración

Por variables de entorno (ver `.env.example`):

| Variable | Por defecto | Para qué |
|---|---|---|
| `CONSUL_URL` | `http://localhost:8500` | Agente de Consul |
| `CONSUL_KV_ROOT` | `pdf-extractext` | Raíz del KV |
| `CONSUL_TIMEOUT_SECONDS` | `2` | Espera antes de dar a Consul por caído |
| `PORT` | `8000` | Puerto HTTP |

## Desarrollo

```bash
uv sync --group dev
uv run pytest                   # unitarios: sin red, sin Consul
uv run pytest -m integration    # contra Consul (CONSUL_URL); se saltan si no responde
uv run python -m app.main       # levanta el servicio en PORT
docker build -t pdf-extractext-config:dev .
```

Para los tests de integración alcanza con un Consul local:

```bash
docker run -d --name consul -p 127.0.0.1:8500:8500 hashicorp/consul:2.1 \
  agent -server -bootstrap-expect=1 -client=0.0.0.0
```

## Estructura

```
app/
├── presentation/     rutas, esquemas y errores de FastAPI
├── application/      casos de uso, puerto ConfigStore y entidades; solo biblioteca estándar
├── infrastructure/   ConsulConfigStore, el adaptador del puerto con py-consul
├── core/             Settings
├── dependencies.py   arma las dependencias
└── main.py
tests/
├── test_architecture.py   la regla de dependencias entre capas
├── test_store_contract.py el mismo contrato para el doble en memoria y para Consul
└── test_*.py
```

La imagen es multi-stage: la final tiene solo el entorno virtual y el código, corre con el
usuario `10001` y declara un `HEALTHCHECK` contra `/health`.

## Seguridad de la imagen

El escaneo Trivy 0.76.2 del 22/11/2026 sobre Debian 13.8 encontró 12 CVE de severidad alta
sin versión corregida disponible en Debian y ninguna crítica: CVE-2025-69720,
CVE-2026-119373, CVE-2026-119374, CVE-2026-119379, CVE-2026-124709, CVE-2026-16742,
CVE-2026-54369, CVE-2026-76642, CVE-2026-78408, CVE-2026-78409, CVE-2026-78410 y
CVE-2026-9538. Afectan paquetes del sistema base (ncurses, SQLite, OpenSSL, systemd,
acl, util-linux y Perl), no dependencias Python de la aplicación. La imagen ejecuta como
UID 10001 y, en orchestration, Compose aplica `read_only`, `cap_drop: [ALL]` y
`no-new-privileges:true`. La CI ignora solo hallazgos sin corrección publicada; cuando
Trivy detecte una versión corregida, el hallazgo vuelve a bloquearla.
