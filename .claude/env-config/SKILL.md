---
name: env-config
description: Estandar obligatorio para variables de entorno, archivos de configuracion y manejo de secretos. Usar al crear o modificar archivos .env, configuraciones, credenciales, integraciones con servicios externos o cualquier valor sensible.
---

# Variables de entorno, configuracion y secretos

## Variables de entorno

### Formato

- Nombres en ingles, UPPER_CASE con guiones bajos: `DB_USER`, `API_KEY`, `SMTP_HOST`
- Cada variable con proposito claro documentado en `.env.example`
- Sin variables extra ni opcionales: todo lo que existe en `.env` debe estar en `.env.example` y viceversa

### Clasificacion

| Tipo | Donde va | Versionado |
| :--- | :--- | :--- |
| Secretos y valores sensibles | `.env` | No, nunca |
| Documentacion de variables | `.env.example` | Si, siempre |
| Configuracion no sensible | `config/` | Si |

## Archivos .env y .env.example

Ambos en la raiz del proyecto.

- `.env`: valores reales del entorno local o del deployment. Nunca se versiona.
- `.env.example`: plantilla con todas las variables y placeholders sin valores reales. Es el unico versionado.

Formato:

```
KEY=VALUE
```

Ejemplo `.env.example`:

```bash
DB_HOST=localhost
DB_USER=your_user
DB_PASSWORD=your_password
API_KEY=your_api_key
PORT=3000
```

Ejemplo `.env` (local, no versionado):

```bash
DB_HOST=localhost
DB_USER=admin
DB_PASSWORD=SuperSecret123
API_KEY=abcdef123456
PORT=3000
```

### Regla de sincronizacion

`.env` y `.env.example` siempre deben estar sincronizados. Actualizar `.env.example` cada vez que se agregue o elimine una variable.

## Separacion de entornos

Para modularizar variables por area o entorno:

| Archivo | Proposito |
| :--- | :--- |
| `.env.local` | Desarrollo local |
| `.env.development` | Entorno de desarrollo compartido |
| `.env.staging` | Staging |
| `.env.production` | Produccion |

- Mecanismo explicito para cargar el entorno correcto: `dotenv` en Node, `python-decouple` en Python
- Las reglas de nomenclatura y sincronizacion aplican a todos los entornos
- Cada archivo de entorno tiene su correspondiente `.env.<entorno>.example`

## Configuracion no sensible

Archivos en `config/`, nombres en kebab-case, nunca con credenciales:

- `config/app-config.json`: parametros de la aplicacion
- `config/logging-config.json`: configuracion de logs
- `config/routes-config.json`: rutas y permisos

Ejemplo:

```json
{
  "appName": "MyProject",
  "logLevel": "info",
  "maxUploadSizeMB": 10
}
```

## Secretos

### Reglas absolutas

- Nunca hardcodear secretos en el codigo fuente
- Nunca versionar secretos en git (ni en `.env`, ni en archivos de config, ni en comentarios)
- Nunca loggear valores sensibles: contraseñas, tokens, claves API
- Nunca incluir secretos en mensajes de commit, nombres de ramas o PR descriptions
- Si un secreto se expone accidentalmente, rotarlo de inmediato y revocar el anterior

### Gestion en entornos productivos

En staging y produccion los secretos no deben venir de archivos `.env` locales sino de un gestor de secretos:

- AWS Secrets Manager / Parameter Store
- HashiCorp Vault
- Azure Key Vault
- GCP Secret Manager
- Variables de entorno inyectadas por el orquestador (Docker, Kubernetes, CI/CD)

La aplicacion los carga en tiempo de ejecucion, nunca en tiempo de build.

### Rotacion de secretos

- Rotar credenciales periodicamente segun politica del proyecto
- Rotar inmediatamente ante: exposicion accidental, salida de un miembro del equipo, brecha de seguridad sospechada
- Documentar el proceso de rotacion en `docs/`

### Clasificacion de sensibilidad

| Tipo | Ejemplos | Manejo |
| :--- | :--- | :--- |
| Criticos | Credenciales de DB produccion, claves privadas, tokens de admin | Solo gestor de secretos, rotacion obligatoria |
| Altos | API keys de servicios de pago, tokens OAuth | Gestor de secretos o `.env` local nunca versionado |
| Medios | Configuracion de servicios internos, endpoints privados | `.env` local o `config/` segun sensibilidad |
| Bajos | Nombre de la app, nivel de log, puertos | `config/` versionado |

### .gitignore obligatorio

Todo proyecto debe incluir en `.gitignore`:

```
.env
.envrc
.env.local
.env.*.local
.env.*
!.env.example
!**/.env.example
*.pem
*.key
*.p12
*.pfx
secrets/
```
