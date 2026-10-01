#!/usr/bin/env python3
"""Descarga los informes del Sistema de Información de Listas de Espera (SISLE-SNS).

Fuente REAL (verificada 2026-10-01):
  Ministerio de Sanidad — Portal Estadístico del SNS
  https://www.sanidad.gob.es/estadEstudios/estadisticas/inforRecopilaciones/listaEspera.htm
  Publicación semestral (cortes 31-dic y 30-jun según RD 605/2003), formato PDF
  (NO hay XLS/CSV oficial de esta serie; el Ministerio publica los informes en PDF).

Se descargan, por periodo:
  - Informe nacional "Indicadores resumen" (LISTAS_PUBLICACION_*)
  - Informe "Datos por comunidades autónomas" (Datos_ccaa_*) — solo referencia
  - dic2025: versión RECTIFICADA (rectificación de datos de Castilla-La Mancha,
    publicada 24-09-2026) + nota aclaratoria

También descarga población por CCAA del INE (Censo anual de población, tabla
jaxiT3 67988, CSV) para el cálculo derivado pacientes/1.000 hab.

Todo se cachea en raw/: reejecutar no re-descarga. Sin claves ni APIs privadas.
"""
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "raw"
BASE = "https://www.sanidad.gob.es/estadEstudios/estadisticas/inforRecopilaciones/docs"
INE = "https://ine.es/jaxiT3/files/t/es/csv_bd/67988.csv"
UA = {"User-Agent": "espera-sanidad/1.0 (observatorio IAcademy)"}

# (periodo, fichero nacional, fichero CCAA)
REPORTS = [
    ("dic2025", "LISTAS_PUBLICACION_Dic_2025_rectificado.pdf", "Datos_ccaa_dic2025_rectificado.pdf"),
    ("jun2025", "LISTAS_PUBLICACION_jun25.pdf", "Datos_ccaa_jun2025.pdf"),
    ("dic2024", "LISTAS_PUBLICACION_dic2024.pdf", "Datos_ccaa_dic2024.pdf"),
    ("jun2024", "LISTAS_PUBLICACION_jun2024.pdf", "Datos_ccaa_jun2024.pdf"),
    ("dic2023", "LISTAS_PUBLICACION_dic2023.pdf", "Datos_ccaa_dic2023.pdf"),
    ("jun2023", "LISTAS_PUBLICACION_jun2023.pdf", "Datos_ccaa_jun2023.pdf"),
    ("dic2022", "LISTAS_PUBLICACION_dic_2022.pdf", "Datos_ccaa_dic2022.pdf"),
    ("jun2022", "LISTAS_PUBLICACION_jun2022.pdf", "Datos_ccaa_jun2022.pdf"),
]
EXTRA = ["Nota_Aclaratoria_Rectificacion_Dic_2025.pdf"]


def get(url: str, dst: Path) -> str:
    if dst.exists() and dst.stat().st_size > 1000:
        return "cache"
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                dst.write_bytes(r.read())
            return "ok" if dst.stat().st_size > 1000 else "vacio"
        except Exception as e:  # red
            if attempt == 2:
                dst.with_suffix(dst.suffix + ".err").write_text(f"{e}\n")
                return "error"
            time.sleep(2 * (attempt + 1))
    return "error"


def main() -> None:
    sile = RAW / "sile"
    ine = RAW / "ine"
    sile.mkdir(parents=True, exist_ok=True)
    ine.mkdir(parents=True, exist_ok=True)
    ok = cache = err = 0
    for periodo, nacional, ccaa in REPORTS:
        for f in (nacional, ccaa):
            st = get(f"{BASE}/{f}", sile / f)
            ok += st == "ok"; cache += st == "cache"; err += st in ("error", "vacio")
            print(f"{periodo} {f}: {st}")
    for f in EXTRA:
        st = get(f"{BASE}/{f}", sile / f)
        ok += st == "ok"; cache += st == "cache"; err += st in ("error", "vacio")
        print(f"{f}: {st}")
    st = get(INE, ine / "censo_anual_67988.csv")
    ok += st == "ok"; cache += st == "cache"; err += st in ("error", "vacio")
    print(f"INE censo anual 67988: {st}")
    print(f"descargados={ok} cache={cache} errores={err}")


if __name__ == "__main__":
    main()
