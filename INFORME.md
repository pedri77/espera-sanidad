# INFORME — Listas de espera sanitarias en España (observatorio «espera-sanidad»)

Fecha de elaboración: 2026-10-01. Todo lo que sigue sale de `raw/` y es reproducible con
`python3 scripts/sile_fetch.py && python3 scripts/sile_build.py`. Ninguna cifra está estimada.

## 1. Cómo se obtienen los datos (dos niveles)

**Nivel estatal (el que usa este observatorio).** El Ministerio de Sanidad publica el
*Sistema de Información sobre Listas de Espera del SNS* (SISLE-SNS):

- Página oficial: https://www.sanidad.gob.es/estadEstudios/estadisticas/inforRecopilaciones/listaEspera.htm
- **Formato: PDF** (informe nacional «Indicadores resumen» + informe «Datos por CCAA»).
  No existe un XLS/CSV oficial de esta serie en el portal estadístico; los PDF son la
  publicación normativa (RD 605/2003).
- **Periodicidad: semestral**, cortes a 31 de diciembre y 30 de junio (RD 605/2003).
- Serie histórica desde 2003 en la misma página («Informes previos»).
- Marco normativo y definiciones: RD 605/2003 (criterios homogéneos) y RD 1039/2011
  (procesos seleccionados, criterios OCDE). Definiciones en el glosario de cada informe.

