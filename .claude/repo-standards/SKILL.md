---
name: repo-standards
description: Estandar obligatorio para creacion, nomenclatura, estructura y flujo de repositorios. Usar al crear repositorios, configurarlos inicialmente, definir ramas, flujos de trabajo o revisar Pull Requests.
---

# Estandar de repositorios

## Nomenclatura

- Nombres en ingles, kebab-case
- Minimo 2 repositorios por proyecto de producto:
  - `project-name-backend`
  - `project-name-frontend`
- Componentes adicionales:
  - `project-name-infra`
  - `project-name-shared-lib`
- Nombres claros y descriptivos, sin abreviaciones ambiguas

Ejemplos validos:

```
billing-platform-backend
billing-platform-frontend
notification-service-backend
admin-dashboard-frontend
```

## Configuracion inicial obligatoria

Todo repositorio debe incluir:

- `README.md` con descripcion, requisitos de entorno y pasos para correr el proyecto
- `.gitignore` adecuado al stack
- Carpeta `standards/` o enlace a los estandares globales
- Estructura base alineada a los estandares de nombres de archivos, carpetas, variables de entorno, testing y documentacion

## Ramas principales

| Rama | Proposito | Regla |
| :--- | :--- | :--- |
| `main` | Codigo estable listo para produccion | Sin push directo, solo via PR |
| `develop` | Integracion de desarrollo previo a release | Sin push directo, solo via PR |

### Reglas de main

- Solo codigo estable y probado
- Merges desde `develop` (release normal) o `hotfix/*` (correcciones criticas)
- Requiere PR + al menos 1 aprobacion de reviewer + tests en verde

### Reglas de develop

- Integracion de todas las funcionalidades antes de pasar a `main`
- Merges desde `feature/*`, `hotfix/*` o `release/*`
- Mismas protecciones que `main`

## Tipos de ramas de trabajo

Todas en kebab-case:

| Tipo | Formato | Origen |
| :--- | :--- | :--- |
| Funcionalidad | `feature/<descripcion>` | `develop` |
| Correccion critica | `hotfix/<descripcion>` | `main` |
| Preparacion de release | `release/<version>` | `develop` |

### Flujo feature

```bash
git checkout develop && git pull
git checkout -b feature/add-user-login
# desarrollar, commits, tests
git push -u origin feature/add-user-login
# crear PR: feature/* -> develop
```

### Flujo hotfix

```bash
git checkout main && git pull
git checkout -b hotfix/fix-payment-bug
# correccion + tests minimos
# PR: hotfix/* -> main
# PR: main -> develop (para sincronizar)
```

### Flujo release

```bash
# desde develop, congelar alcance de version
git checkout -b release/1.3.0
# ajustes menores: versiones, docs, fixes menores
# PR: release/* -> main
# tag en main: v1.3.0
# PR/merge: main -> develop
```

## Flujo estandar (feature completo)

1. Actualizar `develop`: `git checkout develop && git pull`
2. Crear rama: `git checkout -b feature/<nombre>`
3. Desarrollar con commits siguiendo estandar de commits
4. Subir rama: `git push -u origin feature/<nombre>`
5. Crear PR hacia `develop`
6. Esperar revision y aplicar cambios si se solicitan
7. Merge una vez aprobado y con tests en verde
8. Eliminar la rama `feature/*`

## Reglas de Pull Request

- Titulo claro y descriptivo (puede seguir formato de commit principal)
- Descripcion debe incluir: resumen del cambio, modulos afectados y pasos para probarlo
- Asociar a issue/ticket cuando aplique
- Incluir referencia a cambios de base de datos si los hay
- No hacer merge si los tests no pasan o no hay al menos una aprobacion

### Destinos de PR por tipo

| Rama origen | Destino |
| :--- | :--- |
| `feature/*` | `develop` |
| `hotfix/*` | `main` (luego sincronizar `develop`) |
| `release/*` | `main` (luego sincronizar `develop`) |

## Proteccion de ramas

Las ramas `main` y `develop` deben estar protegidas:

- Sin push directo
- Solo merge mediante PR
- Revision obligatoria
- Tests automaticos obligatorios
- Rama actualizada con base antes del merge
- Sin conflictos pendientes
