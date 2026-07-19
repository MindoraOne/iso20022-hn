---
name: design-patterns
description: Guia de patrones de diseno aplicables a todos los proyectos. Usar al disenar arquitectura, crear servicios, controladores, repositorios, eventos, estrategias de negocio o cuando se identifica codigo duplicado o acoplamiento alto.
---

# Patrones de diseno

Referencia de patrones aplicables segun contexto. No aplicar un patron por aplicarlo: usarlo cuando resuelve un problema concreto.

## Criterios para elegir un patron

- El codigo tiene logica duplicada que varia solo en detalles -> Strategy o Template Method
- Se necesita desacoplar quien produce datos de quien los consume -> Observer
- Se necesita abstraer el acceso a datos -> Repository
- Se necesita una unica instancia global compartida -> Singleton
- La creacion de objetos es compleja o variable -> Factory o Builder
- Se necesita adaptar una interfaz externa a la interna -> Adapter
- Se quiere agregar comportamiento sin modificar la clase original -> Decorator
- Hay dependencias complejas entre modulos -> Facade o Mediator

---

## Patrones creacionales

### Singleton

Garantiza una unica instancia de una clase en toda la aplicacion.

Cuando usarlo:
- Conexion a base de datos
- Cliente HTTP compartido
- Logger global
- Cache en memoria

```typescript
class DatabaseConnection {
  private static instance: DatabaseConnection;

  private constructor() {}

  static getInstance(): DatabaseConnection {
    if (!DatabaseConnection.instance) {
      DatabaseConnection.instance = new DatabaseConnection();
    }
    return DatabaseConnection.instance;
  }
}
```

Evitar: no usar para estado mutable compartido entre modulos independientes.

---

### Factory

Centraliza la creacion de objetos, desacoplando al consumidor de la implementacion concreta.

Cuando usarlo:
- Crear instancias de servicio segun tipo o entorno
- Instanciar estrategias o handlers segun parametro
- Tests donde se necesita inyectar implementaciones distintas

```typescript
interface Notifier {
  send(message: string): void;
}

class EmailNotifier implements Notifier { ... }
class SmsNotifier implements Notifier { ... }

class NotifierFactory {
  static create(type: 'email' | 'sms'): Notifier {
    if (type === 'email') return new EmailNotifier();
    if (type === 'sms') return new SmsNotifier();
    throw new Error(`Unknown notifier type: ${type}`);
  }
}
```

---

### Builder

Construye objetos complejos paso a paso con una interfaz fluida.

Cuando usarlo:
- Objetos con muchos parametros opcionales
- Construccion de queries o payloads complejos
- Configuracion de clientes o conexiones con opciones variables

```typescript
class QueryBuilder {
  private query = { table: '', conditions: [], limit: 100 };

  from(table: string): this {
    this.query.table = table;
    return this;
  }

  where(condition: string): this {
    this.query.conditions.push(condition);
    return this;
  }

  limit(n: number): this {
    this.query.limit = n;
    return this;
  }

  build() {
    return this.query;
  }
}

const query = new QueryBuilder().from('users').where('active = true').limit(50).build();
```

---

## Patrones estructurales

### Repository

Abstrae el acceso a datos detras de una interfaz, separando la logica de negocio del mecanismo de persistencia.

Cuando usarlo:
- Siempre que se accede a base de datos desde servicios de negocio
- Cuando se necesita poder cambiar el ORM o motor de DB sin tocar la logica
- Para facilitar mocking en tests

```typescript
interface UserRepository {
  findById(id: string): Promise<User | null>;
  save(user: User): Promise<void>;
  delete(id: string): Promise<void>;
}

class PrismaUserRepository implements UserRepository {
  async findById(id: string) {
    return prisma.user.findUnique({ where: { id } });
  }
  // ...
}
```

La capa de servicio solo conoce la interfaz, no la implementacion concreta.

---

### Adapter

Permite que una interfaz incompatible funcione con la interfaz esperada por el sistema.

Cuando usarlo:
- Integrar librerias o servicios externos con interfaces propias
- Normalizar respuestas de APIs terceras
- Migrar de una dependencia a otra sin cambiar el consumidor

```typescript
// Interfaz interna esperada
interface PaymentGateway {
  charge(amount: number, currency: string): Promise<boolean>;
}

// Adaptador de Stripe a la interfaz interna
class StripeAdapter implements PaymentGateway {
  async charge(amount: number, currency: string): Promise<boolean> {
    const result = await stripe.paymentIntents.create({ amount, currency });
    return result.status === 'succeeded';
  }
}
```

---

### Decorator

Agrega comportamiento a un objeto dinamicamente sin modificar su clase.

Cuando usarlo:
- Agregar logging, cache o validacion a servicios existentes
- Middlewares y pipes en frameworks
- Funcionalidades transversales (cross-cutting concerns)

