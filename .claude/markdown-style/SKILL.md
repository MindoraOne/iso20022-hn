---
name: markdown-style
description: Estandar obligatorio de escritura y formato en archivos Markdown. Usar siempre al crear o editar archivos .md en cualquier proyecto.
---

# Estilo de Markdown

## Reglas de escritura

- Sin emojis
- Idioma: español
- Usar `-` para listados, nunca `*`
- Sin saltos de linea manuales para envolver parrafos (hard-wrap) a un ancho fijo: cada parrafo u oracion logica va en UNA sola linea y el editor hace el ajuste visual. Los saltos de linea solo separan parrafos o elementos (titulos, listas, tablas, bloques de codigo). Por eso MD013 (longitud de linea) esta desactivado.
- Solo un `#` por archivo (titulo principal), los demas titulos se desglosan como `##`, `###`, etc.
- Si el documento es informativo de una parte mas grande, incluir al inicio el enlace a la documentacion oficial completa

## Matematicas y LaTeX

Usar siempre sintaxis LaTeX para funciones, expresiones, simbolos y operaciones matematicas. Nunca usar caracteres Unicode matematicos directamente (como `≈`, `∑`, `∞`, `α`, `→`).

### Expresiones en linea

Para funciones, variables, simbolos o expresiones dentro de un parrafo, usar `$...$`:

```
La funcion $f(x) = x^2 + 1$ es continua en $\mathbb{R}$.
El error es $\approx 0.01$, con media $\mu$ y desviacion $\sigma$.
El limite cuando $x \to \infty$ converge a $L$.
```

### Bloques de ecuaciones

Para ecuaciones completas o desarrollos que ocupan su propia linea, usar `$$...$$`:

```
$$
f(x) = \frac{1}{\sigma\sqrt{2\pi}} e^{-\frac{(x-\mu)^2}{2\sigma^2}}
$$
```

### Ejemplos de reemplazo obligatorio

| No usar | Usar en su lugar |
| :--- | :--- |
| `≈` | `$\approx$` |
| `∑` | `$\sum$` |
| `∞` | `$\infty$` |
| `α`, `β`, `γ` | `$\alpha$`, `$\beta$`, `$\gamma$` |
| `→` | `$\to$` o `$\rightarrow$` |
| `≤`, `≥` | `$\leq$`, `$\geq$` |
| `×` (multiplicacion) | `$\times$` |
| `√` | `$\sqrt{x}$` |

## Configuracion de linter (.markdownlint.json)

Todo proyecto debe incluir un `.markdownlint.json` en la raiz con las siguientes reglas base:

```json
{
  "MD013": false,
  "MD024": false,
  "MD029": false,
  "MD033": false,
  "MD034": false,
  "MD036": false,
  "MD060": false
}
```

| Regla | Que desactiva |
| :--- | :--- |
| MD013 | Limite de longitud de linea |
| MD024 | Titulos duplicados en el mismo documento |
| MD029 | Numeracion ordenada en listas numeradas |
| MD033 | HTML inline en Markdown |
| MD034 | URLs sin formato de enlace |
| MD036 | Enfasis usado como encabezado |

En un repositorio con CI esta configuracion SE VERSIONA: el runner hace checkout limpio y necesita las reglas en el repo (de lo contrario `markdownlint` falla con ENOENT). Por el mismo motivo, NO usar `extends` hacia un archivo ignorado por `.gitignore`. Si se quiere overrides puramente locales, hacerlo en un archivo aparte sin afectar la config compartida que valida el CI.
