# Diapositivas de P3 (2,5 min) — descuentos y ahorro

Contenido para las 2-3 diapositivas de P3 en `docs/presentacion_parte2.pptx`. Una idea por
diapositiva, el gráfico ocupa la mayor parte y el texto es solo el titular + la cifra.

---

## Diapositiva 1 — ¿Dónde hay más ofertas?

**Titular:** Cuidado Personal concentra las ofertas; Frutas y Verduras, casi ninguna.

**Gráfico:** `docs/figures/f3_tasa_descuento_categoria.png`

**Cifra:** 80,0 % de Cuidado Personal tiene oferta activa, frente a 12,0 % de Frutas y Verduras
(68 puntos porcentuales de diferencia).

---

## Diapositiva 2 — El ahorro real suele ser chico

**Titular:** La mitad de las ofertas del catálogo ahorran S/ 1,75 o menos — salvo en Cuidado
Personal.

**Gráfico:** `docs/figures/f3_dispersion_descuento_ahorro.png`

**Cifra:** solo el 21,9 % del catálogo (326 de 1491 productos) tiene una oferta "significativa"
(≥10 % de descuento y ≥S/ 2 de ahorro). El ahorro promedio en Cuidado Personal (S/ 61,35) es
más de 30 veces el del resto del catálogo junto (S/ 0,82).

---

## Diapositiva 3 — El pipeline reproducible

**Titular:** Un solo comando regenera el dataset final desde el crudo.

**Diagrama:** `docs/pipeline.png` (lo diseña P5, sección 5 del informe)

**Texto:**
- `python run_pipeline.py` encadena limpieza (P1) → features (P2+P3) → verificación de calidad
  → `data/final/plazavea_final.csv` + `data/plazavea.db`
- `--scrape` vuelve a extraer el catálogo si hace falta (tarda horas, por eso es opcional)
