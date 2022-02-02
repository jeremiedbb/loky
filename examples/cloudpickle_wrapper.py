# -*- coding: utf-8 -*-
"""
Serialization of un-picklable objects
=====================================

This example highlights the options for tempering with loky serialization
process.

"""

# Code source: Thomas Moreau
# License: BSD 3 clause

import sys
import time
import traceback
from loky import set_loky_pickler
from loky import get_reusable_executor
from loky import wrap_non_picklable_objects

###############################################################################
# First, define functions which cannot be pickled with the standard ``pickle``
# protocol. They cannot be serialized with ``pickle`` because they are defined
# in the ``__main__`` module. They can however be serialized with
# ``cloudpickle``.
#


def func_async(i, *args):
    return 2 * i


###############################################################################
# With the default behavior, ``loky`` is to use ``cloudpickle`` to serialize
# the objects that are sent to the workers.
#

executor = get_reusable_executor(max_workers=1)
print(executor.submit(func_async, 21).result())


###############################################################################
# For most use-cases, using ``cloudpickle``` is efficient enough. However, this
# solution can be very slow to serialize large python objects, such as dict or
# list, compared to the standard ``pickle`` serialization.
#

# We have to pass an extra argument with a large list (or another large python
# object).
large_list = list(range(1000000))

t_start = time.time()
executor = get_reusable_executor(max_workers=1)
executor.submit(func_async, 21, large_list).result()
print(f"With cloudpickle serialization: {time.time() - t_start:.3f}s")


###############################################################################
# To mitigate this, it is possible to fully rely on ``pickle`` to serialize
# all communications between the main process and the workers. This can be done
# with an environment variable ``LOKY_PICKLER=pickle`` set before the
# script is launched, or with the switch ``set_loky_pickler`` provided in the
# ``loky`` API.
#

# Now set the `loky_pickler` to use the pickle serialization from stdlib. Here,
# we do not pass the desired function ``call_function`` as it is not picklable
# but it is replaced by ``id`` for demonstration purposes.
set_loky_pickler('pickle')
t_start = time.time()
executor = get_reusable_executor(max_workers=1)
executor.submit(id, large_list).result()
print(f"With pickle serialization: {time.time() - t_start:.3f}s")


###############################################################################
# However, the function and objects defined in ``__main__`` are not
# serializable anymore using ``pickle`` and it is not possible to call
# ``func_async`` using this pickler.
#

try:
    executor = get_reusable_executor(max_workers=1)
    executor.submit(func_async, 21, large_list).result()
except Exception:
    traceback.print_exc(file=sys.stdout)


###############################################################################
# ``loky`` provides a wrapper function
# :func:`wrap_non_picklable_objects` to wrap the non-picklable function and
# indicate to the serialization process that this specific function should be
# serialized using ``cloudpickle``. This changes the serialization behavior
# only for this function and keeps using ``pickle`` for all other objects. The
# drawback of this solution is that it modifies the object. This should not
# cause many issues with functions but can have side effects with object
# instances.
#

@wrap_non_picklable_objects
def func_async_wrapped(i, *args):
    return 2 * i


t_start = time.time()
executor = get_reusable_executor(max_workers=1)
executor.submit(func_async_wrapped, 21, large_list).result()
print(f"With default and wrapper: {time.time() - t_start:.3f}s")


###############################################################################
# The same wrapper can also be used for non-picklable classes. Note that the
# side effects of :func:`wrap_non_picklable_objects` on objects can break magic
# methods such as ``__add__`` and can mess up the ``isinstance`` and
# ``issubclass`` functions. Some improvements will be considered if use-cases
# are reported.
#
