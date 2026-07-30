# CoverMap v0.6.2 — ficheros para sustituir directamente

**Cómo aplicarlo:** copia estos 10 ficheros sobre el repo respetando las rutas
(`code/`, `data/`, y los tres de la raíz) y haz commit. No hay nada que buscar y reemplazar.

He clonado el repo, aplicado los cambios en las **fuentes**, reconstruido los tres países y
vuelto a pasar la verificación completa. **256/256 comprobaciones en verde, 0 fallos, y la pasada
OCR sobre las 11 figuras también pasa.**

```
code/viz_common.py          ← renderizador de la matriz
code/make_report_v2.py      ← leyenda del brief de Ghana
code/make_index.py          ← leyenda de la portada
code/build_v2.py            ← quitado un número escrito a mano
code/publish.py             ← NUEVO: sincroniza out2/ → raíz, con diff
data/coverage_matrix.csv    ← 10 celdas reclasificadas
methods.md                  ← 8 correcciones
methods.html                ← regenerado desde methods.md
ghana.html                  ← regenerado (leyenda + celdas)
index.html                  ← regenerado
```

---

## 1. El hallazgo que no esperaba: la matriz enseñaba un fallo demostrado como "parcial"

Esto es lo importante de todo el lote, y no estaba en mi lista anterior.

`coverage_matrix.csv` tenía **dos** columnas —`coverage` y `evidence_grade`— y la clase
`not-covered` mezclaba tres cosas que no son la misma:

| Fila | Estaba | Realidad |
|---|---|---|
| PANAF × *Naja katiensis* | `paraspecific-partial` → se pintaba **`~` parcial** | Khochare 2024 lo midió en **11,16 LD50/mL, por debajo del umbral de 20**. Es un **fallo demostrado**, y se estaba enseñando como cobertura parcial |
| EchiTAbG × *Naja nigricollis* | `not-covered` → **✗ rojo** | Es un producto monoespecífico de víbora: no reclama actividad elapídica. No es un fallo, es que no lo pretende |
| PANAF × *Atractaspis* | `not-covered` → **✗ rojo** | "Untested". No hay dato. Pintarlo igual que un fallo demostrado es afirmar algo que no sabemos |

**Los dos errores van en direcciones opuestas y los dos son malos.** El de *katiensis* **subestima
el riesgo** en la dirección insegura para una decisión de stock. El de *Atractaspis* **afirma sobre
un producto comercial algo que la evidencia no sostiene**, que es justo el riesgo legal que declaro
en C.6.1 de la candidatura.

Y además: la candidatura dice en C.2.1 y C.6.2 que *"la evidencia de fallo anula todo grado
superior"*. **Con la clasificación anterior eso no era verdad.** Ahora sí.

### La corrección

Clases nuevas y separadas:

| Clase | Glifo | Qué significa | Filas |
|---|---|---|---|
| `failed` | **✗** rojo oscuro | Evidencia publicada **en contra** de la neutralización | 6 |
| `not-covered` | **–** rosa apagado | No reclama actividad / fuera de alcance / no está en el inmunógeno | 4 |
| `no-data` | **·** gris | Sin testar, sin dato | 4 |
| `paraspecific-partial` | **~** | Parcial / paraespecífico | 3 |
| `unknown` | **?** | En la indicación, sin dato in vivo | 3 |

Las 6 filas que pasan a `failed`, todas con fuente:

1. **PANAF-Premium × *Naja katiensis*** — Khochare 2024, 11,16 LD50/mL, bajo umbral
2. **Asna Antivenom C (Bharat) × *Echis ocellatus*** — Visser 2008, letalidad 1,8% → 12,1%
3. **Inoserp Pan-Africa × *Dendroaspis polylepis*** — Kenya QC 2026, falla a la dosis reclamada
4. **SAIMR Polyvalent × *Atractaspis*** — Oulion 2018, neutralización pobre
5. **VINS polyvalent × *Dendroaspis polylepis*** — Ainsworth 2018, ineficaz
6. **VINS polyvalent × *Dendroaspis viridis*** — Ainsworth 2018, ineficaz

> ⚠️ **Esta es la única decisión de criterio que he tomado sobre tus datos.** Es reversible: está
> toda en `data/coverage_matrix.csv` más una función de 8 líneas en `viz_common.py`. Si no
> compartes alguna reclasificación, cámbiala y reconstruye. Pero la de *katiensis* deberías
> mantenerla: un fallo medido pintado como "parcial" es el tipo de error del que va este proyecto.

---

## 2. Correcciones de números obsoletos

Todas verificadas ejecutando el código, no deducidas.

