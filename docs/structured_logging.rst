===================
Structured Logging
===================

Pain001 uses structured logging to provide consistent, machine-parsable log output. All log entries are formatted as JSON for easy integration with log aggregation systems.

Overview
========

Structured logging enables:

- **Machine-parsable logs** - JSON format for log aggregation tools
- **Consistent event naming** - Standardized event names across CLI and library
- **Rich context** - Detailed metadata with each log entry
- **PII protection** - Built-in masking for sensitive data
- **Performance tracking** - Duration and timing metrics

Log Format
==========

All log entries follow this JSON structure:

.. code-block:: json

    {
        "event": "process_start",
        "timestamp": 1704987654.123,
        "message_type": "pain.001.001.03",
        "data_source_type": "csv",
        "record_count": 100
    }

Standard Events
===============

Process Lifecycle Events
-------------------------

**process_start**
    Process initialization

    Fields:
        - ``message_type``: ISO 20022 message type
        - ``data_source_type``: csv | sqlite | list | dict
        - ``timestamp``: Unix timestamp

**process_success**
    Successful process completion

    Fields:
        - ``message_type``: ISO 20022 message type
        - ``record_count``: Number of records processed
        - ``duration_ms``: Total processing time in milliseconds

**process_error**
    Process failure

    Fields:
        - ``error_type``: Exception class name
        - ``error_message``: Error description
        - ``message_type``: ISO 20022 message type (if available)

CLI Events
----------

**cli_args_parsed**
    Command line arguments parsed successfully

    Fields:
        - ``message_type``: ISO 20022 message type
        - ``dry_run``: Boolean flag

**cli_dry_run**
    Dry-run validation completed

    Fields:
        - ``message_type``: ISO 20022 message type
        - ``validation_passed``: Boolean result

Validation Events
-----------------

**validation_success**
    Validation passed

    Fields:
        - ``validation_type``: schema | data | business_rules
        - ``message_type``: ISO 20022 message type

**validation_error**
    Validation failed

    Fields:
        - ``validation_type``: schema | data | business_rules
        - ``error_type``: Exception class name
        - ``error_message``: Error description

Data Loading Events
-------------------

**data_load_start**
    Data loading initiated

    Fields:
        - ``data_source_type``: csv | sqlite | list | dict

**data_load_success**
    Data loaded successfully

    Fields:
        - ``data_source_type``: csv | sqlite | list | dict
        - ``record_count``: Number of records loaded
        - ``duration_ms``: Loading time in milliseconds

**data_load_error**
    Data loading failed

    Fields:
        - ``data_source_type``: csv | sqlite | list | dict
        - ``error_type``: Exception class name
        - ``error_message``: Error description

XML Generation Events
---------------------

**xml_generate_start**
    XML generation initiated

    Fields:
        - ``message_type``: ISO 20022 message type
        - ``record_count``: Number of records to process

**xml_generate_success**
    XML generated successfully

    Fields:
        - ``message_type``: ISO 20022 message type
        - ``record_count``: Number of records in XML
        - ``duration_ms``: Generation time in milliseconds

**xml_generate_error**
    XML generation failed

    Fields:
        - ``message_type``: ISO 20022 message type
        - ``error_type``: Exception class name
        - ``error_message``: Error description

XSD Validation Events
---------------------

**xsd_validation_start**
    XSD validation initiated

**xsd_validation_success**
    XSD validation passed

**xsd_validation_error**
    XSD validation failed

    Fields:
        - ``error_type``: Exception class name
        - ``error_message``: Error description

Namespace Events
----------------

**namespace_register**
    XML namespace registration

    Fields:
        - ``message_type``: ISO 20022 message type

Standard Fields
===============

Core Fields
-----------

- ``event``: Event name (always present)
- ``timestamp``: Unix timestamp (always present)
- ``level``: Log level (info, error, etc.)

Identity Fields
---------------

- ``component``: Component name
- ``module``: Python module name
- ``function``: Function name

Message Fields
--------------

- ``message_type``: ISO 20022 message type (e.g., pain.001.001.03)
- ``iso_version``: ISO version number

File Path Fields
----------------

- ``template_path``: XML template file path
- ``schema_path``: XSD schema file path
- ``data_source_type``: csv | sqlite | list | dict

Statistics Fields
-----------------

- ``record_count``: Number of records
- ``transaction_count``: Number of transactions
- ``duration_ms``: Duration in milliseconds
- ``size_bytes``: Size in bytes

Error Fields
------------

- ``error_type``: Exception class name
- ``error_message``: Human-readable error description
- ``error_details``: Additional error context

Validation Fields
-----------------

- ``validation_type``: schema | data | business_rules

