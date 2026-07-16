---
name: api-standards
description: Estandar obligatorio para el diseño de APIs RESTful, estructura de rutas, metodos HTTP, status codes, query params y formato de respuestas JSON. Usar siempre al crear, modificar o revisar endpoints, controladores, contratos de respuesta o documentacion de API.
---

# Estandar de APIs RESTful

## Principios generales

- APIs basadas en recursos (sustantivos), no acciones (verbos)
- Nombres de recursos en ingles, plural, kebab-case: `/api/v1/users`, `/api/v1/user-roles`
- La accion va en el metodo HTTP, no en la ruta
- Cuerpos de request y response en JSON con propiedades en camelCase
- APIs stateless: cada request contiene toda la informacion necesaria
- No exponer detalles internos: nombres de tablas, servicios internos, stack traces
- Toda API documentada en OpenAPI/Swagger

```
# Correcto
GET  /api/v1/users
POST /api/v1/users

# Incorrecto
POST /api/v1/createUser
GET  /api/v1/deleteUser
```

---

## camelCase en Python (Pydantic)

El contrato externo (JSON de request/response) va en camelCase; el codigo Python interno sigue en snake_case (PEP 8). La conversion se hace con **alias de Pydantic** (`Field(alias="camelCase")` + `model_config = ConfigDict(populate_by_name=True)`), nunca con un mapa/normalizador manual (dict de conversion + funcion aplicada a mano sobre los dicts). Ver `pain001/api/local/models.py` (repo `iso20022-hn`) o `pain002/mapping/contract.py` (repo `iso20022-response-hn`) como referencia del patron.

---

## Estructura de rutas

### Patron base

```
/api/v{version}/{recurso}/{sub-recursos...}
```

Ejemplos:

```
/api/v1/users
/api/v1/users/{userId}
/api/v1/users/{userId}/orders
/api/v1/orders/{orderId}/items
```

### Reglas de rutas

- `api` es fijo
- `v{n}` indica la version mayor: `v1`, `v2`
- El primer segmento es el recurso principal en plural
- Los recursos anidados representan relaciones jerarquicas claras
- Sin extensiones en la URL: `/api/v1/users` no `/api/v1/users.json`
- Los IDs van en el path, no como query params: `/api/v1/users/{userId}` no `?userId=123`
- El nombre del parametro en la ruta debe coincidir con el campo en el JSON: ruta `{userId}` → JSON `"userId"`

### Anidamiento

Usar anidamiento solo cuando existe una relacion padre-hijo clara. Evitar mas de dos niveles:

```
# Aceptable
/api/v1/users/{userId}/orders

# Evitar
/api/v1/companies/{companyId}/users/{userId}/orders/{orderId}/items/{itemId}
```

### Versionamiento

- Formato: `/api/v{major}` — `/api/v1`, `/api/v2`
- Cambios no retrocompatibles implican nueva version mayor
- Mantener versiones en paralelo hasta plan de deprecacion definido

---

## Metodos HTTP

| Metodo | Uso | Ejemplo |
| :--- | :--- | :--- |
| `GET` | Obtener recurso o lista | `GET /api/v1/users` |
| `POST` | Crear nuevo recurso | `POST /api/v1/users` |
| `PUT` | Reemplazo completo del recurso | `PUT /api/v1/users/{userId}` |
| `PATCH` | Actualizacion parcial | `PATCH /api/v1/users/{userId}` |
| `DELETE` | Eliminar recurso | `DELETE /api/v1/users/{userId}` |

- `GET` no debe tener efectos secundarios ni modificar estado
- `DELETE` debe ser idempotente: llamadas repetidas dan el mismo estado final
- `PUT` recibe una representacion completa del recurso

---

## Status codes

### Exito

| Codigo | Cuando usar |
| :--- | :--- |
| `200 OK` | Operacion exitosa con cuerpo de respuesta |
| `201 Created` | Recurso creado exitosamente |
| `204 No Content` | Operacion exitosa sin cuerpo (DELETE) |

### Error de cliente (4xx)

| Codigo | Cuando usar |
| :--- | :--- |
| `400 Bad Request` | Request mal formado, JSON invalido, parametros incorrectos |
| `401 Unauthorized` | Falta autenticacion o token invalido |
| `403 Forbidden` | Autenticado pero sin permisos sobre el recurso |
| `404 Not Found` | Recurso no encontrado |
| `409 Conflict` | Conflicto de estado (duplicidad unica, version desactualizada) |
| `422 Unprocessable Entity` | Validaciones de negocio fallidas |

