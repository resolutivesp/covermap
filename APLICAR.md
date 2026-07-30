# Sello de versión v0.6.2 — 9 ficheros

**Por qué hace falta.** Ya subiste los cambios de la matriz, y están live y renderizando bien
(comprobado: `ghana.html` pinta 4 celdas con el ✗ de fallo, la leyenda nueva está, `methods.md` dice
5.627 · 24/25 · 52/63 · 256). **Pero todos los artefactos siguen sellados `v0.6.1`.**

Eso rompe justo la disciplina de la que presume la candidatura. La v0.6.1 publicada ya no es la
v0.6.1 que había: la matriz clasifica distinto. Y B.8/C.2.1/C.5.1 citan el sello de versión y la
reproducibilidad. Un sello que no distingue dos estados del contenido no sirve para nada.

**Cómo aplicarlo:** copia estos 9 ficheros respetando rutas y haz commit.

```
code/viz_common.py     ← VERSION = "v0.6.2" + nota de versión (fuente única del sello)
methods.md             ← cabecera v0.6.2 + fila de changelog explicando el error y por qué
methods.html           ← regenerado
ghana.html   ghana-planner.html
nigeria.html nigeria-planner.html
india.html   index.html         ← regenerados, todos sellados v0.6.2
```

**Verificado tras el cambio:** 256/256 comprobaciones (54·62·73·67), 0 fallos, 11/11 figuras en la
pasada OCR. El pie de los tres briefs dice ya `CoverMap v0.6.2`.

## La fila de changelog que se añade

Dice lo que pasó sin maquillarlo: que la matriz confundía **fallo demostrado** con **ausencia de
dato**, que *N. katiensis* se pintaba como cobertura parcial teniendo un fallo medido en su propia
celda, que cuatro celdas de *Atractaspis* sin testar se pintaban como fallos, y —esto es lo que
importa— **que los dos errores iban en direcciones opuestas y los dos eran malos**: uno subestima el
riesgo en la dirección insegura para una decisión de stock, el otro afirma sobre un producto
comercial algo que la evidencia no sostiene.

Esa fila es un activo para la candidatura, no un pasivo. C.6.2 dice *"corrections are carried in
public rather than deleted"*. Aquí está la prueba.

---

*Reconstruido y verificado el 29 de julio de 2026 sobre un clon limpio de `main` con tus cambios
ya dentro.*