Using Structured Logging
=========================

Basic Usage
-----------

.. code-block:: python

    from pain001.logging_schema import (
        log_event,
        Events,
        Fields,
    )
    import logging

    logger = logging.getLogger(__name__)

    # Log a simple event
    log_event(
        logger,
        logging.INFO,
        Events.PROCESS_START,
        message_type="pain.001.001.03",
    )

Process Lifecycle
-----------------

.. code-block:: python

    from pain001.logging_schema import (
        log_process_start,
        log_process_success,
        log_process_error,
    )

    # Start process
    start_time = log_process_start(
        logger,
        "pain.001.001.03",
        "csv",
    )

    try:
        # ... process data ...
        
        # Log success
        log_process_success(
            logger,
            start_time,
            "pain.001.001.03",
            record_count=100,
        )
    except Exception as e:
        # Log error
        log_process_error(
            logger,
            e,
            "pain.001.001.03",
        )
        raise

Validation Logging
------------------

.. code-block:: python

    from pain001.logging_schema import log_validation_event

    try:
        # Perform validation
        validate_schema(data)
        
        # Log success
        log_validation_event(
            logger,
            "schema",
            True,
            message_type="pain.001.001.03",
        )
    except ValidationError as e:
        # Log error
        log_validation_event(
            logger,
            "schema",
            False,
            e,
            message_type="pain.001.001.03",
        )
        raise

PII Protection
==============

Pain001 includes built-in PII masking for sensitive financial data:

.. code-block:: python

    from pain001.logging_schema import mask_sensitive_data

    # Mask IBAN (show first 4 and last 4 characters)
    iban = "GB29NWBK60161331926819"
    masked = mask_sensitive_data(iban, 4)
    # Result: "GB29**************6819"

    # Log with masked data
    log_event(
        logger,
        logging.INFO,
        Events.DATA_LOAD_SUCCESS,
        account=mask_sensitive_data(iban),
    )

**Sensitive Data Guidelines:**

- **IBAN**: Show first 4 + last 4 characters
- **BIC**: Show first 4 + last 2 characters
- **Names**: Use ``<REDACTED>`` for Debtor/Creditor names in INFO logs
- **Amounts**: Use ``<REDACTED>`` in INFO logs
- **Full data**: Only log at DEBUG level with explicit consent

Log Aggregation
===============

Parsing JSON Logs
-----------------

.. code-block:: python

    import json

    # Parse log line
    with open('app.log') as f:
        for line in f:
            entry = json.loads(line)
            if entry['event'] == 'process_error':
                print(f"Error: {entry['error_message']}")

Elasticsearch Integration
-------------------------

JSON logs can be directly ingested into Elasticsearch:

.. code-block:: python

    import logging
    from pythonjsonlogger import jsonlogger

    # Configure JSON logger
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

Splunk Integration
------------------

Forward logs to Splunk with structured fields:

.. code-block:: bash

    # Configure Splunk Universal Forwarder
    [monitor:///var/log/pain001/*.log]
    sourcetype = json
    index = payments

CloudWatch Logs
---------------

.. code-block:: python

    import watchtower
    import logging

    logger = logging.getLogger()
    logger.addHandler(watchtower.CloudWatchLogHandler())

Performance Monitoring
======================

All process events include timing information:

.. code-block:: json

    {
        "event": "process_success",
        "message_type": "pain.001.001.03",
        "record_count": 1000,
        "duration_ms": 450,
        "generation_ms": 320
    }

Use these fields to:

- Track processing performance
- Identify bottlenecks
- Set SLO alerts
- Monitor system health

Example Queries
---------------

**Find slow processes:**

.. code-block:: python

    # Filter logs where duration > 5 seconds
    slow_processes = [
        entry for entry in logs
        if entry.get('duration_ms', 0) > 5000
    ]

**Count errors by type:**

.. code-block:: python

    from collections import Counter
    
    errors = [
        entry['error_type']
        for entry in logs
        if entry.get('event') == 'process_error'
    ]
    
    error_counts = Counter(errors)

Best Practices
==============

1. **Always use structured logging** for programmatic access
2. **Include message_type** in all payment-related events
3. **Mask sensitive data** (IBAN, BIC, names, amounts)
4. **Log durations** for performance monitoring
5. **Use consistent event names** from the Events class
6. **Include error context** for debugging
7. **Log at appropriate levels** (DEBUG for details, INFO for lifecycle, ERROR for failures)

Next Steps
==========

- Review `Usage Guide <usage.html>`_ for integration examples
- Check `Examples <examples.html>`_ for real-world patterns
- See `API Reference <modules.html>`_ for detailed function signatures
