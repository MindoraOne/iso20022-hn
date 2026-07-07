---
name: security-optimization
description: Estandar obligatorio de seguridad y optimizacion para todos los proyectos y capas. Usar siempre al escribir codigo que maneje inputs de usuario, credenciales, tokens, datos sensibles, logs, dependencias o rendimiento.
---

# Seguridad y optimizacion

Aplica a todas las capas del proyecto: backend, frontend y servicios externos.

---

## Validacion de inputs y outputs

- Validar estrictamente todos los datos recibidos de usuarios, APIs externas o servicios internos
- Aplicar validacion de tipo, formato y rango permitido en cada entrada
- Rechazar y registrar cualquier input que no cumpla el esquema esperado
- Nunca confiar en datos que vengan del cliente aunque el frontend ya los valide

### Vulnerabilidades OWASP a prevenir siempre

| Vulnerabilidad | Prevencion |
| :--- | :--- |
| Inyeccion SQL / NoSQL | Usar queries parametrizadas o el ORM, nunca concatenar strings |
| XSS | Escapar outputs en HTML, usar CSP headers |
| CSRF | Tokens CSRF en formularios y validacion de origen |
| Subida de archivos | Validar tipo MIME real, extension, tamano y escanear contenido |
| Path traversal | Sanitizar rutas de archivo, no usar input del usuario directamente |
| Inyeccion de comandos | Nunca pasar input del usuario a comandos de shell sin sanitizacion estricta |
| Broken access control | Verificar permisos en cada endpoint, no solo en el frontend |
| Exposicion de datos sensibles | Filtrar campos sensibles antes de enviar respuestas |

### Ejemplo de validacion con schema (TypeScript)

```typescript
import { z } from 'zod';

const createUserSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8).max(128),
  name: z.string().min(1).max(100).regex(/^[a-zA-Z\s]+$/),
});

// En el controller, antes de pasar al servicio
const result = createUserSchema.safeParse(req.body);
if (!result.success) {
  return res.status(400).json({ error: result.error.flatten() });
}
```

---

## Credenciales y tokens

- Nunca almacenar credenciales en codigo fuente ni en control de versiones
- Usar variables de entorno o gestores de secretos (ver skill `env-config`)
- Tokens deben tener tiempo de expiracion definido y mecanismo de renovacion
- Hashing de contrasenas con algoritmos lentos por diseno: bcrypt (cost >= 12) o Argon2

```typescript
import bcrypt from 'bcrypt';

const SALT_ROUNDS = 12;

async function hashPassword(plain: string): Promise<string> {
  return bcrypt.hash(plain, SALT_ROUNDS);
}

async function verifyPassword(plain: string, hashed: string): Promise<boolean> {
  return bcrypt.compare(plain, hashed);
}
```

- Tokens JWT deben incluir: expiracion (`exp`), emisor (`iss`) y audiencia (`aud`)
- Invalidar tokens comprometidos via lista de revocacion o rotacion de secreto
- Refresh tokens de vida larga deben almacenarse con hash, no en texto plano

---

## Cifrado y proteccion de datos

- Todo trafico en produccion debe usar HTTPS/TLS
- Datos sensibles en reposo deben cifrarse si el riesgo lo justifica (datos financieros, medicos, PII)
- Usar algoritmos recomendados por la industria: AES-256 para simetrico, RSA-2048+ o ECDSA para asimetrico
- No implementar criptografia propia: usar librerias auditadas
- Nunca exponer informacion sensible en mensajes de error ni en respuestas HTTP

```typescript
// Incorrecto: expone detalle interno
res.status(500).json({ error: err.message, stack: err.stack });

// Correcto: mensaje generico al cliente, detalle en logs internos
logger.error('Unexpected error in createUser', { error: err });
res.status(500).json({ error: 'Internal server error' });
```

---

## Logging y auditoria

- Logs deben indicar: que sucedio, cuando (timestamp ISO), en que modulo y con que contexto de usuario si aplica
- Nunca incluir en logs: contraseñas, tokens, claves API, datos de tarjeta ni PII completa
- Datos de usuario en logs: usar ID o email enmascarado, no datos completos
- Implementar auditoria (registro de quien hizo que y cuando) en modulos criticos: autenticacion, pagos, cambios de permisos, eliminaciones

```typescript
// Incorrecto
logger.info(`User login: email=${user.email} password=${dto.password}`);

// Correcto
logger.info('User login successful', { userId: user.id, ip: req.ip });
```

### Niveles de log

| Nivel | Cuando usar |
| :--- | :--- |
| `error` | Excepciones no controladas, fallos criticos |
| `warn` | Situaciones anormales que no detienen el flujo |
| `info` | Eventos de negocio relevantes (login, creacion, pago) |
| `debug` | Informacion de desarrollo, nunca en produccion |

---

## Control de acceso

- Verificar autenticacion y autorizacion en cada endpoint, nunca asumir que el cliente ya lo hizo
- Principio de minimo privilegio: cada rol accede solo a lo estrictamente necesario
- No exponer endpoints de administracion sin autenticacion robusta
- Validar que el usuario autenticado tiene permiso sobre el recurso especifico, no solo sobre el endpoint

```typescript
// Incorrecto: verifica autenticacion pero no que el recurso pertenece al usuario
async getDocument(req: Request, res: Response) {
  const doc = await documentService.findById(req.params.id);
  res.json(doc);
}

// Correcto
async getDocument(req: Request, res: Response) {
  const doc = await documentService.findById(req.params.id);
  if (doc.ownerId !== req.user.id) {
    return res.status(403).json({ error: 'Forbidden' });
  }
  res.json(doc);
}
```

---

## Optimizacion

### Codigo

- Sin codigo duplicado: extraer en funciones reutilizables (skill `code-standards`)
- Dividir funciones con alta complejidad ciclomatica
- Eliminar dependencias no utilizadas: `npm prune`, `pip-autoremove`
- Mantener dependencias actualizadas y revisar alertas de seguridad: `npm audit`, `pip-audit`

### Consultas a base de datos

- Usar indices en columnas usadas frecuentemente en filtros y joins
- Evitar consultas N+1: usar eager loading o DataLoader cuando aplique
- Limitar siempre el numero de resultados en queries sin filtro explicito
- Evitar `SELECT *`: seleccionar solo los campos necesarios

```typescript
// Incorrecto: trae todos los campos y sin limite
const users = await prisma.user.findMany();

// Correcto
const users = await prisma.user.findMany({
  select: { id: true, email: true, name: true },
  take: 50,
  where: { active: true },
});
```

### Cache

- Aplicar cache para datos que no cambian frecuentemente y son costosos de calcular o consultar
- Definir TTL (tiempo de vida) explicito por tipo de dato
- Invalidar cache al modificar los datos que representa

### Frontend

- Minimizar el bundle size: code splitting y lazy loading de rutas y componentes pesados
- Evitar re-renders innecesarios: memoizar componentes y valores cuando el profiler lo justifique
- No optimizar prematuramente: medir primero con herramientas (Lighthouse, React Profiler, etc.)

---

## Integracion con otros estandares

- Manejo de secretos y variables de entorno segun skill `env-config`
- Sanitizacion de codigo con linter antes de todo commit (skill `code-standards`)
- Datos sensibles nunca en mensajes de commit, PR descriptions ni nombres de rama (skill `commits-versioning`, `pull-request-standards`)
- Tests de seguridad (validaciones, autorizacion) incluidos en la cobertura minima (skill `testing-standards`)
