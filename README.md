# Proyecto-ACD

Proyecto EC1 de Web Scraping — curso Análisis Computacional de Datos (DS3021).
Extracción del catálogo de [PlazaVea](https://www.plazavea.com.pe/) con Selenium +
BeautifulSoup para construir un dataset de precios, descuentos y categorías de productos.

## Estructura del proyecto

```
Proyecto-ACD/
├── notebooks/
│   └── Proyecto_.ipynb   # P1-P3: reconocimiento, motor y extracción masiva
├── data/
│   ├── raw/                         # CSV crudos (parciales por categoría + consolidado)
│   └── processed/                   # dataset limpio (P4)
├── docs/                            # informe, diccionario de datos (P5-P6)
├── requirements.txt
└── .gitignore
```

## Entorno virtual

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Con el entorno activado, abrir `notebooks/Proyecto_.ipynb` en Jupyter o VS Code.
Los CSV se guardan en `data/raw/` con rutas relativas al propio notebook (`../data/raw`),
así que hay que ejecutarlo desde `notebooks/` y no mover el archivo fuera de esa carpeta.

## Integrantes

- Denilson Jermai Cuadros Villegas 202510232
- Enrique Eusebio Torres Chafloque 202510601
- Leo Alexander Torres Ccencho 202410078
- Valeria Bazán Meléndez 202410443
- Lucas Armando Aliaga Mena 201810550

## Parte II — Preprocesamiento, features y pipeline

La Parte II se reparte en 5 partes (P1-P5). El código reutilizable de cada parte vive en `src/`
y un solo comando reproduce el dataset final desde cero:

```
Proyecto-ACD/
├── run_pipeline.py                        # pipeline completo: crudo -> final + SQLite
├── src/
│   ├── ingestion.py                       # extracción del catálogo (P3), opcional (--scrape)
│   ├── preprocessing.py                   # limpieza y preprocesamiento (P1)
│   └── features.py                        # ingeniería de características (P2 + P3)
├── notebooks/
│   ├── Proyecto_.ipynb                    # Parte I: scraping + limpieza inicial
│   ├── 02_preprocesamiento.ipynb          # P1
│   ├── P2.ipynb                           # P2 (ingeniería de características)
│   └── 04_analisis_descuentos_ahorro.ipynb  # P3: objetivos 3-4, figuras, pipeline
├── data/
│   ├── raw/                               # crudo del scraping
│   ├── processed/                         # dataset limpio e inicial + dataset final de P2
│   ├── interim/                           # dataset preprocesado (P1)
│   ├── final/                             # dataset final regenerado por run_pipeline.py
│   ├── reference/                         # dim_categoria.csv, dim_marca.csv
│   └── plazavea.db                        # mismo dataset final, en SQLite
└── docs/
    ├── bitacora_decisiones.csv            # cada decisión técnica, con su justificación
    ├── cifras_oficiales.csv               # cifras que se citan en el informe
    └── figures/                           # f3_*.png (P3), f4_*.png (P4)
```

### Reproducir el proyecto

```bash
pip install -r requirements.txt
python run_pipeline.py            # usa el crudo ya guardado en data/raw/
python run_pipeline.py --scrape   # antes, vuelve a extraer el catálogo (tarda horas)
```

`run_pipeline.py` encadena `src/preprocessing.py` (limpieza + P1) y `src/features.py` (P2 + dos
variables del contrato de datos que el dataset de P2 todavía no incluye: `oferta_significativa`
y `segmento_precio`, necesarias para el análisis de P3). Verifica los requisitos de calidad de
la rúbrica antes de guardar y deja el resultado en `data/final/plazavea_final.csv` y en
`data/plazavea.db` (tablas `productos`, `dim_categoria`, `dim_marca`).

**Nota sobre rutas:** el notebook `P2.ipynb` guarda su propio resultado en
`data/processed/plazavea_final.csv` (no en `data/final/`, como se había acordado en el contrato
de datos del equipo); por eso conviven dos archivos de dataset final. `data/final/` es la salida
de `run_pipeline.py` y la ruta que describe este README.
