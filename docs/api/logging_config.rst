Logging System
==============

Standardized logging with colors and progress tracking.

.. automodule:: logging_config
   :members:
   :undoc-members:
   :show-inheritance:

Quick Start
-----------

.. code-block:: python

   from logging_config import setup_logger, log_section, LogTimer

   # Setup logger
   logger = setup_logger(level="INFO")

   # Log section
   log_section("Pipeline Initialization", logger)
   logger.info("Starting analysis")

   # Timed operation
   with LogTimer("Heavy computation", logger):
       process_data()

Main Classes
------------

.. autoclass:: logging_config.PipelineLogger
   :members:
   :undoc-members:

.. autoclass:: logging_config.LogTimer
   :members:
   :undoc-members:

Convenience Functions
---------------------

.. autofunction:: logging_config.setup_logger
.. autofunction:: logging_config.get_logger
.. autofunction:: logging_config.log_section
.. autofunction:: logging_config.log_step
