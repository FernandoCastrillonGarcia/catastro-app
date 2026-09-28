"""Evaluación de punta a punta contra los servicios reales: casos_prueba.csv (año) y
casos_variables.csv (código, pisos, uso, tipología y año por ciudad)."""
import csv
import sys

from municipios import MUNICIPIOS
from resumen import resumir


def _filas(ruta):
    with open(ruta, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def evaluar(ruta="casos_prueba.csv"):
    aciertos, filas = 0, _filas(ruta)
    print("| Dirección | Esperado | Obtenido | Lote | Aprox. | OK |\n|---|---|---|---|---|---|")
    for fila in filas:
        esperado, obtenido, lote, aprox = int(fila["anio_esperado"]), None, "-", "-"
        try:
            ficha = MUNICIPIOS[fila["municipio"]]["consultar"](fila["direccion"])
            if ficha:
                lote, aprox = ficha["codigo"], ficha["aproximada"]
                r = resumir(ficha)["anio"]
                obtenido = r["anio"] if r else "sin año"
            else:
                obtenido = "no encontrada"
        except Exception as e:  # noqa: BLE001 - se reporta, no se oculta
            obtenido = f"ERROR {type(e).__name__}: {e}"
        ok = obtenido == esperado
        aciertos += ok
        print(f"| {fila['direccion']} | {esperado} | {obtenido} | {lote} | {aprox} | {'✔' if ok else '✘'} |")
    pct = 100 * aciertos / len(filas)
    print(f"\nAciertos: {aciertos}/{len(filas)} = {pct:.0f} %")
    return pct


def evaluar_variables(ruta="casos_variables.csv"):
    """Una fila acierta si coinciden código, pisos, uso, tipología y año (vacío = sin dato), y si
    hay coordenadas."""
    aciertos, filas = 0, _filas(ruta)
    print("\n| Municipio | Dirección | Diferencias | OK |\n|---|---|---|---|")
    for fila in filas:
        try:
            ficha = MUNICIPIOS[fila["municipio"]]["consultar"](fila["direccion"])
            if ficha is None:
                diferencias = ["no encontrada"]
            else:
                r = resumir(ficha)
                obtenido = {"codigo": ficha["codigo"], "pisos": str(r["pisos"] or ""),
                            "uso": r["uso"] or "", "tipologia": r["tipologia"] or "",
                            "anio": str(r["anio"]["anio"]) if r["anio"] else ""}
                diferencias = [f"{k}: {obtenido[k]!r} ≠ {fila[k]!r}"
                               for k in obtenido if obtenido[k] != fila[k]]
                if r["lat"] is None or r["lon"] is None:
                    diferencias.append("sin coordenadas")
        except Exception as e:  # noqa: BLE001 - se reporta, no se oculta
            diferencias = [f"ERROR {type(e).__name__}: {e}"]
        aciertos += not diferencias
        print(f"| {fila['municipio']} | {fila['direccion']} | {'; '.join(diferencias) or '-'} "
              f"| {'✘' if diferencias else '✔'} |")
    pct = 100 * aciertos / len(filas)
    print(f"\nAciertos: {aciertos}/{len(filas)} = {pct:.0f} %")
    return pct


if __name__ == "__main__":
    sys.exit(0 if min(evaluar(), evaluar_variables()) >= 80 else 1)
