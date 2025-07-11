
"""Very simplified stress-VaR to check capital reserve."""
import numpy as np
from .utils import load_cfg

cfg = load_cfg()
_RESERVE = cfg["risk"]["capital_reserve"]

def check(price_series):
    var99 = np.percentile(price_series, 1)
    required = abs(price_series[-1] - var99) * 1000
    return required <= _RESERVE
