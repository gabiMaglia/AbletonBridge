"""Fixtures del composer: perfil real, estructura T02-like y un set de elementos falsos."""
from typing import Dict, Iterable

import pytest

from composer.model import Elemento
from composer.profile import cargar_perfil
from composer.rules import Contexto
from composer.structure import construir_estructura

ROLES_T02 = (
    "kick rumble bass drums top clap stab atmo atmo_trippy lead vox_acid vox_angel choir pad "
    "snare_fill roll roll_32 crash impacto reverse sweep_up sweep_down riser_largo riser_corto"
).split()


def elementos(roles: Iterable[str]) -> Dict[str, Elemento]:
    return {r: Elemento(rol=r, ruta="C:\\pack\\%s.wav" % r) for r in roles}


@pytest.fixture(scope="session")
def perfil():
    return cargar_perfil()


@pytest.fixture()
def ctx_t02(perfil):
    est = construir_estructura(perfil, "t02_like")
    return Contexto(perfil=perfil, estructura=est, elementos=elementos(ROLES_T02), tempo=134.0)


@pytest.fixture()
def make_ctx(perfil):
    """ctx a medida: make_ctx(secciones=[...], roles=[...])."""
    from composer.structure import estructura_desde_secciones

    def _make(secciones, roles=ROLES_T02, tempo=134.0):
        return Contexto(perfil=perfil, estructura=estructura_desde_secciones(secciones),
                        elementos=elementos(roles), tempo=tempo)
    return _make
