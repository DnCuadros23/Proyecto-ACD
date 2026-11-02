"""Comparación de precios entre marcas de productos similares (objetivo 5) y concentración del
precio exclusivo con tarjeta Oh! (objetivo 6), a partir del dataset final.
"""
import pandas as pd

# primeras palabras del nombre que no dicen qué producto es ("Pack Galletas OREO ...")
_PALABRAS_ENVASE = {"pack", "mix", "sixpack", "set", "kit"}
# variantes de una misma palabra que deben caer en el mismo grupo
_SINONIMOS = {"galleta": "galletas"}

MIN_PRODUCTOS_GRUPO = 4
MIN_MARCAS_GRUPO = 2


def extraer_tipo_producto(nombre):
    """`tipo_producto`: la primera palabra del nombre (en PlazaVea el nombre empieza por el tipo
    de producto: "Galletas OREO ...", "Queso Edam LAIVE ..."), saltando palabras de envase."""
    palabras = str(nombre).lower().split()
    if not palabras:
        return None
    tipo = palabras[1] if palabras[0] in _PALABRAS_ENVASE and len(palabras) > 1 else palabras[0]
    return _SINONIMOS.get(tipo, tipo)


def grupos_comparables(df, min_productos=MIN_PRODUCTOS_GRUPO, min_marcas=MIN_MARCAS_GRUPO):
    """Productos "similares" = misma categoría, mismo tipo_producto y misma unidad de medida
    (100g, 100ml o unidad), con precio_unitario_normalizado conocido. Solo se conservan los
    grupos con al menos `min_productos` productos y `min_marcas` marcas distintas: con menos no
    hay nada que comparar.

    Agrega `grupo_comparable` y `precio_relativo` (precio unitario / mediana del grupo; 1 = precio
    típico del grupo, 0,8 = 20 % más barato que lo típico)."""
    df = df.copy()
    df["tipo_producto"] = df["nombre"].apply(extraer_tipo_producto)
    df = df.dropna(subset=["precio_unitario_normalizado", "tipo_producto"])
    df = df[df["tipo_unidad_medida"] != "desconocido"]

    df["grupo_comparable"] = df["categoria"] + " | " + df["tipo_producto"] + " | " + df["tipo_unidad_medida"]
    tamano = df.groupby("grupo_comparable")["id_producto"].transform("size")
    marcas = df.groupby("grupo_comparable")["marca"].transform("nunique")
    df = df[(tamano >= min_productos) & (marcas >= min_marcas)].copy()

    mediana = df.groupby("grupo_comparable")["precio_unitario_normalizado"].transform("median")
    df["precio_relativo"] = (df["precio_unitario_normalizado"] / mediana).round(4)
    return df


def marca_mas_economica(comparables):
    """Una fila por grupo comparable: la marca con la mediana de precio unitario más baja, la
    más cara, y cuánto se ahorra eligiendo la más barata frente al precio típico del grupo."""
    por_marca = (
        comparables.groupby(["grupo_comparable", "marca"])
        .agg(precio_unitario=("precio_unitario_normalizado", "median"),
             es_marca_propia=("es_marca_propia", "max"))
        .reset_index()
    )
    filas = []
    for grupo, sub in por_marca.groupby("grupo_comparable"):
        grupo_df = comparables[comparables["grupo_comparable"] == grupo]
        barata = sub.loc[sub["precio_unitario"].idxmin()]
        cara = sub.loc[sub["precio_unitario"].idxmax()]
        mediana_grupo = grupo_df["precio_unitario_normalizado"].median()
        filas.append({
            "grupo_comparable": grupo,
            "categoria": grupo_df["categoria"].iloc[0],
            "tipo_producto": grupo_df["tipo_producto"].iloc[0],
            "unidad": grupo_df["tipo_unidad_medida"].iloc[0],
            "n_productos": len(grupo_df),
            "n_marcas": sub["marca"].nunique(),
            "marca_mas_economica": barata["marca"],
            "es_marca_propia": bool(barata["es_marca_propia"]),
            "precio_unitario_economica": round(barata["precio_unitario"], 4),
            "marca_mas_cara": cara["marca"],
            "precio_unitario_cara": round(cara["precio_unitario"], 4),
            "mediana_grupo": round(mediana_grupo, 4),
            "ahorro_vs_mediana_pct": round((1 - barata["precio_unitario"] / mediana_grupo) * 100, 1),
            "veces_mas_cara": round(cara["precio_unitario"] / barata["precio_unitario"], 1),
        })
    return pd.DataFrame(filas).sort_values("n_productos", ascending=False).reset_index(drop=True)


def comparar_marca_propia(comparables):
    """En los grupos donde hay a la vez marca propia de PlazaVea y marcas comerciales, la mediana
    de `precio_relativo` de cada lado. Comparar dentro del grupo evita mezclar una papa con un
    suplemento."""
    con_ambas = comparables.groupby("grupo_comparable")["es_marca_propia"].transform("nunique") == 2
    sub = comparables[con_ambas]
    tabla = (
        sub.groupby(["grupo_comparable", "es_marca_propia"])["precio_relativo"]
        .median().unstack()
        .rename(columns={False: "comercial", True: "marca_propia"})
    )
    tabla["propia_mas_barata"] = tabla["marca_propia"] < tabla["comercial"]
    return tabla.round(3)


def concentracion_oh(df, por="categoria"):
    """Productos con precio exclusivo Oh! por grupo: cuántos hay, qué % del grupo tienen precio
    Oh! (`tasa_oh_pct`) y qué parte de todos los precios Oh! del catálogo concentra el grupo
    (`participacion_pct`)."""
    total_oh = df["tiene_precio_oh"].sum()
    tabla = df.groupby(por).agg(n=("tiene_precio_oh", "size"), con_oh=("tiene_precio_oh", "sum"))
    tabla["tasa_oh_pct"] = (tabla["con_oh"] / tabla["n"] * 100).round(1)
    tabla["participacion_pct"] = (tabla["con_oh"] / total_oh * 100).round(1)
    return tabla.sort_values("tasa_oh_pct", ascending=False)
