from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class IntegrationStatus:
    name: str
    enabled: bool
    configured: bool
    details: str = ""


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)
