"""Qlib Studio (qstudio) - Commercial-grade GUI Workstation for Microsoft Qlib."""

from __future__ import annotations

__version__ = "0.1.0"
__app_name__ = "Qlib Studio"


def main() -> int:
    """CLI / GUI entry point for `uv run qstudio`."""
    from main import main as run_app

    return run_app()