### Error de servidor (5xx)

| Codigo | Cuando usar |
| :--- | :--- |
| `500 Internal Server Error` | Error no controlado |
| `503 Service Unavailable` | Servicio temporalmente no disponible |

---

## Query params

Usar para filtros, paginacion, ordenamiento y busqueda:

```
GET /api/v1/users?page=1&pageSize=20
GET /api/v1/users?status=active
GET /api/v1/orders?from=2025-01-01&to=2025-01-31
GET /api/v1/users?sortBy=createdAt&sortOrder=desc
GET /api/v1/products?q=keyboard
```

Nombres de params estandar:

| Proposito | Parametro |
| :--- | :--- |
| Pagina actual | `page` |
| Tamano de pagina | `pageSize` |
| Campo de orden | `sortBy` |
| Direccion de orden | `sortOrder` (`asc`/`desc`) |
| Busqueda de texto libre | `q` |

---

## Paginacion

Obligatoria en endpoints que puedan devolver grandes volumenes de datos (usuarios, ordenes, logs). Rechazar requests sin paginacion si la respuesta podria ser demasiado grande.

Los endpoints `GET` solo deben devolver los campos que el cliente va a utilizar, no el objeto completo si no es necesario. Los diccionarios estaticos o catalogos pequenos son la unica excepcion a la paginacion.

---

## Seguridad

- HTTPS obligatorio en todos los entornos productivos
- Bearer token en header `Authorization`:

```http
Authorization: Bearer <token>
```

- No exponer datos sensibles en URLs, query params, logs ni mensajes de error
- Secretos y tokens nunca en el codigo fuente (ver skill `env-config`)
- Validar autenticacion y autorizacion por recurso en cada endpoint (ver skill `security-optimization`)

---

## Formato de respuestas (obligatorio)

Todas las respuestas siguen la misma estructura. El formato es fijo y no se puede modificar por proyecto.

### Respuesta exitosa (recurso individual)

```json
{
  "code": "user_created",
  "message": "User created successfully",
  "data": {
    "userId": "u_123",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

- `code`: key value que el frontend busca en el diccionario de traducciones o mensajes
- `message`: mensaje legible para log o debug, no para mostrar al usuario final
- `data`: objeto de respuesta del endpoint. Omitir si no hay datos que devolver

### Respuesta de error

```json
{
  "code": "validation_error",
  "message": "Request validation failed",
  "errors": {
    "details": [
      {
        "field": "email",
        "code": "INVALID_FORMAT",
        "message": "Email must be a valid email address"
      },
      {
        "field": "password",
        "code": "MIN_LENGTH",
        "message": "Password must be at least 8 characters"
      }
    ]
  }
}
```

- `code`: codigo general del error para el frontend
- `message`: descripcion del error a nivel log o debug
- `errors.details`: lista de errores especificos cuando aplica (validaciones de campos, multiples fallos)
- `field`: campo afectado, si el error es especifico de un campo
- `errors.details` es opcional: incluir solo cuando hay informacion de detalle util

### Respuesta con paginacion (lista)

```json
{
  "code": "user_list",
  "message": "Resources list retrieved successfully",
  "data": [
    {
      "userId": "u_123",
      "email": "user@example.com",
      "name": "John Doe"
    },
    {
      "userId": "u_124",
      "email": "other@example.com",
      "name": "Jane Doe"
    }
  ],
  "meta": {
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "totalItems": 135,
      "totalPages": 7
    }
  }
}
```

- `data`: array de objetos. Solo los campos que el cliente necesita, no el objeto completo
- `meta.pagination.page`: pagina actual (>= 1)
- `meta.pagination.pageSize`: tamano de pagina
- `meta.pagination.totalItems`: total de registros
- `meta.pagination.totalPages`: total de paginas

---

## Integracion con otros estandares

- Validacion de inputs en cada endpoint segun skill `security-optimization`
- Manejo de secretos y variables de entorno segun skill `env-config`
- Nombres de archivos de controladores y rutas segun skill `naming-conventions`
- Funciones y clases de controladores segun skill `code-standards`
- Documentacion de cada endpoint siguiendo skill `documentation-standards`
