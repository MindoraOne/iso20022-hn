---
name: naming-conventions
description: Estandar obligatorio de nomenclatura de archivos y carpetas para todos los proyectos. Usar siempre al crear, renombrar o reorganizar archivos y carpetas, generar estructura de proyectos o revisar codigo.
---

# Nomenclatura de archivos y carpetas

Todos los nombres de archivos y carpetas deben estar en ingles, sin espacios, acentos ni caracteres especiales.

## Principios generales

- Reglas obligatorias sin excepciones
- Ingles en todos los nombres de archivo y carpeta
- Nombres claros y descriptivos, sin abreviaciones ambiguas
- Cualquier desarrollador debe identificar el proposito del archivo solo por su nombre
- Refactorizar nombres que no cumplan la convencion en cada mantenimiento

## Convencion de archivos por tipo

| Tipo | Stack | Convencion | Numeracion | Ejemplo |
| :--- | :--- | :--- | :--- | :--- |
| JavaScript | Frontend | camelCase.js | No | `userForm.js` |
| JavaScript | Backend / Node | camelCase.js | Si, si requiere orden | `01_initializeDB.js` |
| Tests JS | Frontend / Backend | camelCase.test.js | Si, si requiere orden | `loginFlow.test.js` |
| TypeScript | Frontend / Backend | camelCase.ts | Si, si requiere orden | `userService.ts` |
| Python | Backend | snake_case.py | Si, si requiere secuencia | `data_loader.py` |
| Shell | DevOps / Backend | snake_case.sh | Si, si requiere orden | `01_setup_env.sh` |
| HTML | Frontend | kebab-case.html | No | `login-page.html` |
| JSX / TSX | Frontend React | PascalCase.jsx / .tsx | No | `LoginForm.jsx` |
| CSS / SCSS / SASS | Frontend | kebab-case | No | `main-layout.scss` |
| Markdown | Documentacion | kebab-case.md | Si, si es secuencial | `01_project-setup.md` |
| JSON | Configuracion | camelCase.json | Si, si requiere orden | `appConfig.json` |
| Logs | Backend / Scripts | YYYYMMDD_hhmmss.log | Timestamp obligatorio | `20251023_093015.log` |
| .env | Configuracion | snake_case.env | No | `development.env` |
| SQL | DB / Migraciones | snake_case.sql | Numeracion obligatoria | `01_create_users_table.sql` |
| Prisma Schema | Backend / DB | snake_case.prisma | No | `schema.prisma` |

## Reglas por stack

### Frontend

- Componentes React: `PascalCase.jsx` / `.tsx`
- Scripts JS: `camelCase.js`
- HTML / CSS / SCSS / SASS: `kebab-case`
- Tests: `camelCase.test.js`

### Backend

- Scripts Python: `snake_case.py`
- Scripts Node: `camelCase.js`
- Tests JS / TS: `camelCase.test.js`
- Migraciones SQL: numeracion obligatoria + `snake_case.sql`
- Logs: timestamp obligatorio
- Configuracion `.env`: `snake_case`

### Documentacion

- Todos los Markdown: `kebab-case.md`
- Numeracion solo si requiere secuencia: `01_`, `02_`, etc.

## Numeracion inicial

Usar `00_`, `01_`, `02_` unicamente para archivos que requieran orden explicito:

- Scripts de migracion de base de datos
- Scripts de inicializacion que se ejecutan en secuencia
- Documentacion paso a paso

## Ejemplos por contexto

Frontend React:

```
src/components/LoginForm.jsx
src/components/RegisterForm.jsx
src/utils/validateEmail.js
src/styles/main-layout.scss
tests/loginFlow.test.js
```

Backend Node + Python:

```
scripts/01_initializeDB.js
scripts/02_loadSampleData.js
app/server.js
app/routes/userRoutes.js
tests/userService.test.js
```

Base de datos:

```
migrations/01_create_users_table.sql
migrations/02_add_roles_table.sql
prisma/schema.prisma
logs/20251023_093015.log
```

Documentacion:

```
docs/01_project-setup.md
docs/02_deployment-guide.md
docs/03_testing-guide.md
```

## Carpetas estandar por tipo de proyecto

| Carpeta | Stack | Proposito |
| :--- | :--- | :--- |
| `src` | Frontend / Backend | Codigo fuente principal |
| `tests` | Frontend / Backend | Pruebas unitarias y de integracion |
| `scripts` | Backend / DevOps | Scripts ejecutables (DB, CI/CD, setup) |
| `config` | Frontend / Backend | Archivos de configuracion (no incluye `.env`) |
| `docs` | Todos | Documentacion tecnica del proyecto |
| `public` | Frontend | Archivos estaticos accesibles publicamente |
| `assets` | Frontend / Docs | Imagenes, iconos, fuentes |
| `migrations` | Backend / DB | Scripts de migracion de base de datos |
| `logs` | Backend / Scripts | Archivos de logs generados por la aplicacion |
| `prisma` | Backend / DB | Esquema de Prisma |
| `.github` | Todos | Workflows, Actions y templates de GitHub |

## Reglas de carpetas

