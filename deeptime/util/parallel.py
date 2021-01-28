import os
from typing import Optional


def handle_n_jobs(value: Optional[int]) -> int:
    r"""Handles the n_jobs parameter consistently so that a non-negative number is returned.
    In particular, if

      * value is None, use 1 job
      * value is negative, use number cores available * 2
      * value is positive, use value

    Parameters
    ----------
    value : int or None
        The provided n_jobs argument

    Returns
    -------
    n_jobs : int
        A non-negative integer value describing how many threads can be started simultaneously.
    """
    if value is None:
        import psutil
        count = psutil.cpu_count(logical=True)
        if count is None:
            raise ValueError("Could not determine number of cpus in system, please provide n_jobs manually.")
        return os.cpu_count() * 2
    elif value <= 0:
        raise ValueError(f"n_jobs can only be None (in which case it will be determined from hardware) "
                         f"or a positive number, but was {value}.")
    assert isinstance(value, int) and value > 0
    return value