| Dónde | Decía | Dice ahora | Cómo lo he comprobado |
|---|---|---|---|
| `methods.md` §5 Ghana | `3,760 envenomings/yr` | **`5,627`** | `impact_summary.json` → `burden_anchor.modelled_envenomings_yr` = 5627 |
| `methods.md` §5 India | `55,649` / `4.1%` | **`55,656`** / **`4.0%`** | `impact_summary_in.json` |
| `methods.md` §6 | La fórmula de demanda llevaba `care-seeking` | Cadena corregida, y dice explícitamente que no se aplica | El parámetro se borró en v0.4; §6 y §7 se contradecían |
| `methods.md` §9 | `Ghana 23/25 y Nigeria 51/64` | **`Ghana 24/25 y Nigeria 52/63`** | `placement_robustness` en los dos JSON. **Los dos números estaban mal** |
| `methods.md` §10 límite 1 | "Care-seeking is the dominant uncertainty" | La atendencia por zona, que es el parámetro dominante real | El anterior describía un parámetro que ya no existe |
| `methods.md` §11 | `All 245 pass` | **`All 256 pass (54 · 62 · 73 · 67)`** | Contando líneas `PASS` de las cuatro suites ejecutadas |
| `methods.md` §11 | "10 load-bearing numbers remain assumptions" | **"6 de 28 siguen NOT CONFIRMED"** | Coincide con la auditoría |
| `methods.md` §7 | Tabla con **12 filas, 4 duplicadas** y rangos incompatibles | **8 filas, sin duplicados** | `Reach radius` ×2, `Price/vial` con `$3,4–$315` *y* `$18–200`, `buffer` como "NOT CONFIRMED" *y* "planning assumption" |
| `code/build_v2.py` | `"...; 5,811 < 9,900 ..."` escrito a mano | Se calcula del modelo | Un literal más que sobrevivía a las correcciones |

**Sobre el 3.760: te debo una rectificación.** Te dije que 3.760/5.627 = 0,668 era "exactamente un
descuento de `care-seeking` de más". **Era falso.** El `care-seeking` valía 0,45 y la fracción de
envenenamiento 0,647; ninguno da 0,668. La cifra correcta es 5.627 porque **la ha devuelto
`build_v2.py` al ejecutarlo**, no porque yo dedujera un mecanismo. La lección 4 del proyecto,
aplicada a mí.

**Sobre el umbral de 3 h:** `methods.md` se lo atribuía a Longbottom 2018. Una comprobación
independiente dice que Longbottom usa **>1 h**. No lo he podido resolver, así que he reescrito la
fila para decir que *el estándar publicado es tiempo de viaje, no distancia*, y que **el umbral y la
conversión son nuestros** — que es cierto en cualquier caso. Verifícalo antes de citar una cifra.

---

## 3. `code/publish.py` — nuevo

No había script de publicación: la copia de `out2/` a la raíz se hacía a mano. Por eso el repo
llegó a llevar figuras nuevas con scripts viejos. Lección 6 del proyecto: *copiar no es sincronizar*.

```bash
python3 code/publish.py            # diff, no escribe nada
python3 code/publish.py --write    # publica
python3 code/publish.py --write --audit   # además regenera parameter-audit.txt
```

Hace diff por SHA-256, dice qué fichero cambia y cuántos bytes, y **aborta si falta una salida de
build** en vez de publicar a medias. Al ejecutarlo ahora: 7 ficheros ya sincronizados, solo
`ghana.html` cambiaba (+209 bytes, la leyenda). Esa es la comprobación que no existía.

---

## 4. Reproducir esto desde cero

```bash
pip install geopandas rasterstats rdata pandas numpy matplotlib
python3 code/build_v2.py && python3 code/make_v2_visuals.py && python3 code/make_report_v2.py
python3 code/nigeria_build.py && python3 code/nigeria_outputs.py
python3 code/india_build.py  && python3 code/india_outputs.py
python3 code/make_planner.py && python3 code/make_index.py && python3 code/make_methods_page.py
python3 code/publish.py --write --audit
for f in ghana nigeria india crosscountry; do python3 code/verify_$f.py; done
python3 code/verify_figures.py
```

`geopandas`, `rasterstats` y `rdata` **no están declaradas en ningún sitio del repo**. Sin ellas no
arranca nada. Añade un `requirements.txt` — es una línea de trabajo y quita el mismo obstáculo que
las rutas absolutas de la v0.6.1.

---

## 5. Lo que queda y no he tocado

- **`india.html` dice 32,6% de *Hypnale hypnale* en Kerala**; la revisión de Menon que cita reporta
  **15,4%**. No lo he cambiado porque no sé cuál de los dos es el bueno: hay que ir al paper.
- **El hueco de reproducibilidad de Ghana** sigue: `facilities_hospitals.csv` es un filtro sobre
  `ghana_facilities_who.csv` cuyo script no está en el repo. Declarado en `data/README.md`.
- **La versión.** Los ficheros siguen sellados **v0.6.1**. Si publicas esto, súbelo a **v0.6.2** y
  añade la entrada de changelog — el cambio de la matriz es material y la candidatura cita el sello.

---

*Verificado el 29 de julio de 2026 sobre un clon limpio de `main`. 256/256 comprobaciones, 11/11
figuras.*