**Nivel autonómico (documentado, NO mezclado en los agregados).** Cada comunidad publica
su propio detalle (por hospital, por procedimiento, a veces con cortes mensuales). El
Ministerio mantiene un directorio:
https://www.sanidad.gob.es/estadEstudios/estadisticas/inforRecopilaciones/listaEsperaInfCCAA.htm
Estas fuentes usan criterios y calendarios propios → no son comparables entre sí ni con la
serie estatal sin ajuste. Este observatorio **solo** usa la serie estatal homogénea.
Los indicadores también están en INCLASNS (https://inclasns.sanidad.gob.es), actualizados
con retraso respecto al informe semestral.

## 2. Cobertura y números medidos

| Concepto | Valor medido |
|---|---|
| Informes descargados (cacheados en `raw/sile/`) | 16 PDF (8 periodos × informe nacional + datos CCAA) + nota aclaratoria |
| Periodos cubiertos | 8 semestres: jun2022 → dic2025 (mínimo pedido: 4-6) |
| Filas parseadas y validadas | nacional: 8 × (14 especialidades + TOTAL); CCAA: 8 × 19; consulta externa: 19 + TOTAL |
| Validación automática | suma de especialidades = TOTAL nacional en los 8 periodos (0 desviación); suma de las 19 CCAA dic2025 = 853.740 = total nacional publicado |
| **Periodos descartados** | **0** |
| Población INE (Censo anual 2025, tabla jaxiT3 67988) | 19 CCAA + total nacional (49.128.297 hab a 1-1-2025) |

**Celdas sin dato (no se rellenan):** algunas celdas por CCAA/especialidad figuran «-» en
los PDF (p. ej. Rioja sin Cirugía Pediátrica ni Neurocirugía, Ceuta/Melilla sin la mayoría
de especialidades quirúrgicas). El parseo las deja fuera; no se imputan.

**Métrica que NO está publicada y NO se estima:**
- El informe de **consulta externa no publica el número de pacientes por CCAA**, solo la
  tasa por 1.000 hab, el tiempo medio y el % de citas >60 días. Se recoge tal cual
  (`data/sile_consultas_externas.json`); no se deriva ningún recuento multiplicando por población.
- Pruebas diagnósticas: el SISLE actual ya no publica tabla de pruebas diagnósticas en el
  informe nacional (sí existía en ediciones antiguas). No se incluye.

## 3. Verificación manual contra lo publicado (3 cifras)

1. **Total nacional dic2025 (rectificado):** este pipeline → 853.740 pacientes, 122 días.
   Publicado: página 3 del informe (`853.740`, `122`) y nota aclaratoria de rectificación
   («la versión rectificada consigna un total de 853.740 pacientes», «122 días»). ✔
2. **dic2024:** este pipeline → 846.583 pacientes, 126 días. Publicado: nota de prensa del
   Ministerio (id 6655): «846.583 pacientes… tiempo medio de espera de 126 días». ✔
3. **Andalucía dic2025:** este pipeline → 199.950 pacientes, tasa 23,51, 173 días.
   Publicado: página 8 del informe (fila `ANDALUCÍA 199.950 23,51 64.302 32,2 173`). ✔

## 4. Agregados que sostienen el episodio (todo en `data/`, con `meta` por campo)

**Serie nacional quirúrgica (jun2022 → dic2025), pacientes / tiempo medio días / % >6 meses:**

| Periodo | Pacientes | Días | % >6 meses |
|---|---|---|---|
| jun2022 | 742.518 | 113 | 17,6 |
| dic2022 | 793.521 | 120 | 20,8 |
| jun2023 | 819.964 | 112 | 17,4 |
| dic2023 | 849.535 | 128 | 24,3 |
| jun2024 | 848.340 | 121 | 20,5 |
| dic2024 | 846.583 | 126 | 22,9 |
| jun2025 | 832.728 | 118,6 | 19,6 |
| dic2025 | 853.740 | 122 | 21,6 |

Tendencia: el número de pacientes crece un **+15%** entre jun2022 y dic2025; el tiempo medio
se mueve en una banda de 112–128 días sin tendencia clara (máximo dic2023).

**Por especialidad (dic2025, nacional):** más espera = Cirugía Plástica (269 días, 40,8% >6
meses), Neurocirugía (172), Angiología/Cirugía Vascular (152); menos espera = Dermatología
(64 días), Cirugía Cardiaca (77), Oftalmología (80). Volumen: Traumatología 200.604
pacientes, Oftalmología 173.079, Cirugía General y Digestivo 149.836.

**Por comunidad (dic2025):** pacientes/1.000 hab con la tasa oficial del SISLE (denominador
= población de tarjeta sanitaria) y, **etiquetado como DERIVADO**, el cálculo propio con
población INE (`pacientes_por_1000_hab_ine`, diferencias pequeñas: ambos métodos dan
±0,5 salvo Canarias/CLM por población protegida > residente). Ambas columnas están en el
JSON; en ningún caso se presenta como ranking objetivo (ver §5).

**Consulta externa (dic2025, nacional):** tasa 84,42 pacientes/1.000 hab, tiempo medio 102
días, 61,5% de citas con demora >60 días. Rango CCAA en tasa: Melilla 13,26 — Madrid 134,69.

## 5. LA TRAMPA CENTRAL: las comunidades no miden igual

El propio Ministerio lo advierte literalmente en cada informe y en la web oficial:

> «El contenido de los indicadores depende de la información suministrada en origen por
> cada Comunidad Autónoma. El Ministerio de Sanidad agrega las cifras en un único documento
> y lo publica como indica la normativa, siendo responsabilidad de cada administración
> autonómica la fidelidad de los datos respecto a su realidad asistencial y el cumplimiento
> de los criterios de cómputo vigentes.» (listaEspera.htm, actualización 24-09-2026)

Diferencias concretas documentadas en esta investigación:

1. **Los datos los aporta cada CCAA**; el Ministerio solo agrega (RD 605/2003). No hay
   auditoría central publicada del criterio de cómputo de cada comunidad.
2. **Rectificación de Castilla-La Mancha en dic2025** (24-09-2026): el total nacional pasó
   de 853.509 a 853.740 pacientes y el tiempo medio de 121 a 122 días *nueve meses después*
   de publicarse. Evidencia: `Nota_Aclaratoria_Rectificacion_Dic_2025.pdf`. Es decir: el
   dato "definitivo" de un corte puede cambiar mucho después.
3. **Anomalías visibles en los propios datos:** CLM reportó **0,0%** de pacientes >6 meses
   en dic2022 (todos sus vecinos: 13-32%) y Madrid reporta 0,8% en dic2025 frente a 32,2%
   de Andalucía — diferencias tan extremas que reflejan criterios de registro distintos, no
   solo realidad asistencial.
4. **El % de pacientes >6 meses no se publicaba por CCAA antes de 2024** (los informes
   2022-2023 traen 4 columnas, sin el recuento absoluto) → la comparación temporal de ese
   indicador tiene menos historia que el resto.
5. **Criterios de inicio de cuenta:** el RD 605/2003 fija que la espera empieza en la fecha
   de prescripción registrada, pero la captura de "pacientes en espera estructural"
   (excluye pacientes programados/rechazos según criterio de cada CCAA) depende del
   registro autonómico. No se publica qué CCAA excluye a quién.
6. **Población de referencia distinta:** la tasa oficial usa tarjeta sanitaria; el dato
   derivado con INE da valores distintos (hasta 1 punto/1.000 en Canarias). Ambos están en
   el JSON para no esconder el efecto.
7. **Revisión retrospectiva sin nota:** el gráfico del informe dic2025 atribuye a Dic-22 un
   22,0% de pacientes >6 meses, mientras el informe original dic2022 (fila TOTAL) y el
   gráfico del informe dic2024 consignan 20,8%. Este observatorio usa siempre la cifra del
   informe original de cada periodo.
8. **Consulta externa cambia de criterio dentro del propio informe:** «En esta edición, se
   han incluido también pacientes pendientes de fecha que, en el momento del corte,
   superaban los 60 días» (glosario dic2025) → el % >60 días no es comparable con ediciones
   anteriores sin más.
9. **Ceuta y Melilla** no reportan la mayoría de especialidades quirúrgicas (celdas «-»).

**Consecuencia editorial:** los datos por CCAA se presentan con su definición oficial y con
esta advertencia; no como clasificación objetiva de "mejor o peor gestión".

## 6. Ficheros

- `data/sile_quirurgica_nacional.json` — serie nacional 8 semestres + serie por especialidad.
- `data/sile_quirurgica_ccaa.json` — dic2025 por CCAA (tasa SISLE + derivado INE) + series por CCAA.
- `data/sile_consultas_externas.json` — consulta externa dic2025 (nacional + CCAA).
- `data/sources.json` — catálogo de fuentes con URL y uso.
- `raw/sile/`, `raw/ine/` — crudos (no se versionan).

Tono: se describen datos oficiales agregados; nada de personas físicas, ni valoraciones
ni acusaciones.
