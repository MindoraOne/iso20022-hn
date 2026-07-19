---
name: commits-versioning
description: Estandar obligatorio de commits, branching y versionado semantico para todos los proyectos. Usar siempre al crear commits, ramas, tags, releases o revisar Pull Requests.
---

# Estandar de commits y versionado

Al crear commits, ramas, tags o revisar PRs, seguir siempre estas convenciones.

## Formato de commit

Seguir Conventional Commits:

```
<tipo>[alcance opcional]: <descripcion breve>

[body opcional]

[footer opcional]
```

- El tipo y la descripcion son obligatorios
- El alcance indica el modulo o area afectada
- El body detalla que se hizo y por que
- El footer referencia issues o declara breaking changes

## Tipos de commit

| Tipo | Cuando usar |
| :--- | :--- |
| `feat` | Nueva funcionalidad |
| `fix` | Correccion de bug existente |
| `chore` | Mantenimiento que no afecta produccion (dependencias, config) |
| `docs` | Cambios en documentacion, READMEs, comentarios |
| `style` | Formato o estilo sin cambios de logica |
| `refactor` | Cambio de estructura sin modificar funcionalidad |
| `test` | Agregar o modificar tests, fixtures, mocks |
| `perf` | Optimizaciones de rendimiento |
| `ci` | Cambios en pipelines, workflows, scripts CI/CD |
| `build` | Cambios en build, compilacion o dependencias |
| `revert` | Revertir un commit anterior |

## Reglas de descripcion

- Breve e imperativa: responde a "que hace este cambio"
- Consistente en el proyecto: ingles o espanol, no mezclar
- Sin punto final

## Ejemplos

```bash
feat(auth): add Google OAuth login

Implemented Google OAuth for user authentication.
Updated login controller and added new routes.

Closes #23
```

```bash
fix(payment): corregir calculo de impuestos

Se ajusto calculateTax para usar el porcentaje correcto
segun la ubicacion del usuario.
```

```bash
BREAKING CHANGE: remove legacy API endpoints

Refs #45
```

## Branching

| Rama | Proposito |
| :--- | :--- |
| `main` / `master` | Codigo estable, listo para produccion |
| `develop` | Integracion de desarrollo, previo a release |
| `feature/<nombre>` | Nueva funcionalidad en desarrollo |
| `hotfix/<nombre>` | Correccion rapida sobre produccion |
| `release/<version>` | Preparacion de release |

- Nombre en kebab-case: `feature/login-oauth`
- Merge hacia `develop` o `main` segun flujo del proyecto

## Versionado semantico

Formato: `v<major>.<minor>.<patch>`

| Cambio | Incremento |
| :--- | :--- |
| Breaking change | major: `1.x.x` a `2.0.0` |
| Nueva funcionalidad compatible | minor: `1.2.x` a `1.3.0` |
| Correccion de bug | patch: `1.2.3` a `1.2.4` |

## Tags y releases

- Etiquetar cada release con `v<semver>`
- El tag debe coincidir con la version publicada
- Release notes incluyen: `feat`, `fix` y `perf` del periodo

## Checklist antes de merge (PR)

- [ ] Descripcion clara del cambio
- [ ] Referencias a issues o tickets
- [ ] Tests agregados o actualizados segun corresponda
- [ ] Codigo revisado y aprobado por al menos un reviewer
- [ ] Cumple con estandares de commits y branching
