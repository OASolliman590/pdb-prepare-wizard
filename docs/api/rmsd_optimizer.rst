RMSD Optimizer
==============

Optimized RMSD calculations with triangular matrix storage.

.. automodule:: rmsd_optimizer
   :members:
   :undoc-members:
   :show-inheritance:

Quick Start
-----------

.. code-block:: python

   from rmsd_optimizer import CachedRMSDCalculator
   import numpy as np

   # Prepare poses
   poses = [np.random.rand(50, 3) for _ in range(100)]

   # Calculate with caching
   calculator = CachedRMSDCalculator()
   rmsd_matrix = calculator.calculate_rmsd_optimized(
       poses_data=poses,
       use_cache=True,
       cache_key="my_poses"
   )

   # Check memory savings
   stats = rmsd_matrix.get_memory_usage()
   print(f"Saved {stats['savings_percent']:.1f}%")

Main Classes
------------

.. autoclass:: rmsd_optimizer.TriangularRMSDMatrix
   :members:
   :undoc-members:

.. autoclass:: rmsd_optimizer.CachedRMSDCalculator
   :members:
   :undoc-members:
