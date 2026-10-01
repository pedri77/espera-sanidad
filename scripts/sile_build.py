#!/usr/bin/env python3
"""Construye los agregados del observatorio desde los PDF del SISLE-SNS (raw/sile).

Entrada: 8 informes nacionales (jun2022 .. dic2025 rectificado) + INE censo anual.
Salida (data/):
  sile_quirurgica_nacional.json   — serie semestral nacional (pacientes, días, %>6m) y por especialidad
  sile_quirurgica_ccaa.json       — último periodo por CCAA + serie de tiempo medio por CCAA
  sile_consultas_externas.json    — consulta externa, último periodo (nacional + CCAA), si existe
  sources.json                    — catálogo de fuentes

Método: pdftotext -layout y parseo de las tablas:
  1. "Distribución por especialidades" (nacional): 7 columnas numéricas por especialidad.
  2. "Distribución por comunidades autónomas" (resumen CCAA): 4 o 5 columnas numéricas.
  3. Consulta externa: tabla de "especialidades básicas" (nacional) y resumen CCAA.
Validación dura: el TOTAL nacional parseado debe cuadrar fila a fila; los periodos
con parseo fallido se descartan y se registran en data/*/descartes.
"""
import json
import re
import subprocess
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "raw" / "sile"
INE = REPO / "raw" / "ine" / "censo_anual_67988.csv"
DATA = REPO / "data"

PERIODOS = [  # (clave, fichero nacional, etiqueta corte, fecha corte)
    ("dic2025", "LISTAS_PUBLICACION_Dic_2025_rectificado.pdf", "31/12/2025", "2025-12-31"),
    ("jun2025", "LISTAS_PUBLICACION_jun25.pdf", "30/06/2025", "2025-06-30"),
    ("dic2024", "LISTAS_PUBLICACION_dic2024.pdf", "31/12/2024", "2024-12-31"),
    ("jun2024", "LISTAS_PUBLICACION_jun2024.pdf", "30/06/2024", "2024-06-30"),
    ("dic2023", "LISTAS_PUBLICACION_dic2023.pdf", "31/12/2023", "2023-12-31"),
    ("jun2023", "LISTAS_PUBLICACION_jun2023.pdf", "30/06/2023", "2023-06-30"),
    ("dic2022", "LISTAS_PUBLICACION_dic_2022.pdf", "31/12/2022", "2022-12-31"),
    ("jun2022", "LISTAS_PUBLICACION_jun2022.pdf", "30/06/2022", "2022-06-30"),
]
URL_DOC = "https://www.sanidad.gob.es/estadEstudios/estadisticas/inforRecopilaciones/listaEspera.htm"

ESPECIALIDADES = [
    "Cirugía General y de Digestivo", "Ginecología", "Oftalmología", "ORL",
    "Traumatología", "Urología", "Cirugía Cardiaca", "Angiología /Cir. Vascular",
    "Cirugía Maxilofacial", "Cirugía Pediátrica", "Cirugía Plástica",
    "Cirugía Torácica", "Neurocirugía", "Dermatología",
]
CCAA = ["ANDALUCÍA", "ARAGON", "PDO DE ASTURIAS", "BALEARES", "CANARIAS", "CANTABRIA",
        "CASTILLA Y LEON", "CASTILLA-LA MANCHA", "CATALUÑA", "COMUNIDAD VALENCIANA",
        "EXTREMADURA", "GALICIA", "MADRID", "MURCIA", "C. FORAL DE NAVARRA",
        "PAÍS VASCO", "RIOJA", "CEUTA", "MELILLA"]
INE_MAP = {  # nombre SILE -> código INE censo (67988)
    "ANDALUCÍA": "01", "ARAGON": "02", "PDO DE ASTURIAS": "03", "BALEARES": "04",
    "CANARIAS": "05", "CANTABRIA": "06", "CASTILLA Y LEON": "07",
    "CASTILLA-LA MANCHA": "08", "CATALUÑA": "09", "COMUNIDAD VALENCIANA": "10",
    "EXTREMADURA": "11", "GALICIA": "12", "MADRID": "13", "MURCIA": "14",
    "C. FORAL DE NAVARRA": "15", "PAÍS VASCO": "16", "RIOJA": "17",
    "CEUTA": "18", "MELILLA": "19",
}


def txt(pdf: Path) -> str:
    return subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                          capture_output=True, text=True, check=True).stdout