```typescript
class CachedUserRepository implements UserRepository {
  constructor(
    private readonly base: UserRepository,
    private readonly cache: CacheService,
  ) {}

  async findById(id: string): Promise<User | null> {
    const cached = await this.cache.get(id);
    if (cached) return cached;
    const user = await this.base.findById(id);
    if (user) await this.cache.set(id, user);
    return user;
  }
}
```

---

### Facade

Provee una interfaz simplificada para un subsistema complejo.

Cuando usarlo:
- Orquestar multiples servicios desde un punto de entrada
- Simplificar interacciones con librerias complejas
- Exponer solo las operaciones relevantes de un modulo

```typescript
class OrderFacade {
  constructor(
    private inventory: InventoryService,
    private payment: PaymentService,
    private notification: NotificationService,
  ) {}

  async placeOrder(order: Order): Promise<void> {
    await this.inventory.reserve(order.items);
    await this.payment.charge(order.total);
    await this.notification.sendConfirmation(order.userId);
  }
}
```

---

## Patrones de comportamiento

### Observer / Event Emitter

Define una dependencia uno-a-muchos: cuando un objeto cambia de estado, notifica automaticamente a sus suscriptores.

Cuando usarlo:
- Eventos de dominio (usuario creado, pedido completado)
- Desacoplar efectos secundarios de la logica principal
- Sistemas de notificaciones o webhooks

```typescript
class EventBus {
  private handlers: Map<string, Function[]> = new Map();

  on(event: string, handler: Function): void {
    const list = this.handlers.get(event) ?? [];
    this.handlers.set(event, [...list, handler]);
  }

  emit(event: string, payload: unknown): void {
    this.handlers.get(event)?.forEach(h => h(payload));
  }
}
```

---

### Strategy

Define una familia de algoritmos intercambiables. Permite cambiar el comportamiento en tiempo de ejecucion.

Cuando usarlo:
- Multiples formas de calcular algo (precios, descuentos, impuestos)
- Distintos metodos de autenticacion o pago
- Ordenamiento o filtrado con criterios variables

```typescript
interface DiscountStrategy {
  calculate(price: number): number;
}

class PercentageDiscount implements DiscountStrategy {
  constructor(private percent: number) {}
  calculate(price: number) { return price * (1 - this.percent / 100); }
}

class FixedDiscount implements DiscountStrategy {
  constructor(private amount: number) {}
  calculate(price: number) { return price - this.amount; }
}

class PriceCalculator {
  constructor(private strategy: DiscountStrategy) {}
  getPrice(price: number) { return this.strategy.calculate(price); }
}
```

---

### Command

Encapsula una solicitud como objeto, permitiendo parametrizar, encolar o deshacer operaciones.

Cuando usarlo:
- Implementar undo/redo
- Encolar operaciones para ejecucion diferida
- Auditar o loggear acciones del sistema

```typescript
interface Command {
  execute(): Promise<void>;
  undo(): Promise<void>;
}

class CreateUserCommand implements Command {
  constructor(private service: UserService, private data: CreateUserDto) {}

  async execute() { await this.service.create(this.data); }
  async undo() { await this.service.delete(this.data.email); }
}
```

---

### Template Method

Define el esqueleto de un algoritmo en una clase base y delega los pasos variables a subclases.

Cuando usarlo:
- Flujos con pasos fijos pero implementacion variable (importacion, exportacion, reportes)
- Evitar duplicacion en clases que comparten estructura pero difieren en detalles

```typescript
abstract class DataExporter {
  // Metodo template: define el flujo
  async export(): Promise<void> {
    const data = await this.fetchData();
    const formatted = this.format(data);
    await this.write(formatted);
  }

  protected abstract fetchData(): Promise<unknown[]>;
  protected abstract format(data: unknown[]): string;
  protected abstract write(content: string): Promise<void>;
}
```

---

## Anti-patrones a evitar

| Anti-patron | Problema | Solucion |
| :--- | :--- | :--- |
| God Object | Una clase hace demasiado | Separar responsabilidades (SRP) |
| Magic Numbers | Numeros literales sin contexto | Extraer a constantes nombradas |
| Spaghetti Code | Flujo sin estructura ni separacion | Refactorizar con patrones y capas claras |
| Shotgun Surgery | Un cambio obliga a tocar muchos archivos | Cohesion alta, bajo acoplamiento |
| Premature Optimization | Optimizar antes de medir | Primero que funcione, luego que escale |
| Overengineering | Aplicar patrones sin necesidad concreta | Usar el patron mas simple que resuelva el problema |

## Integracion con otros estandares

- Los nombres de clases, metodos e interfaces siguen el skill `code-standards`
- Los repositorios y servicios se ubican en carpetas segun el skill `naming-conventions`
- Los cambios de arquitectura se documentan en `docs/` como Markdown siguiendo el skill `markdown-style`
