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