- Nombres en kebab-case: `nombre-de-carpeta`
- Subcarpetas descriptivas del contenido: `src/controllers`, `src/services`, `docs/setup`, `scripts/db`
- No mezclar codigo fuente con documentacion o configuraciones en la misma carpeta
- Carpetas generadas o temporales (`dist`, `build`, `.cache`) deben estar en `.gitignore`
- `node_modules` nunca se versiona

---

## Contenedores y volumenes Docker

Cuando un proyecto corre con docker-compose, cada contenedor, volumen y red debe seguir dos reglas:

1. **Prefijo de proyecto** en formato kebab-case: siglas del nombre del repo. Ejemplo: repo `lead-flow-ai` -> prefijo `lf-ai`; repo `saas-core` -> prefijo `saas-core`. El prefijo evita colisiones cuando multiples proyectos corren a la vez en la misma maquina.
2. **Nombre tematico** para cada servicio, siguiendo un tema geek consistente a lo largo del proyecto. El tema puede variar segun el gusto del equipo (mitologias, sagas, universos de ficcion, etc.) — lo importante es elegirlo al inicio y no mezclar universos: todos los nombres del proyecto deben pertenecer al mismo tema.

### Estructura

| Elemento | Formato | Ejemplo generico |
| :--- | :--- | :--- |
| Contenedor | `{prefix}-{theme-name}` | `myapp-service-a`, `myapp-service-b` |
| Volumen | `{prefix}-{theme-name}-data` | `myapp-service-a-data` |
| Red | `{prefix}-{collective}` | `myapp-collective` (colectivo propio del tema elegido) |
| Service name (interno compose) | `{theme-name}` sin prefijo | `service-a`, `service-b` |

El **service name** dentro de `docker-compose.yml` se deja sin prefijo para que los servicios se comuniquen entre si con nombres cortos (`http://service-a:5678`). El `container_name` explicito sirve para `docker ps`, logs y scripts.

### Elegir el tema

Al arrancar un proyecto, elige un tema que tenga al menos 10-15 nombres reconocibles (suficiente para crecer). Mantener el tema facilita recordar roles y mejora la experiencia del equipo.

Ejemplos de temas validos (cualquiera sirve, pueden variar):

| Tema | Ejemplos de nombres | Colectivo (red) |
| :--- | :--- | :--- |
| Personajes de sagas de fantasia | nombres de personajes de la saga elegida | colectivo del universo (ciudad, grupo, orden) |
| Universos de ciencia ficcion | nombres de personajes, naves o lugares | nombre del universo o faccion |
| Mitologias (griega, nordica, egipcia, etc.) | nombres de deidades o figuras miticas | lugar simbolico del pantheon |
| Comics y superheroes | nombres de personajes del universo elegido | grupo o equipo (liga, hermandad) |
| Matematicos, cientificos o filosofos | apellidos reconocibles | `academia`, `lyceum`, `institute` |

La tabla es ilustrativa: elige un tema que el equipo disfrute y que tenga suficientes nombres para cubrir los servicios del proyecto.

### Mapear nombre tematico al rol del servicio

El nombre debe tener una **conexion semantica** con lo que hace el servicio, no escogerse al azar. Esto ayuda a recordar que hace cada contenedor.

Ejemplo generico (proyecto `myapp`, tema a elegir por el equipo):

| Servicio tecnico | Container | Criterio semantico |
| :--- | :--- | :--- |
| API principal / voz | `myapp-{name}` | Personaje asociado a comunicacion o mensajes |
| Orquestador de flujos | `myapp-{name}` | Personaje asociado a viajes, rutas o coordinacion |
| Base de datos | `myapp-{name}` | Personaje que sostiene, guarda o carga algo |
| Cache | `myapp-{name}` | Personaje asociado a memoria o rapidez |
| Busqueda vectorial | `myapp-{name}` | Personaje asociado a vision, prediccion o oraculo |
| LLM local | `myapp-{name}` | Personaje asociado a conocimiento o sabiduria |
| Ingestor / procesador | `myapp-{name}` | Personaje asociado a trabajo manual o cosecha |

El equipo reemplaza `{name}` con el nombre concreto del tema elegido siguiendo la misma conexion semantica.

### Qué NO hacer

- No mezclar temas: mantener un unico universo en todo el proyecto, de lo contrario si se repite el diferenciador debe ser el id dado por el proyecto o  repositorio.
- No usar el nombre tecnico como container: `myapp-postgres` pierde la conexion tematica
- No omitir el prefijo: un nombre suelto puede chocar con contenedores de otros proyectos en la misma maquina
- No usar mayusculas ni underscores: siempre kebab-case (`myapp-service`, no `myapp-Service` ni `myapp_service`)

### Integracion con otros estandares

- Los archivos de configuracion del stack siguen el skill general (`docker-compose.yml`, `Dockerfile`)
- Las variables de entorno que referencian contenedores usan el service name sin prefijo (`DB_POSTGRESDB_HOST=atlas`, no `lf-ai-atlas`) porque la comunicacion interna en la red compose usa el service name
- Las rutas externas (puertos expuestos al host) no se ven afectadas; solo los nombres identificadores
