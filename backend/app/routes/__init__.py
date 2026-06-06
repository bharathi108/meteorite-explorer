"""Auto-discover and register route modules that expose a `router` attribute."""

from __future__ import annotations

import importlib
import pkgutil
from typing import List

from fastapi import APIRouter


def discover_routers() -> List[APIRouter]:
    routers: List[APIRouter] = []

    for module_info in pkgutil.iter_modules(__path__):
        if module_info.name.startswith("_"):
            continue

        module = importlib.import_module(f"{__name__}.{module_info.name}")
        router = getattr(module, "router", None)
        if router is not None:
            routers.append(router)

    return routers
