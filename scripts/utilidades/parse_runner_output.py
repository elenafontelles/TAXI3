"""Parse runner output to extract download statistics."""
from dataclasses import dataclass


@dataclass
class RunnerDownloadResult:
    descargadas: int = 0
    ya_leidas: int = 0


def parse_runner_output(output: str) -> RunnerDownloadResult:
    """Parse runner stdout to count downloaded docs and already-read notifications.

    Counts:
    - "Documento guardado en:" as successful downloads (NOT "Acuse guardado en:")
    - "sin contenido descargable" as already-read notifications
    """
    result = RunnerDownloadResult()
    for line in output.splitlines():
        stripped = line.strip()
        if "Documento guardado en:" in stripped:
            result.descargadas += 1
        elif "sin contenido descargable" in stripped:
            result.ya_leidas += 1
    return result
