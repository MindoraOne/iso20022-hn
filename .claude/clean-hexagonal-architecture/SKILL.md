---
name: clean-hexagonal-architecture
description: Guia de arquitectura limpia y hexagonal para proyectos que requieren alta mantenibilidad, testabilidad y desacoplamiento entre logica de negocio e infraestructura. Usar al disenar o estructurar proyectos backend complejos.
---

# Clean Architecture y Arquitectura Hexagonal

Ambas arquitecturas comparten el mismo principio central: la logica de negocio no debe depender de ningun detalle de infraestructura (base de datos, framework, HTTP, mensajeria). La dependencia siempre apunta hacia adentro.

## Principio fundamental

```
Infraestructura -> Aplicacion -> Dominio
```

El dominio no importa nada del exterior. La infraestructura implementa las interfaces definidas por el dominio.

---

## Clean Architecture

### Capas

```
src/
  domain/           # Entidades, value objects, interfaces de repositorio
  application/      # Casos de uso (use cases)
  infrastructure/   # Implementaciones concretas (DB, HTTP, colas)
  interfaces/       # Controladores, presenters, CLI, GraphQL resolvers
```

### Domain

Contiene las reglas de negocio puras. No importa ningun framework ni libreria externa.

- Entidades con identidad y comportamiento propio
- Value Objects inmutables sin identidad
- Interfaces de repositorios y servicios externos
- Excepciones de dominio

```typescript
// domain/entities/user.entity.ts
export class User {
  constructor(
    public readonly id: string,
    public readonly email: string,
    private password: string,
  ) {}

  changePassword(newPassword: string): void {
    if (!newPassword || newPassword.length < 8) {
      throw new DomainException('Password must be at least 8 characters');
    }
    this.password = newPassword;
  }
}

// domain/repositories/user.repository.ts
export interface UserRepository {
  findById(id: string): Promise<User | null>;
  save(user: User): Promise<void>;
}
```

### Application

Orquesta los casos de uso. Coordina entidades y repositorios pero no contiene logica de negocio.

```typescript
// application/use-cases/create-user.use-case.ts
export class CreateUserUseCase {
  constructor(private readonly userRepo: UserRepository) {}

  async execute(dto: CreateUserDto): Promise<void> {
    const existing = await this.userRepo.findByEmail(dto.email);
    if (existing) throw new ApplicationException('Email already in use');

    const user = new User(generateId(), dto.email, dto.password);
    await this.userRepo.save(user);
  }
}
```

### Infrastructure

Implementa las interfaces definidas en el dominio. Aqui viven ORM, clientes HTTP, colas, etc.

```typescript
// infrastructure/repositories/prisma-user.repository.ts
export class PrismaUserRepository implements UserRepository {
  async findById(id: string): Promise<User | null> {
    const row = await prisma.user.findUnique({ where: { id } });
    return row ? new User(row.id, row.email, row.password) : null;
  }

  async save(user: User): Promise<void> {
    await prisma.user.upsert({ where: { id: user.id }, update: { ...user }, create: { ...user } });
  }
}
```

### Interfaces

Adaptadores de entrada: HTTP controllers, CLI commands, event handlers.

```typescript
// interfaces/http/user.controller.ts
export class UserController {
  constructor(private readonly createUser: CreateUserUseCase) {}

  async post(req: Request, res: Response): Promise<void> {
    await this.createUser.execute(req.body);
    res.status(201).json({ message: 'User created' });
  }
}
```

### Reglas de dependencia

- `domain` no importa nada de otras capas
- `application` importa solo de `domain`
- `infrastructure` importa de `domain` y `application`
- `interfaces` importa de `application`
- Nunca importar hacia afuera del circulo

### Inyeccion de dependencias

El punto de composicion (composition root) conecta las capas en el arranque de la aplicacion:

```typescript
// main.ts
const userRepo = new PrismaUserRepository();
const createUser = new CreateUserUseCase(userRepo);
const userController = new UserController(createUser);
```

---

## Arquitectura Hexagonal (Ports & Adapters)

Variante de Clean Architecture con terminologia diferente pero mismo principio. El dominio esta en el centro y se comunica con el exterior a traves de puertos (interfaces) y adaptadores (implementaciones).

### Terminologia

| Concepto | Equivalente en Clean |
| :--- | :--- |
| Puerto primario (driving) | Caso de uso / interfaz de entrada |
| Puerto secundario (driven) | Interfaz de repositorio o servicio externo |
| Adaptador primario | Controller, CLI, consumer de cola |
| Adaptador secundario | Repositorio concreto, cliente HTTP, broker |

### Estructura

```
src/
  domain/
    model/          # Entidades y value objects
    ports/
      in/           # Puertos primarios (interfaces de casos de uso)
      out/          # Puertos secundarios (interfaces de salida)
  application/
    services/       # Implementacion de puertos primarios
  adapters/
    in/             # HTTP, CLI, eventos de entrada
    out/            # DB, APIs externas, colas
```

### Ejemplo de puertos

```typescript
// domain/ports/in/create-user.port.ts
export interface CreateUserPort {
  execute(dto: CreateUserDto): Promise<void>;
}

// domain/ports/out/user-repository.port.ts
export interface UserRepositoryPort {
  findByEmail(email: string): Promise<User | null>;
  save(user: User): Promise<void>;
}
```

```typescript
// application/services/user.service.ts
export class UserService implements CreateUserPort {
  constructor(private readonly userRepo: UserRepositoryPort) {}

  async execute(dto: CreateUserDto): Promise<void> {
    const user = new User(generateId(), dto.email, dto.password);
    await this.userRepo.save(user);
  }
}
```

---

## Cuando usar cada una

| Contexto | Arquitectura recomendada |
| :--- | :--- |
| Backend complejo con multiples integraciones externas | Hexagonal |
| Backend con reglas de negocio ricas y equipo grande | Clean |
| Microservicio con logica simple | Layered (ver skill `layered-architecture`) |
| Proyecto con alta necesidad de testabilidad | Cualquiera de las dos |

## Reglas de integracion

- Nombres de archivos y carpetas segun skill `naming-conventions`
- Interfaces y clases segun skill `code-standards`
- Patrones usados dentro de cada capa segun skill `design-patterns`
- Nunca colocar logica de negocio en controllers ni en repositorios
