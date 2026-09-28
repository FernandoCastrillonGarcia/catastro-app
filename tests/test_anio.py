from anio import elegir_anio


def test_varias_construcciones():
    r = elegir_anio([(2012, 51.6), (1984, 204.6)])
    assert r == {"anio": 1984, "detalle": [(1984, 204.6), (2012, 51.6)]}


def test_ampliacion_pequena_no_desplaza():
    r = elegir_anio([(1971, 57.02), (1971, 37.32), (1971, 133.83), (2021, 11.52),
                     (1971, 143.48), (1971, 629.26)])
    assert r["anio"] == 1971
    assert r["detalle"] == [(1971, 1000.91), (2021, 11.52)]


def test_sin_anio():
    assert elegir_anio([]) is None
    assert elegir_anio([(None, 0)]) is None


def test_empate_gana_mas_antiguo():
    assert elegir_anio([(2000, 50), (1990, 50)])["anio"] == 1990
