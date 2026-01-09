.. Pain001 documentation master file, created by
   sphinx-quickstart on Sun May 19 21:59:47 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Pain001's documentation!
===================================

Pain001 is an open-source Python library for automating ISO 20022-compliant payment file creation 
using CSV or SQLite data files. It simplifies the generation of payment initiation files for 
SEPA and international payments.

Features
--------

* **ISO 20022 Compliance**: Generate payment files compliant with pain.001.001.03 through pain.001.001.09
* **Multiple Data Sources**: Support for CSV files, SQLite databases, and Python data structures
* **Automatic Validation**: Built-in XSD schema validation for generated XML files
* **Type Safety**: Full type hints for better IDE support and type checking
* **Secure by Design**: Uses defusedxml to prevent XXE attacks and XML bombs
* **Comprehensive Testing**: 97% test coverage with 150+ tests

Quick Start
-----------

Installation::

    pip install pain001

Basic usage::

    from pain001 import main
    
    main(
        xml_message_type='pain.001.001.03',
        xml_template_file_path='template.xml',
        xsd_schema_file_path='schema.xsd',
        data_file_path='payments.csv'
    )

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
