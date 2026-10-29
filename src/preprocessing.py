"""Preprocesamiento del dataset: limpieza de marcas, outliers de precio, integración con las
tablas de referencia del equipo y transformación de precio_venta.

Reproduce en funciones reutilizables la lógica del notebook, para que run_pipeline.py pueda
regenerar el dataset preprocesado sin volver a correr el notebook completo. Las decisiones (qué
se hizo y por qué) están documentadas en notebooks/Proyecto_Final.ipynb y en
docs/bitacora_decisiones.csv; aquí solo queda el código.
"""
import re
import unicodedata

import numpy as np
import pandas as pd

COLUMNAS_P1 = ["es_outlier_precio", "precio_venta_log", "macro_grupo", "es_marca_propia", "marca_agrupada"]

MAPA_CATEGORIAS = {
    "abarrotes": "Abarrotes", "bebidas": "Bebidas", "lacteos": "Lácteos",
    "cuidado-personal": "Cuidado Personal", "frutas-verduras": "Frutas y Verduras",
    "carnes-pescados": "Carnes y Pescados", "desayunos": "Desayunos",
    "quesos-fiambres": "Quesos y Fiambres", "panaderia": "Panadería",
    "congelados": "Congelados", "limpieza": "Limpieza",
}


def limpiar(df_crudo, umbral_categoria=50):
    """Limpieza del crudo del scraping (data/raw/plazavea_crudo_*.csv -> dataset inicial):
    normaliza texto, renombra sku -> id_producto, deduplica por url_producto, quita
    `url_imagen` (más de 70 % de nulos, y gran parte de lo que queda es el octógono
    nutricional, no la foto del producto), tipa y valida precios, descarta categorías con
    extracción incompleta (< umbral_categoria productos) y recalcula las variables de oferta."""
    df = df_crudo.copy()

    df["nombre"] = df["nombre"].map(lambda s: re.sub(r"\s+", " ", str(s)).strip())
    df["marca"] = df["marca"].map(lambda s: re.sub(r"\s+", " ", str(s)).strip()).str.upper()
    df["categoria"] = df["categoria"].map(MAPA_CATEGORIAS).fillna(df["categoria"])

    df = df.rename(columns={"sku": "id_producto"})
    df = df.drop_duplicates(subset="url_producto", keep="first").reset_index(drop=True)
    df = df.drop(columns=["url_imagen"], errors="ignore")

    for col in ["precio_venta", "precio_regular"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[df[col] <= 0, col] = pd.NA
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.loc[df["precio_regular"] < df["precio_venta"], "precio_regular"] = df["precio_venta"]

    conteo = df["categoria"].value_counts()
    categorias_chicas = conteo[conteo < umbral_categoria].index.tolist()
    df = df[~df["categoria"].isin(categorias_chicas)].reset_index(drop=True)

    hay_oferta = df["precio_regular"] > df["precio_venta"]
    df["descuento_pct"] = 0.0
    df.loc[hay_oferta, "descuento_pct"] = ((1 - df["precio_venta"] / df["precio_regular"]) * 100).round(2)
    df["tiene_descuento"] = hay_oferta
    df["ahorro_soles"] = (df["precio_regular"] - df["precio_venta"]).round(2)
    df["fecha_extraccion"] = pd.to_datetime(df["fecha_extraccion"], errors="coerce")

    return df


def _clave_marca(texto):
    """Clave de comparación sin tildes, signos ni mayúsculas (BELL'S == BELLS == Bell s)."""
    normalizado = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z0-9]", "", normalizado.upper())


def unificar_marcas(df):
    """Une una misma marca escrita de dos formas (se queda con la más frecuente de las dos)."""
    df = df.copy()
    frecuencia = df["marca"].value_counts()
    agrupadas = df.groupby(df["marca"].map(_clave_marca))["marca"].agg(lambda s: sorted(s.unique()))
    variantes = agrupadas[agrupadas.map(len) > 1]
    mapa_marca = {
        escritura: max(escrituras, key=lambda m: frecuencia[m])
        for escrituras in variantes
        for escritura in escrituras
    }
    df["marca"] = df["marca"].replace(mapa_marca)
    return df


def marcar_outliers_precio(df, k=1.5):
    """`es_outlier_precio`: regla IQR calculada dentro de cada categoría (un kilo de papa y un
    suplemento no son comparables). No se elimina ninguna fila: son productos reales."""
    df = df.copy()

    def fuera_de_rango(serie):
        q1, q3 = serie.quantile([0.25, 0.75])
        iqr = q3 - q1
        return (serie < q1 - k * iqr) | (serie > q3 + k * iqr)

    df["es_outlier_precio"] = df.groupby("categoria")["precio_venta"].transform(fuera_de_rango).astype(bool)
    return df


def integrar_referencias(df, dim_categoria, dim_marca):
    """Left join con dim_categoria (-> macro_grupo) y dim_marca (-> es_marca_propia); no debe
    cambiar el número de filas."""
    n0 = len(df)
    df = df.merge(dim_categoria, on="categoria", how="left", validate="many_to_one")
    df = df.merge(dim_marca[["marca", "es_marca_propia"]], on="marca", how="left", validate="many_to_one")
    df["es_marca_propia"] = df["es_marca_propia"].fillna(False).astype(bool)
    assert len(df) == n0, "la integración de referencias cambió el número de filas"
    return df


def agrupar_marcas(df, top_n=30, sin_marca="GENÉRICO"):
    """`marca_agrupada`: conserva las top_n marcas reales más frecuentes, deja GENÉRICO como
    nivel propio (no es una marca, son productos de terceros) y agrupa el resto en OTRAS.

    Al desempate (marcas con la misma frecuencia justo en el borde del top_n) se resuelve por
    orden alfabético: `value_counts().head(n)` por sí solo no es reproducible ahí, porque el
    orden entre empates depende del orden interno (no garantizado) de pandas."""
    df = df.copy()
    frecuencia_real = df.loc[df["marca"] != sin_marca, "marca"].value_counts()
    frecuencia_real = frecuencia_real.sort_index().sort_values(ascending=False, kind="stable")
    top_marcas = frecuencia_real.head(top_n).index
    df["marca_agrupada"] = np.where(
        df["marca"].isin(top_marcas), df["marca"],
        np.where(df["marca"] == sin_marca, sin_marca, "OTRAS"),
    )
    return df


def transformar_precio(df):
    """`precio_venta_log`: log1p(precio_venta), reduce la fuerte asimetría del precio de venta."""
    df = df.copy()
    df["precio_venta_log"] = np.log1p(df["precio_venta"])
    return df


def preprocesar(df_inicial, dim_categoria, dim_marca):
    """Encadena los pasos de preprocesamiento y devuelve el dataset con las 5 columnas del
    contrato de datos (es_outlier_precio, precio_venta_log, macro_grupo, es_marca_propia,
    marca_agrupada), sin cambiar el número de filas."""
    df = unificar_marcas(df_inicial)
    df = marcar_outliers_precio(df)
    df = integrar_referencias(df, dim_categoria, dim_marca)
    df = agrupar_marcas(df)
    df = transformar_precio(df)

    faltan = [c for c in COLUMNAS_P1 if c not in df.columns]
    assert not faltan, f"faltan columnas del contrato de datos: {faltan}"
    assert len(df) == len(df_inicial), "el preprocesamiento cambió el número de filas"
    return df
