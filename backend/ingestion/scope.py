"""Request-local workspace selection; never mutate global dataset or environment."""
from contextvars import ContextVar
from datetime import date
from pathlib import Path

workspace = ContextVar('workspace', default=None)


def snapshot_date():
    selected = workspace.get()
    return date.fromisoformat(selected['snapshot_date']) if selected else date(2026, 10, 1)


def data_path():
    selected = workspace.get()
    return Path(selected['path']) if selected else None
