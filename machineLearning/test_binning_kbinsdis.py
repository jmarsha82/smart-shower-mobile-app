"""
Compatibility wrapper for the original school-project module name.

The production implementation now lives in ``machineLearning.binning_kbins`` so
pytest does not mistake application logic for a test module.
"""

from machineLearning.binning_kbins import (
    KBinsDiscretizer,
    binning_kbins,
)
