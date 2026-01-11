========
Examples
========

Real-world examples demonstrating Pain001 usage.

Example 1: Basic SEPA Payment Processing
=========================================

Create a simple pain.001.001.03 file from a CSV file:

.. code-block:: python

    from pain001 import main

    # Simple SEPA payment file generation
    main(
        xml_message_type='pain.001.001.03',
        xml_template_file_path='sepa_template.xml',
        xsd_schema_file_path='pain.001.001.03.xsd',
        data_file_path='payments.csv'
    )

**CSV Input (payments.csv):**

.. code-block:: text

    InitiatingParty,InitiatingPartyId,PaymentInformationId,DebtorName,DebtorId,DebtorAccountNumber,TransactionId,EndToEndId,Amount,CreditorName,CreditorAccountNumber,RemittanceInfo
    Company XYZ,COMP123,PMT001,Acme Corp,ACME001,DE89370400440532013000,TXN001,E2E001,1000.00,Supplier ABC,DE89370400440532013001,Invoice #001

Example 2: Batch Payment Processing from CSV
==============================================

Process multiple payment files and generate XML outputs:

.. code-block:: python

    from pathlib import Path
    from pain001 import main
    from datetime import datetime
    from pain001.exceptions import ValidationError

    # Define directories
    input_dir = Path('payments_input')
    output_dir = Path('payments_output')
    output_dir.mkdir(exist_ok=True)

    # Process all CSV files
    for csv_file in input_dir.glob('*.csv'):
        try:
            print(f"Processing: {csv_file.name}")

            # Generate output filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = output_dir / f"{csv_file.stem}_{timestamp}.xml"

            # Generate payment file
            main(
                xml_message_type='pain.001.001.03',
                xml_template_file_path='template.xml',
                xsd_schema_file_path='pain.001.001.03.xsd',
                data_file_path=str(csv_file)
            )

            print(f"✅ Generated: {output_file}")

        except ValidationError as e:
            print(f"❌ Validation error in {csv_file.name}: {e}")
            # Log the error and continue with next file
            continue
        except Exception as e:
            print(f"❌ Error processing {csv_file.name}: {e}")
            continue

Example 3: Database-Driven Payment Processing
==============================================

Generate payment files from SQLite database:

.. code-block:: python

    import sqlite3
    from pain001 import main

    # Connect to database
    conn = sqlite3.connect('payments.db')
    cursor = conn.cursor()

    # Query pending payments
    cursor.execute('''
        SELECT * FROM payments
        WHERE status = 'pending'
        AND payment_date <= date('now')
        ORDER BY payment_date
    ''')

    # Generate payment file for pending payments
    main(
        xml_message_type='pain.001.001.03',
        xml_template_file_path='template.xml',
        xsd_schema_file_path='pain.001.001.03.xsd',
        data_file_path='payments.db'
    )

    # Update payment status
    cursor.execute('''
        UPDATE payments
        SET status = 'processed'
        WHERE status = 'pending'
    ''')
    conn.commit()
    conn.close()

Example 4: Multi-Version Support
=================================

Handle different ISO 20022 versions:

.. code-block:: python

    from pain001 import main
    from pain001.exceptions import ValidationError

    versions = {
        'sepa': 'pain.001.001.03',
        'international': 'pain.001.001.04',
        'instant': 'pain.001.001.06',
        'modern': 'pain.001.001.11'
    }

    # Process different payment types with different versions
    payment_configs = [
        ('sepa_payments.csv', versions['sepa'], 'sepa_template.xml'),
        ('international_payments.csv', versions['international'], 'international_template.xml'),
        ('instant_payments.csv', versions['instant'], 'instant_template.xml'),
    ]

    for csv_file, version, template in payment_configs:
        try:
            print(f"Processing {csv_file} with {version}")
            main(
                xml_message_type=version,
                xml_template_file_path=template,
                xsd_schema_file_path=f'{version}.xsd',
                data_file_path=csv_file
            )
            print(f"✅ {version} processed successfully")
        except ValidationError as e:
            print(f"❌ Validation error for {version}: {e}")

Example 5: Error Handling and Logging
=====================================

Robust error handling with detailed logging:

.. code-block:: python

    import logging
    from pain001 import main
    from pain001.exceptions import (
        ValidationError,
        XMLGenerationError,
        SchemaValidationError,
        DataLoadError
    )

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('pain001.log'),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)

    def process_payment_file(csv_path, version, template, schema):
        """Process payment file with comprehensive error handling."""
        try:
            logger.info(f"Starting payment processing for {csv_path}")

            main(
                xml_message_type=version,
                xml_template_file_path=template,
                xsd_schema_file_path=schema,
                data_file_path=csv_path
            )

            logger.info(f"✅ Successfully processed {csv_path}")
            return True

        except DataLoadError as e:
            logger.error(f"Failed to load data from {csv_path}: {e}")
            return False

        except ValidationError as e:
            logger.error(f"Data validation failed: {e}")
            logger.debug(f"Validation details: {e.details}")
            return False

        except XMLGenerationError as e:
            logger.error(f"XML generation failed: {e}")
            return False

        except SchemaValidationError as e:
            logger.error(f"XSD validation failed: {e}")
            logger.debug(f"Schema validation details: {e.details}")
            return False

        except Exception as e:
            logger.exception(f"Unexpected error processing {csv_path}: {e}")
            return False

    # Usage
    success = process_payment_file(
        'payments.csv',
        'pain.001.001.03',
        'template.xml',
        'pain.001.001.03.xsd'
    )

