"""Canonical package for the product price prediction and deal finder."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .application import App, DealAgentFramework

__all__ = ["App", "DealAgentFramework"]


def __getattr__(name: str):
    if name in __all__:
        from .application import App, DealAgentFramework

        return {"App": App, "DealAgentFramework": DealAgentFramework}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
