"""The one place allowed to know which corpus adapters exist.

Downstream modules ask for a world by name and receive something
implementing `schema.World`. Keeping the registry here is what lets the
architectural test assert that the compiler, the design contract and the
extractor never name a corpus: they name this module instead, and this
module is upstream of ingestion by definition.

Imports are lazy so that adding a heavyweight adapter never slows the
compiler for someone using a different one.
"""

_REGISTRY = {}


def register(name, loader):
    _REGISTRY[name] = loader


def available():
    return sorted(_REGISTRY)


def get(name):
    if name not in _REGISTRY:
        raise KeyError(f"unknown world {name!r}; available: {available()}")
    return _REGISTRY[name]()


def _odyssey():
    from odyssey_adapter import OdysseyWorld
    return OdysseyWorld()


register("odyssey", _odyssey)

DEFAULT = "odyssey"