Example 6: Large Batch Processing with Chunking
================================================

Process large CSV files by splitting into chunks:

.. code-block:: python

    import pandas as pd
    from pain001 import main
    from pathlib import Path
    import logging

    logger = logging.getLogger(__name__)

    def process_large_file(csv_path, chunk_size=1000):
        """Process large CSV file in chunks."""
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)

        # Read CSV without loading entire file into memory
        chunks = pd.read_csv(csv_path, chunksize=chunk_size)

        chunk_num = 0
        processed_chunks = 0

        for chunk in chunks:
            chunk_num += 1
            chunk_file = output_dir / f"chunk_{chunk_num}.csv"

            try:
                # Save chunk to temporary file
                chunk.to_csv(chunk_file, index=False)
                logger.info(f"Processing chunk {chunk_num} ({len(chunk)} rows)")

                # Generate payment file for chunk
                main(
                    xml_message_type='pain.001.001.03',
                    xml_template_file_path='template.xml',
                    xsd_schema_file_path='pain.001.001.03.xsd',
                    data_file_path=str(chunk_file)
                )

                processed_chunks += 1
                logger.info(f"✅ Chunk {chunk_num} processed successfully")

            except Exception as e:
                logger.error(f"❌ Error processing chunk {chunk_num}: {e}")
                continue
            finally:
                # Clean up temporary chunk file
                chunk_file.unlink(missing_ok=True)

        logger.info(f"Processing complete: {processed_chunks}/{chunk_num} chunks successful")
        return processed_chunks == chunk_num

    # Usage
    success = process_large_file('large_payments.csv', chunk_size=2000)

Example 7: Payment Amount Validation
====================================

Validate payment amounts before processing:

.. code-block:: python

    import pandas as pd
    from pain001 import main
    import logging

    logger = logging.getLogger(__name__)

    def validate_amounts(csv_path):
        """Validate payment amounts."""
        df = pd.read_csv(csv_path)

        # Check for negative amounts
        negative_amounts = df[df['Amount'] < 0]
        if not negative_amounts.empty:
            logger.warning(f"Found {len(negative_amounts)} negative amounts")
            logger.warning(negative_amounts[['Amount', 'CreditorName']])

        # Check for zero amounts
        zero_amounts = df[df['Amount'] == 0]
        if not zero_amounts.empty:
            logger.warning(f"Found {len(zero_amounts)} zero amounts")

        # Check for unusually large amounts
        threshold = 1000000  # 1 million
        large_amounts = df[df['Amount'] > threshold]
        if not large_amounts.empty:
            logger.warning(f"Found {len(large_amounts)} amounts > {threshold}")
            logger.warning(large_amounts[['Amount', 'CreditorName']])

        return len(df), len(negative_amounts), len(zero_amounts), len(large_amounts)

    # Validate before processing
    total, negative, zero, large = validate_amounts('payments.csv')
    logger.info(f"Validation: Total={total}, Negative={negative}, Zero={zero}, Large={large}")

    if negative > 0 or zero > 0:
        logger.error("Payment amounts contain invalid values. Fix before processing.")
    else:
        main(
            xml_message_type='pain.001.001.03',
            xml_template_file_path='template.xml',
            xsd_schema_file_path='pain.001.001.03.xsd',
            data_file_path='payments.csv'
        )

Example 8: Custom Data Processing Pipeline
==========================================

Build a complete payment processing pipeline:

.. code-block:: python

    from dataclasses import dataclass
    from typing import List
    import logging
    from pain001 import main
    from pain001.exceptions import ValidationError

    logger = logging.getLogger(__name__)

    @dataclass
    class PaymentConfig:
        """Payment processing configuration."""
        csv_path: str
        version: str
        template: str
        schema: str
        output_dir: str

    class PaymentProcessor:
        """Complete payment processing pipeline."""

        def __init__(self, config: PaymentConfig):
            self.config = config

        def validate_input(self) -> bool:
            """Validate input CSV file."""
            try:
                import pandas as pd
                df = pd.read_csv(self.config.csv_path)
                logger.info(f"Input validation: {len(df)} records found")
                return True
            except Exception as e:
                logger.error(f"Input validation failed: {e}")
                return False

        def process(self) -> bool:
            """Process payment file."""
            try:
                if not self.validate_input():
                    return False

                logger.info(f"Processing payments with {self.config.version}")
                main(
                    xml_message_type=self.config.version,
                    xml_template_file_path=self.config.template,
                    xsd_schema_file_path=self.config.schema,
                    data_file_path=self.config.csv_path
                )

                logger.info("✅ Payment processing complete")
                return True

            except ValidationError as e:
                logger.error(f"Validation failed: {e}")
                return False
            except Exception as e:
                logger.error(f"Processing failed: {e}")
                return False

    # Usage
    config = PaymentConfig(
        csv_path='payments.csv',
        version='pain.001.001.03',
        template='template.xml',
        schema='pain.001.001.03.xsd',
        output_dir='output'
    )

    processor = PaymentProcessor(config)
    success = processor.process()

See Also
========

- `Installation Guide <installation.html>`_
- `Usage Guide <usage.html>`_
- `Configuration <configuration.html>`_
- `API Reference <modules.html>`_
