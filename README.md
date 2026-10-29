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

## Parte II — Preprocesamiento, features y análisis

La Parte II se reparte en 5 partes (P1-P5). El trabajo de P1, P2 y P3 ya está listo y vive en
**un solo notebook**, `notebooks/Proyecto_Final.ipynb`, en ese orden — así se evita tener tres
archivos sueltos y cada quien sigue viendo claramente dónde empieza y termina su parte. El
código reutilizable que ese notebook importa vive en `src/`, y es el mismo que usa
`run_pipeline.py`, así que el resultado de ambos coincide siempre:

```
Proyecto-ACD/
├── run_pipeline.py                        # pipeline completo: crudo -> final + SQLite
├── src/
│   ├── ingestion.py                       # extracción del catálogo (P3), opcional (--scrape)
│   ├── preprocessing.py                   # limpieza y preprocesamiento (P1)
│   └── features.py                        # ingeniería de características (P2 + P3)
├── notebooks/
│   ├── Proyecto_.ipynb                    # Parte I: scraping + limpieza inicial
│   └── Proyecto_Final.ipynb               # Parte II completa: P1 -> P2 -> P3, en un solo archivo
├── data/
│   ├── raw/                               # crudo del scraping
│   ├── processed/                         # dataset limpio e inicial (Parte I)
│   ├── interim/                           # dataset preprocesado (P1)
│   ├── final/                             # dataset final (P2 + P3), también lo regenera run_pipeline.py
│   ├── reference/                         # dim_categoria.csv, dim_marca.csv
│   └── plazavea.db                        # mismo dataset final, en SQLite
└── docs/
    ├── bitacora_decisiones.csv            # cada decisión técnica, con su justificación
    ├── cifras_oficiales.csv               # cifras que se citan en el informe
    ├── diapositivas_p3.md                 # contenido de las diapositivas de P3
    └── figures/                           # f3_*.png (P3), f4_*.png (P4)
```

### Reproducir el proyecto

```bash
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace notebooks/Proyecto_Final.ipynb
# o, de forma equivalente y más rápida (sin abrir Jupyter):
python run_pipeline.py            # usa el crudo ya guardado en data/raw/
python run_pipeline.py --scrape   # antes, vuelve a extraer el catálogo (tarda horas)
```

Las dos vías llegan al mismo resultado porque comparten el código de `src/`: el notebook lo
explica paso a paso con gráficos e interpretación (para leer y para el informe); el pipeline lo
corre de punta a punta en segundos (para verificar reproducibilidad y regenerar
`data/plazavea.db`). `run_pipeline.py` verifica los requisitos de calidad de la rúbrica antes de
guardar.