def num(s: str) -> float:
    s = s.strip().replace(".", "").replace(",", ".")
    return float(s) if s not in ("-", "") else None


TOK = re.compile(r"-?\d[\d.]*,\d+|-?\d[\d.]*|-")


def _fila(toks: list[str]) -> dict | None:
    """Columnas por posición semántica: pacientes=1er token; tasa y %>6m = los
    dos primeros tokens con decimales (coma); días = penúltimo token (a veces
    decimal, p.ej. el TOTAL de jun2025). Soporta 6 columnas (ediciones dic,
    sin 'diferencia con junio') y 7 (ediciones jun)."""
    toks = [t for t in toks if t != "-"]
    dec = [t for t in toks if "," in t]
    if len(dec) < 2 or len(toks) < 5:
        return None
    try:
        return {"pacientes_en_espera": num(toks[0]),
                "tasa_por_1000_hab": num(dec[0]),
                "pct_mas_6_meses": num(dec[1]),
                "tiempo_medio_dias": num(toks[-2])}
    except ValueError:
        return None

def parse_especialidades(text: str) -> tuple[dict, dict]:
    """Tabla nacional: nombre + [pacientes, dif_dic, dif_jun, tasa, %>6m, días, dif_días]."""
    esp, total = {}, {}
    in_tabla = False
    for line in text.splitlines():
        u = unicodedata.normalize("NFC", line)
        if re.search(r"SITUACIÓN DE LA LISTA DE ESPERA QUIRÚRGICA", u):
            in_tabla = True
        if "procesos seleccionados" in u.lower() and in_tabla and len(esp) >= 10:
            break
        if not in_tabla:
            continue
        for e in ESPECIALIDADES:
            if u.strip().startswith(e):
                f = _fila(TOK.findall(u))
                if f:
                    esp[e] = f
        if re.match(r"^\s*TOTAL\b", u):
            f = _fila(TOK.findall(u))
            if f:
                total = f
    return esp, total


def parse_ccaa_resumen(text: str) -> dict:
    """Tabla resumen LEQ por CCAA ('Total de pacientes pendientes').
    5 tokens: total, tasa, n>6m, %>6m, días (informes recientes)
    4 tokens: total, tasa, %>6m, días (informes 2022-2023, sin recuento >6m).
    Se toman por orden de documento las primeras 19 filas válidas (la tabla LEQ
    precede a la de consulta externa); las tablas por especialidad (~15 columnas)
    quedan excluidas por el número de tokens."""
    out = {}
    for line in text.splitlines():
        u = unicodedata.normalize("NFC", line)
        m = re.match(r"^\s*(" + "|".join(CCAA) + r")\b\s+(-?\d.*)$", u)
        if not m or m.group(1) in out:
            continue
        toks = re.findall(r"-?\d[\d.]*,\d+|-?\d[\d.]*|-",
                          m.group(2).split("SNS:")[0])  # recorta nota lateral 'SNS: ...'
        if len(toks) == 5:
            out[m.group(1)] = {"pacientes_en_espera": num(toks[0]),
                               "tasa_por_1000_hab_sile": num(toks[1]),
                               "pacientes_mas_6_meses": num(toks[2]),
                               "pct_mas_6_meses": num(toks[3]),
                               "tiempo_medio_dias": num(toks[4])}
        elif len(toks) == 4:
            out[m.group(1)] = {"pacientes_en_espera": num(toks[0]),
                               "tasa_por_1000_hab_sile": num(toks[1]),
                               "pacientes_mas_6_meses": None,
                               "pct_mas_6_meses": num(toks[2]),
                               "tiempo_medio_dias": num(toks[3])}
        if len(out) == 19:
            break
    return out



def parse_consulta_externa(text: str) -> tuple[dict, dict]:
    """Resumen CCAA de lista de espera de consultas (tasa, días, % citas >60 días)
    y fila TOTAL nacional. El informe NO publica recuento de pacientes por CCAA
    en esta tabla, solo la tasa — así se recoge."""
    idx = text.find("LISTA DE ESPERA DE CONSULTAS")
    if idx < 0:
        return {}, {}
    total, ccaa = {}, {}
    for line in text[idx:].splitlines():
        u = unicodedata.normalize("NFC", line)
        m = re.match(r"^\s*(" + "|".join(CCAA) + r")\b\s+(-?\d.*)$", u)
        t = re.match(r"^\s*TOTAL\b\s+(-?\d.*)$", u)
        rest = None
        if t:
            rest = t.group(1)
        elif m and m.group(1) not in ccaa:
            rest = m.group(2)
        if rest is None:
            continue
        toks = re.findall(r"-?\d[\d.]*,\d+|-?\d[\d.]*", rest.split("SNS:")[0])
        if len(toks) != 3:
            continue
        reg = {"tasa_por_1000_hab": num(toks[0]),
               "tiempo_medio_dias": num(toks[1]),
               "pct_citas_mas_60_dias": num(toks[2])}
        if t:
            total.update(reg)
        else:
            ccaa[m.group(1)] = reg
        if len(ccaa) == 19 and total:
            break
    return total, ccaa



