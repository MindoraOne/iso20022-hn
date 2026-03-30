# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""Internationalisation — human-readable texts per language.

Keys must match the values in message-codes.json — not the constant names.
The field 'message' in API responses is informational/debug only.
The field 'code' is what the frontend uses to look up text in its own i18n dict.

To add a new message:
  1. Add the value key to message-codes.json under the correct category.
  2. Add the same key to every language dict here.

To add a new language:
  1. Add a new top-level key with the ISO 639-1 code.
  2. Translate all existing keys — missing keys fall back to English.
"""

from __future__ import annotations

_MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        # success — payment
        "health_ok":           "Service is running",
        "templates_listed":    "Templates retrieved successfully",
        "xml_generated":       "XML generated successfully",
        # error — payment
        "template_not_found":  "Template not found",
        "generation_failed":   "XML generation failed",
        "xsd_invalid":         "Generated XML failed XSD validation",
        "csv_invalid":         "CSV validation failed",
        # error — fields
        "invalid_file_type":   "Only CSV files are accepted",
        "file_too_large":      "File exceeds the maximum allowed size",
        "file_read_error":     "Could not read the uploaded file",
        # error — generic
        "rate_limit_exceeded": "Too many requests — please try again later",
        "internal_error":      "An unexpected error occurred",
    },
    "es": {
        # success — payment
        "health_ok":           "El servicio está en funcionamiento",
        "templates_listed":    "Plantillas obtenidas correctamente",
        "xml_generated":       "XML generado correctamente",
        # error — payment
        "template_not_found":  "Plantilla no encontrada",
        "generation_failed":   "La generación del XML falló",
        "xsd_invalid":         "El XML generado no pasó la validación XSD",
        "csv_invalid":         "La validación del CSV falló",
        # error — fields
        "invalid_file_type":   "Solo se aceptan archivos CSV",
        "file_too_large":      "El archivo supera el tamaño máximo permitido",
        "file_read_error":     "No se pudo leer el archivo enviado",
        # error — generic
        "rate_limit_exceeded": "Demasiadas solicitudes — intente de nuevo más tarde",
        "internal_error":      "Ocurrió un error inesperado",
    },
}

DEFAULT_LANG = "en"


def msg(code: str, lang: str = DEFAULT_LANG) -> str:
    """Resolve a message code value to its human-readable debug string.

    The returned string is for logging/debug purposes only.
    The frontend uses the 'code' field to look up text in its own dict.

    Falls back to English when the requested language is unavailable.
    Falls back to the raw code string when the key is missing in all languages.

    Args:
        code: Value from message-codes.json (e.g. 'xml_generated').
        lang: ISO 639-1 language code (e.g. 'en', 'es').

    Returns:
        Human-readable message string.
    """
    return (
        _MESSAGES.get(lang, _MESSAGES[DEFAULT_LANG]).get(code)
        or _MESSAGES[DEFAULT_LANG].get(code)
        or code
    )