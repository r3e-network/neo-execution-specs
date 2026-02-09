"""OpCode instruction implementations.

The execution engine imports submodules directly (e.g. ``from neo.vm.instructions
import constants, stack``), so this package primarily serves as a namespace.
"""

from neo.vm.instructions import (  # noqa: F401 — re-exported submodules
    constants,
    stack,
    numeric,
)