def pob_ine() -> dict:
    """Censo anual INE (tabla 67988): {codigo_ccaa: {año: población}}."""
    out = {}
    for line in INE.read_text(encoding="utf-8-sig").splitlines()[1:]:
        p = line.split("\t")
        if len(p) < 6 or p[3] != "Total" or p[2] != "":  # solo filas CCAA (sin provincia)
            continue
        cod = p[1][:2]
        if re.match(r"^\d{2}$", cod):
            out.setdefault(cod, {})[p[4]] = num(p[5])
    return out


META = lambda fuente, periodo, url, extra=None: {"meta": {
    "source": fuente, "period": periodo, "url": url, **(extra or {})}}


def main() -> None:
    DATA.mkdir(exist_ok=True)
    pob = pob_ine()
    descartes = []
    serie_nacional, serie_esp, serie_ccaa_dias, serie_ccaa_pac = [], {}, {}, {}
    ultimo = None

    for clave, fich, corte, iso in PERIODOS:
        path = RAW / fich
        if not path.exists():
            descartes.append({"periodo": clave, "motivo": f"PDF no descargado: {fich}"})
            continue
        text = txt(path)
        esp, total = parse_especialidades(text)
        ccaa = parse_ccaa_resumen(text)
        if not total or not esp:
            descartes.append({"periodo": clave, "motivo": "no se pudo parsear la tabla nacional"})
            continue
        vals = [v for v in esp.values() if v["pacientes_en_espera"] is not None]
        if len(vals) != len(esp):
            print(f"  AVISO {clave}: {len(esp)-len(vals)} especialidad(es) con celdas '-' (sin cifra)")
        suma = sum(v["pacientes_en_espera"] for v in vals)
        if abs(suma - total["pacientes_en_espera"]) > 1:  # tolerancia redondeo
            descartes.append({"periodo": clave,
                              "motivo": f"suma especialidades {suma:.0f} != TOTAL {total['pacientes_en_espera']:.0f}"})
            continue
        if len(ccaa) < 19:
            descartes.append({"periodo": clave,
                              "motivo": f"tabla CCAA incompleta: {len(ccaa)}/19 filas parseadas"})
        año = iso[:4]
        reg = {"periodo": clave, "fecha_corte": iso,
               **total, "suma_check_especialidades": round(suma),
               "n_especialidades": len(esp), "n_ccaa": len(ccaa)}
        serie_nacional.append(reg)
        for e, v in esp.items():
            serie_esp.setdefault(e, []).append({"periodo": clave, **v})
        for c, v in ccaa.items():
            serie_ccaa_dias.setdefault(c, []).append({"periodo": clave, "dias": v["tiempo_medio_dias"]})
            serie_ccaa_pac.setdefault(c, []).append({"periodo": clave, "pacientes": v["pacientes_en_espera"]})

        # --- consulta externa (último periodo) ---
        if clave == "dic2025":
            ce_total, ce_ccaa = parse_consulta_externa(text)
            if ce_total and len(ce_ccaa) == 19:
                out3 = META("Ministerio de Sanidad — SISLE-SNS, lista de espera de consultas externas",
                            "31/12/2025", URL_DOC,
                            {"unit": "pacientes/1.000 hab; días; %",
                             "nota": "el informe no publica recuento de pacientes por CCAA en esta "
                                     "tabla, solo tasa por 1.000 hab; '% citas >60 días' incluye "
                                     "pacientes sin cita asignada >60 días (cambio de criterio "
                                     "documentado en el propio informe)"})
                out3["total_nacional"] = ce_total
                out3["ccaa"] = ce_ccaa
                (DATA / "sile_consultas_externas.json").write_text(
                    json.dumps(out3, ensure_ascii=False, indent=1))
            else:
                descartes.append({"periodo": clave,
                                  "motivo": f"consulta externa incompleta: {len(ce_ccaa)}/19 CCAA"})
            ultimo = {"ccaa": ccaa, "esp": esp, "total": total}


    # --- nacional ---
    out = META("Ministerio de Sanidad — SISLE-SNS, informes semestrales (RD 605/2003)",
               "jun2022 – dic2025 (8 semestres)", URL_DOC,
               {"unit": "pacientes; días; %", "provisional": False,
                "nota": "dic2025 es la versión RECTIFICADA (CLM) de 24-09-2026"})
    out["serie"] = serie_nacional
    out["por_especialidad"] = serie_esp
    out["descartes"] = descartes
    (DATA / "sile_quirurgica_nacional.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))

    # --- CCAA último periodo + series + derivado INE ---
    if ultimo:
        ccaa_out = {}
        for c, v in ultimo["ccaa"].items():
            cod = INE_MAP.get(c)
            pob_año = pob.get(cod, {}).get("2025")
            reg = {
                **v,
                "pacientes_por_1000_hab_ine": (round(v["pacientes_en_espera"] / pob_año * 1000, 2)
                                               if v["pacientes_en_espera"] and pob_año else None),
                "poblacion_ine_2025": pob_año,
            }
            ccaa_out[c] = reg
        out2 = META("Ministerio de Sanidad — SISLE-SNS dic2025 (rectificado); INE Censo anual 2025 (tabla 67988)",
                    "31/12/2025", URL_DOC,
                    {"unit": "pacientes; pacientes/1.000 hab; días; %",
                     "comparabilidad": "limitada: criterios de cómputo dependen de cada CCAA (RD 605/2003); la tasa oficial usa población de tarjeta sanitaria, el campo *_ine es DERIVADO con población INE",
                     "provisional": False})
        out2["ccaa"] = ccaa_out
        out2["serie_tiempo_medio_dias"] = serie_ccaa_dias
        out2["serie_pacientes"] = serie_ccaa_pac
        out2["nota_rectificacion"] = ("dic2025 rectificado el 24-09-2026 por corrección de los datos "
                                      "de Castilla-La Mancha: total nacional 853.509→853.740 pacientes; "
                                      "tiempo medio 121→122 días.")
        (DATA / "sile_quirurgica_ccaa.json").write_text(json.dumps(out2, ensure_ascii=False, indent=1))

    # --- fuentes ---
    fuentes = {
        "meta": META("este fichero", "-", "-")["meta"],
        "fuentes": [
            {"nombre": "SISLE-SNS — página oficial (indicadores resumen + datos por CCAA)",
             "url": URL_DOC, "formato": "PDF (no existe XLS/CSV oficial de la serie)",
             "periodicidad": "semestral (cortes 31-dic y 30-jun, RD 605/2003)", "uso": "serie estatal"},
            {"nombre": "RD 605/2003 — criterios homogéneos de listas de espera",
             "url": "http://www.boe.es/boe/dias/2003/06/05/pdfs/A21830-21840.pdf", "uso": "definición oficial de métricas"},
            {"nombre": "RD 1039/2011 — tiempo máximo de acceso a prestaciones",
             "url": "http://www.boe.es/boe/dias/2011/08/29/pdfs/BOE-A-2011-14190.pdf", "uso": "referencia normativa"},
            {"nombre": "Nota aclaratoria rectificación dic2025 (datos CLM)",
             "url": "https://www.sanidad.gob.es/estadEstudios/estadisticas/inforRecopilaciones/docs/Nota_Aclaratoria_Rectificacion_Dic_2025.pdf",
             "uso": "evidencia de rectificación posterior a la publicación"},
            {"nombre": "INE — Censo anual de población, tabla jaxiT3 67988 (CCAA y provincia)",
             "url": "https://www.ine.es/jaxiT3/Tabla.htm?t=67988", "formato": "CSV",
             "uso": "denominador del dato DERIVADO pacientes/1.000 hab"},
        ],
        "ficheros_raw": [f for _, f, _, _ in PERIODOS] + ["Nota_Aclaratoria_Rectificacion_Dic_2025.pdf"],
    }
    (DATA / "sources.json").write_text(json.dumps(fuentes, ensure_ascii=False, indent=1))

    print(f"periodos_ok={len(serie_nacional)} descartes={len(descartes)} ccaa_ultimo={len(ultimo['ccaa']) if ultimo else 0}")
    for d in descartes:
        print("  DESCARTE:", d)


if __name__ == "__main__":
    main()
