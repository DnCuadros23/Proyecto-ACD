"""Ingeniería de características (P2 + P3): contenido y precio unitario, rango de descuento,
y dos variables del contrato de datos que el dataset de P2 todavía no incluye.

Las tres primeras funciones reproducen notebooks/P2.ipynb. `calcular_oferta_significativa` y
`calcular_segmento_precio` no vienen en ese notebook; se agregan aquí porque el análisis de P3
(objetivo 4, segmentación) las necesita y ya estaban definidas en el contrato de datos del equipo.
"""
import re

import numpy as np
import pandas as pd

COLUMNAS_P2 = ["cantidad_base", "tipo_unidad_medida", "precio_unitario_normalizado", "rango_descuento"]

# (patrón en el nombre, factor de conversión a la unidad base, tipo de unidad, normaliza por 100)
_PATRONES_CONTENIDO = [
    (r"(\d+[.,]?\d*)\s*(?:kg|kilo)\b", 1000, "100g", True),
    (r"(\d+[.,]?\d*)\s*(?:gr|g)\b", 1, "100g", True),
    (r"(\d+[.,]?\d*)\s*(?:lt|l)\b", 1000, "100ml", True),
    (r"(\d+[.,]?\d*)\s*(?:ml|cc)\b", 1, "100ml", True),
    (r"(\d+[.,]?\d*)\s*(?:un|und|pack|pq|paquete)\b", 1, "unidad", False),
]


def extraer_contenido_y_precio(row):
    """`cantidad_base`, `tipo_unidad_medida` y `precio_unitario_normalizado`, a partir del
    contenido (peso, volumen o unidades) que aparece en el nombre del producto."""
    nombre = str(row["nombre"]).lower()
    precio = row["precio_venta"]

    for patron, factor, tipo, por_cien in _PATRONES_CONTENIDO:
        coincidencia = re.search(patron, nombre)
        if not coincidencia:
            continue
        cantidad_base = float(coincidencia.group(1).replace(",", ".")) * factor
        base = 100 if por_cien else 1
        precio_unitario = (precio / cantidad_base) * base
        return pd.Series([cantidad_base, tipo, round(precio_unitario, 4)])

    return pd.Series([np.nan, "desconocido", np.nan])


def clasificar_descuento(descuento_pct):
    """`rango_descuento`: Sin descuento / Bajo (<10%) / Moderado (10%-25%) / Alto (>25%)."""
    if descuento_pct == 0:
        return "Sin descuento"
    if descuento_pct < 10:
        return "Bajo (<10%)"
    if descuento_pct <= 25:
        return "Moderado (10%-25%)"
    return "Alto (>25%)"


def calcular_oferta_significativa(df):
    """`oferta_significativa`: descuento_pct >= 10 y ahorro_soles >= 2 (umbral acordado en el
    contrato de datos). No viene en el dataset de P2; la necesita el objetivo 4 de P3."""
    df = df.copy()
    df["oferta_significativa"] = (df["descuento_pct"] >= 10) & (df["ahorro_soles"] >= 2)
    return df


def calcular_segmento_precio(df):
    """`segmento_precio`: terciles de precio_venta dentro de cada categoría (Económico/Medio/
    Premium). Tampoco viene en el dataset de P2; la necesita la segmentación del objetivo 4."""
    df = df.copy()

    def en_terciles(serie):
        etiquetas = ["Económico", "Medio", "Premium"]
        try:
            return pd.qcut(serie, 3, labels=etiquetas)
        except ValueError:
            # categorías con muchos precios repetidos: se desempata por posición para no
            # dejar bins vacíos (pd.qcut no admite bordes duplicados)
            return pd.qcut(serie.rank(method="first"), 3, labels=etiquetas)

    df["segmento_precio"] = df.groupby("categoria")["precio_venta"].transform(en_terciles)
    return df


def crear_features(df):
    """Encadena los pasos de P2 y agrega oferta_significativa + segmento_precio (ver arriba)."""
    df = df.copy()
    df[["cantidad_base", "tipo_unidad_medida", "precio_unitario_normalizado"]] = df.apply(
        extraer_contenido_y_precio, axis=1
    )
    df["rango_descuento"] = df["descuento_pct"].apply(clasificar_descuento)
    df = calcular_oferta_significativa(df)
    df = calcular_segmento_precio(df)

    faltan = [c for c in COLUMNAS_P2 if c not in df.columns]
    assert not faltan, f"faltan columnas del contrato de datos (P2): {faltan}"
    return df
