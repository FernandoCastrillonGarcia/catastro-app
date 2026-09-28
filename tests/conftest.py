import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
FIXTURES = Path(__file__).parent / "fixtures"

from municipios import bogota, medellin  # noqa: E402


@pytest.fixture(autouse=True)
def sin_cache():
    """Los dominios que se piden una vez por sesión no deben pasar de una prueba a otra."""
    bogota.dominios.cache_clear()
    medellin.usos.cache_clear()


@pytest.fixture
def fixture():
    return lambda nombre: json.loads((FIXTURES / nombre).read_text(encoding="utf-8"))


@pytest.fixture
def falso_get(monkeypatch):
    """Reemplaza requests.get y Session.get. Cada respuesta es un dict o lista (el JSON) o una
    excepción, que se lanza. Devuelve la lista de (url, params) de cada llamada."""
    def instalar(*respuestas):
        llamadas, cola = [], list(respuestas)

        def get(url, params=None, timeout=None):
            assert timeout
            llamadas.append((url, params))
            respuesta = cola.pop(0)
            if isinstance(respuesta, Exception):
                raise respuesta
            return SimpleNamespace(json=lambda: respuesta, raise_for_status=lambda: None)

        monkeypatch.setattr(requests, "get", get)
        monkeypatch.setattr(requests.Session, "get",
                            lambda self, url, params=None, timeout=None: get(url, params, timeout))
        return llamadas
    return instalar
