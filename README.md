# En espera · Las listas de espera del Sistema Nacional de Salud

Ocho semestres de datos oficiales del **Ministerio de Sanidad** (SISLE-SNS): cuántos pacientes esperan
una operación, cuánto tardan de media, cuántos llevan más de seis meses, y lo mismo para la primera
consulta del especialista. Por comunidad autónoma y por especialidad quirúrgica.

- **Web:** <https://pedri77.github.io/espera-sanidad/>
- **Vídeo:** episodio `cci-11` de la serie [«Construido con IA»](https://iacedemy.com/free/yt/construido-con-ia/) de IAcademy.
- **Plantilla para hacer el tuyo:** [observatorio-datos-plantilla](https://github.com/pedri77/observatorio-datos-plantilla).

## Lo primero, y es lo que define este proyecto

**Esta web no hace un ranking de comunidades.** Los datos los aporta cada comunidad autónoma y **no
todas miden igual**: quién entra en lista, cuándo empieza a contar la espera y qué pacientes se
incluyen varía de un territorio a otro. El propio Ministerio lo advierte en su publicación.

Así que aquí se muestra lo que cada administración declara, con su definición, y **se señalan los casos
que no cuadran entre sí** en vez de corregirlos o suavizarlos. Hay semestres con un 0,0 % de pacientes
esperando más de seis meses y comunidades que difieren más de treinta veces en ese mismo indicador:
son artefactos de registro, no diferencias reales de atención, y borrarlos sería peor que mostrarlos.

Comparar dos comunidades es comparar dos formas de contar.

## Qué sale de los datos (diciembre de 2025)

| Indicador | Valor |
|---|---|
| **Pacientes en espera quirúrgica** | **853.740** |
| Espera media | **122 días** |
| Lleva más de seis meses | 21,6 % |
| Tasa | 17,70 por 1.000 tarjetas sanitarias |
| Espera media para el especialista | 102 días |
| Citas con más de 60 días de espera | 61,5 % |

## La tendencia no es una recta

La serie arranca en junio de 2022 con 742.518 pacientes y 113 días. Al cerrar 2025 hay **111.222
pacientes más (+15 %)**, pero la lista **bajó en tres de los siete semestres** siguientes (junio de
2024, diciembre de 2024 y junio de 2025). La espera media tampoco mejora de forma sostenida: oscila
entre 112 y 128 días y termina en 122, nueve días más que en el primer semestre de la serie.

Las tres especialidades con más pacientes son **traumatología** (200.604 pacientes, 137 días de
espera), **oftalmología** (173.079, 80 días) y **cirugía general y de digestivo** (149.836, 113 días):
entre las tres suman el 61 % de la lista. Pero el mayor tiempo de espera no está ahí sino en **ORL:
142 días** para 72.030 pacientes.

## La fuente no tiene Excel

El Ministerio **no publica un XLS ni un CSV**: la serie sale de un PDF semestral. El pipeline descarga
el PDF y lo extrae con `pdftotext`, con validaciones duras en cada paso:

- La suma de las **catorce especialidades** tiene que dar exactamente el total nacional.
- La suma de las **diecinueve comunidades** (17 + Ceuta y Melilla) tiene que dar exactamente el total.
- Se comprueba en los **ocho semestres**, no solo en el último.
- Las celdas con guion («-») se dejan como **sin dato**: no se imputan ni se rellenan.

## Reproducirlo

```bash
python3 scripts/sile_fetch.py     # descarga los PDF semestrales y el censo del INE a raw/ (cachea)
python3 scripts/sile_build.py     # extrae, valida y escribe data/*.json  (necesita pdftotext)
```

| Fichero | Contenido |
|---|---|
| `data/sile_quirurgica_nacional.json` | Serie nacional de 8 semestres + las 14 especialidades |
| `data/sile_quirurgica_ccaa.json` | 19 comunidades, con la tasa oficial y una derivada con población INE |
| `data/sile_consultas_externas.json` | Primera consulta del especialista, nacional y por comunidad |
| `data/sources.json` | Fuentes, ficheros originales y definiciones |

`raw/` (12 MB de PDF y CSV) no se versiona: `sile_fetch.py` lo repone.

## Trampas encontradas

- **Los datos se rectifican.** El semestre de diciembre de 2025 se corrigió **nueve meses después** por
  un error en los datos de Castilla-La Mancha: el total nacional pasó de 853.509 a 853.740 pacientes y
  la media de 121 a 122 días. Esta web usa la versión rectificada.
- **La tasa oficial no es la nuestra.** Sanidad calcula por 1.000 **tarjetas sanitarias**; aquí se
  muestra también una versión con población del INE, **etiquetada como derivada**. Dan cifras parecidas
  y distintas.
- **El porcentaje de pacientes con más de seis meses solo se publica por comunidad desde 2024.** Para
  los semestres anteriores no hay dato territorial y no se estima.
- **Las pruebas diagnósticas ya no se publican.** Hubo semestres con ese indicador; la serie actual no
  lo trae, así que no aparece.
- **Cambio de criterio** en el porcentaje de citas con más de 60 días de consulta externa: afecta a la
  comparabilidad entre semestres.
- **Revisión retrospectiva sin aviso**: la cifra de diciembre de 2022 pasó del 20,8 % al 22,0 % de
  pacientes con más de seis meses sin nota que lo explicara.

## Verificación

- **Contra la nota de prensa del Ministerio**: 853.740 pacientes y 122 días (dic-2025), 846.583 y 126
  días (dic-2024), Andalucía 199.950 pacientes y 173 días — todo coincide.
- **Coherencia interna**: especialidades y comunidades suman el total nacional **exacto** en los 8
  semestres (diferencia 0 en ambos casos).
- **Sin descartes silenciosos**: 0 periodos descartados, 0 imputaciones.

## Fuente y licencia

Ministerio de Sanidad, **Sistema de Información sobre Listas de Espera del Sistema Nacional de Salud**
(SISLE-SNS), publicación semestral al amparo del Real Decreto 605/2003. Población: INE (censo, tabla
67988). Agregados y tasa derivada de elaboración propia; el Ministerio no participa ni avala esta
reutilización.

Código bajo **MIT** (`LICENSE`).
