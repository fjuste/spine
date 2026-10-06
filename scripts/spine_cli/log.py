"""Installer progress lines and counters."""

from __future__ import annotations

import sys


class Log:
    """Prints ``+`` / ``=`` / ``!`` lines and counts conflicts.

    Args:
        dry_run: When True, mutating messages are prefixed with ``[DRY-RUN]``.
    """

    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run
        self.linked = 0
        self.skipped = 0
        self.conflicts = 0
        self.warnings = 0
        self.cleaned = 0

    def plus(self, message: str) -> None:
        """Record a created or removed artefact."""
        self.linked += 1
        print(f"  + {message}")

    def skip(self, message: str) -> None:
        """Record an artefact that was already correct."""
        self.skipped += 1
        print(f"  = {message}")

    def warn(self, message: str) -> None:
        """Record a warning."""
        self.warnings += 1
        print(f"  ! {message}")

    def conflict(self, message: str) -> None:
        """Record a conflict that ``--force`` can replace."""
        self.conflicts += 1
        print(f"  x {message}", file=sys.stderr)

    def info(self, message: str) -> None:
        """Print a note that does not change counters."""
        print(f"  i {message}")

    def dry(self, message: str) -> None:
        """Print a dry-run preview line."""
        print(f"  [DRY-RUN] {message}")


class SpineExit(Exception):
    """Stop the CLI with a process exit code.

    Args:
        code: Process exit code. ``3`` is a mode conflict.
        message: Optional text already suitable for stderr.
    """

    def __init__(self, code: int, message: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def die(message: str, code: int = 1) -> None:
    """Print ``message`` to stderr and raise ``SpineExit``.

    Args:
        message: Error text. A leading ``ERROR:`` is added when missing.
        code: Process exit code.

    Raises:
        SpineExit: Always.
    """
    text = message if message.startswith("ERROR:") else f"ERROR: {message}"
    print(text, file=sys.stderr)
    raise SpineExit(code, text)
