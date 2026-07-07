---
name: testing-standards
description: Estandar obligatorio de pruebas para todos los proyectos. Usar siempre al crear, modificar o revisar tests unitarios, de integracion, mocks, fixtures o configuracion de CI/CD para ejecucion de pruebas.
---

# Estandar de testing

## Estructura de carpetas

```
tests/
  unit/           # Pruebas unitarias por modulo
  integration/    # Pruebas de integracion entre modulos o con servicios externos
  mocks/          # Mocks reutilizables entre tests
  fixtures/       # Datos de prueba estaticos o factories
  helpers/        # Utilidades auxiliares para tests
```

Si el proyecto organiza por modulo, los tests pueden ubicarse junto al codigo:

```
src/
  users/
    user.service.ts
    user.service.test.ts
    user.repository.ts
    user.repository.test.ts
```

Ambas convenciones son validas. Elegir una y mantenerla consistente en todo el proyecto.

## Nomenclatura de archivos de prueba

Seguir la misma convencion que el archivo que se prueba, mas el sufijo correspondiente:

| Tipo | Sufijo | Ejemplo |
| :--- | :--- | :--- |
| Test unitario JS/TS | `.test.ts` | `user.service.test.ts` |
| Test unitario Python | `_test.py` | `user_service_test.py` |
| Test de integracion | `.int.test.ts` | `user.int.test.ts` |
| Test de integracion alternativo | `.integration.test.ts` | `auth.integration.test.ts` |

Los nombres siguen el skill `naming-conventions`: camelCase para JS/TS, snake_case para Python.

## Cobertura minima

- No inferior al 70% de las funciones criticas
- Funciones criticas: logica de negocio en servicios, validaciones, transformaciones de datos, manejo de errores
- Funciones no criticas (helpers simples, utilidades de formato): cobertura recomendada pero no obligatoria
- Las pruebas deben cubrir: comportamiento esperado, manejo de errores y casos limite

## Estructura de un test

Seguir el patron AAA (Arrange, Act, Assert):

```typescript
describe('UserService', () => {
  describe('create', () => {
    it('should create a user when email is not taken', async () => {
      // Arrange
      const dto = { email: 'user@example.com', password: 'secret123', name: 'Test' };
      userRepo.findByEmail.mockResolvedValue(null);
      userRepo.save.mockResolvedValue({ id: '1', ...dto });

      // Act
      const result = await userService.create(dto);

      // Assert
      expect(result.id).toBeDefined();
      expect(userRepo.save).toHaveBeenCalledOnce();
    });

    it('should throw ConflictException when email already exists', async () => {
      // Arrange
      const dto = { email: 'taken@example.com', password: 'secret123', name: 'Test' };
      userRepo.findByEmail.mockResolvedValue({ id: '99', ...dto });

      // Act & Assert
      await expect(userService.create(dto)).rejects.toThrow(ConflictException);
    });
  });
});
```

Reglas de estructura:

- `describe` agrupa por clase o modulo
- `describe` anidado agrupa por metodo o funcion
- `it` o `test` describe el comportamiento esperado en lenguaje natural
- Un solo concepto por test
- Sin logica compleja dentro de los tests

## Mocks y fixtures

### Mocks

Simulan dependencias externas para aislar la unidad bajo prueba:

```typescript
// tests/mocks/user.repository.mock.ts
export const mockUserRepository = {
  findById: vi.fn(),
  findByEmail: vi.fn(),
  save: vi.fn(),
  delete: vi.fn(),
};
```

Reglas:

- Nombres descriptivos: `mockUserRepository`, `mockPaymentService`
- Documentar brevemente el proposito en comentarios si no es evidente
- Resetear mocks entre tests con `beforeEach(() => vi.clearAllMocks())`

### Fixtures

Datos de prueba reutilizables:

```typescript
// tests/fixtures/user.fixture.ts
export const userFixture = {
  valid: {
    id: 'user-001',
    email: 'test@example.com',
    name: 'Test User',
    createdAt: new Date('2024-01-01'),
  },
  admin: {
    id: 'user-002',
    email: 'admin@example.com',
    name: 'Admin User',
    role: 'admin',
    createdAt: new Date('2024-01-01'),
  },
};
```

Para datos variables, usar factories:

```typescript
// tests/fixtures/user.factory.ts
export function createUserFixture(overrides: Partial<User> = {}): User {
  return {
    id: 'user-001',
    email: 'test@example.com',
    name: 'Test User',
    createdAt: new Date('2024-01-01'),
    ...overrides,
  };
}
```

## Tests de integracion

Los tests de integracion verifican la interaccion entre modulos o con servicios externos reales (DB, APIs):

```typescript
// tests/integration/user.int.test.ts
describe('UserRepository (integration)', () => {
  beforeAll(async () => {
    await setupTestDatabase();
  });

  afterAll(async () => {
    await teardownTestDatabase();
  });

  afterEach(async () => {
    await clearTestData();
  });

  it('should persist and retrieve a user', async () => {
    const user = createUserFixture();
    await userRepo.save(user);
    const found = await userRepo.findById(user.id);
    expect(found?.email).toBe(user.email);
  });
});
```

Reglas de integracion:

- Usar una base de datos de test aislada, nunca la de desarrollo o produccion
- Limpiar datos entre tests para evitar dependencias entre pruebas
- Los tests de integracion pueden ser mas lentos: separar su ejecucion de los unitarios

## Herramientas recomendadas por stack

| Stack | Test runner | Assertions | Mocks |
| :--- | :--- | :--- | :--- |
| TypeScript / Node | Vitest | Vitest | Vitest (`vi.fn()`) |
| JavaScript / Node | Jest | Jest | Jest (`jest.fn()`) |
| Python | pytest | pytest | pytest-mock |
| React | Vitest + Testing Library | Vitest | Vitest |

## CI/CD

- Ejecutar pruebas unitarias en cada push y pull request
- Fallos en tests bloquean merge a `main` y `develop`
- Tests de integracion pueden ejecutarse en un pipeline separado o bajo demanda
- Reportar cobertura cuando el proyecto lo configure

Ejemplo de script en `package.json`:

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "test:integration": "vitest run tests/integration"
  }
}
```

## Nota sobre Gherkin y feature files

Los tests con Gherkin (`.feature`) son de naturaleza operativa, no tecnica. La estructura y convencion para este tipo de pruebas sera definida por la organizacion segun el proyecto. Esta guia cubre unicamente la parte tecnica de los tests.

## Integracion con otros estandares

- Nombres de archivos de test segun skill `naming-conventions`
- El codigo de los tests sigue las mismas reglas de estilo que el skill `code-standards`
- El linter debe pasar antes de considerar los tests listos (skill `code-standards`, seccion de sanitizacion)
- Los commits con tests siguen el tipo `test` del skill `commits-versioning`
