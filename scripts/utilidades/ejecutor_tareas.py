"""Task executor utilities for AEAT runner scripts."""
from scripts.utilidades.parse_runner_output import parse_runner_output


def _script_really_succeeded(runner_output: str) -> bool:
    """Determine if a runner script actually succeeded based on its output.

    Returns True if:
    - At least one document was downloaded, OR
    - All notifications were already read (ya_leidas > 0)

    Returns False if:
    - Empty output (crash/no execution)
    - No downloads AND no already-read notifications (real errors)
    """
    result = parse_runner_output(runner_output)

    if result.descargadas > 0:
        return True

    if result.ya_leidas > 0:
        return True

    return False
