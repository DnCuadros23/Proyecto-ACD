"""Extracción del catálogo de PlazaVea: el scraper de la Parte I (notebooks/Proyecto_.ipynb,
secciones 1-10) empaquetado como función, para que run_pipeline.py lo pueda invocar con
`--scrape`. Usa Selenium para renderizar el catálogo (se arma con JavaScript) y BeautifulSoup
para parsear el HTML resultante; recorre cada categoría por paginación real (`?page=N`), no por
scroll infinito, que tiene un techo fijo. Tarda varias horas en correr completo, así que no se
ejecuta por defecto.
"""
import re
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

BASE = "https://www.plazavea.com.pe"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

CATEGORIAS = {
    "abarrotes": f"{BASE}/abarrotes",
    "bebidas": f"{BASE}/bebidas",
    "lacteos": f"{BASE}/lacteos-y-huevos",
    "limpieza": f"{BASE}/cuidado-del-hogar",
    "cuidado-personal": f"{BASE}/cuidado-personal",
    "frutas-verduras": f"{BASE}/frutas-y-verduras",
    "carnes-pescados": f"{BASE}/carnes-aves-y-pescados",
    "desayunos": f"{BASE}/desayunos",
    "quesos-fiambres": f"{BASE}/quesos-y-fiambres",
    "panaderia": f"{BASE}/panaderia-y-pasteleria",
    "congelados": f"{BASE}/congelados",
}

# Cada campo tiene varios selectores candidatos, en orden de preferencia: si el sitio cambia una
# clase CSS, el resultado se degrada en vez de romper la corrida entera.
SELECTORES = {
    "tarjeta": [
        "div.Showcase__content", "div[class*='Showcase__content']", "div.Showcase",
        "div.shelf-item", "article[class*='product']", "li[class*='product-item']",
    ],
    "nombre": [
        "a.Showcase__name", ".Showcase__name", "[class*='Showcase__name']",
        "h2 a", "[class*='productName']",
    ],
    "marca": [".Showcase__brand", "[class*='brand']"],
    "precio_venta": [".Showcase__salePrice", "[class*='salePrice']", "[class*='sellingPrice']",
                      "[class*='bestPrice']"],
    "precio_regular": [".Showcase__oldPrice", "[class*='oldPrice']", "[class*='listPrice']", "del"],
    "precio_oh": ["[class*='ohPrice']", "[class*='priceOh']", "[class*='cardPrice']"],
    "enlace": ["a.Showcase__link", "a[href*='/p']", "a[href]"],
}
ATRIBUTOS_IMAGEN = ["src", "data-src", "data-original", "data-lazy-src", "data-lazy"]
MIN_TARJETAS = 3


def crear_driver(headless=True, ancho=1400, alto=1000):
    """Abre Chrome con un user-agent realista y sin la señal `navigator.webdriver` que algunos
    sitios usan para detectar bots."""
    opciones = Options()
    if headless:
        opciones.add_argument("--headless=new")
    opciones.add_argument(f"--window-size={ancho},{alto}")
    opciones.add_argument(f"--user-agent={UA}")
    opciones.add_argument("--disable-blink-features=AutomationControlled")
    opciones.add_argument("--lang=es-PE")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opciones)
    driver.set_page_load_timeout(60)
    return driver


def cerrar_modales(driver, espera=1.0):
    """Cierra el aviso de cookies y el modal de dirección de entrega si están abiertos."""
    cerrados = []
    candidatos = [
        (By.ID, "onetrust-accept-btn-handler"),
        (By.CSS_SELECTOR, "button[id*='accept']"),
        (By.CSS_SELECTOR, "button[class*='accept']"),
        (By.CSS_SELECTOR, "[class*='modal'] [class*='close']"),
        (By.CSS_SELECTOR, "button[aria-label='Close']"),
    ]
    for by, sel in candidatos:
        try:
            WebDriverWait(driver, espera).until(EC.element_to_be_clickable((by, sel))).click()
            cerrados.append(sel)
            time.sleep(0.5)
        except Exception:
            continue
    return cerrados


def seleccionar_tarjetas(soup):
    """Se queda con el selector de tarjeta que más coincidencias trae en esta página."""
    mejor, mejor_sel = [], None
    for sel in SELECTORES["tarjeta"]:
        t = soup.select(sel)
        if len(t) > len(mejor):
            mejor, mejor_sel = t, sel
    return (mejor, mejor_sel) if len(mejor) >= MIN_TARJETAS else ([], None)


def contar_tarjetas(driver):
    mejor = 0
    for sel in SELECTORES["tarjeta"]:
        try:
            mejor = max(mejor, len(driver.find_elements(By.CSS_SELECTOR, sel)))
        except Exception:
            continue
    return mejor if mejor >= MIN_TARJETAS else 0


def desplazar_para_cargar_imagenes(driver, paso=700, pausa=0.5):
    """Baja la página en pasos pequeños para que el lazy-loading de cada foto tenga tiempo de
    disparar su carga (un salto directo al final deja la mayoría de imágenes sin `src`)."""
    alto = driver.execute_script("return document.body.scrollHeight")
    pos = 0
    while pos < alto:
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(pausa)
        pos += paso
        alto = driver.execute_script("return document.body.scrollHeight")


def construir_url_pagina(url_categoria, pagina, tamano_pagina=100):
    """Paginación real del catálogo (parámetros `PS`/`page`): a diferencia del scroll infinito,
    cada página trae productos distintos, sin techo fijo."""
    separador = "&" if "?" in url_categoria else "?"
    return f"{url_categoria}{separador}PS={tamano_pagina}&page={pagina}"


def primer_texto(nodo, candidatos):
    """Primer selector de la lista que devuelva texto no vacío."""
    for sel in candidatos:
        el = nodo.select_one(sel)
        if el:
            txt = el.get_text(" ", strip=True)
            if txt:
                return txt
    return None


def a_numero(texto):
    """'S/ 1,299.90' -> 1299.90 (formato peruano: coma de miles, punto decimal)."""
    if not texto:
        return None
    m = re.search(r"(\d[\d.,]*)", texto.replace(" ", ""))
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def primera_imagen(tarjeta):
    """El catálogo usa lazy-loading: la imagen real a veces no está en `src` sino en un
    atributo `data-*`; se prueban varios en cascada antes de dar la imagen por ausente."""
    for img in tarjeta.select("img"):
        for attr in ATRIBUTOS_IMAGEN:
            val = img.get(attr)
            if val and not val.startswith("data:"):
                return val
    fuente = tarjeta.select_one("picture source[srcset]")
    if fuente and fuente.get("srcset"):
        return fuente["srcset"].split(",")[0].strip().split(" ")[0]
    return None


def extraer_tarjeta(tarjeta, categoria):
    """Convierte una tarjeta HTML en una fila del dataset."""
    nombre = primer_texto(tarjeta, SELECTORES["nombre"])

    enlace = None
    for s in SELECTORES["enlace"]:
        a = tarjeta.select_one(s)
        if a and a.get("href"):
            enlace = a["href"]
            break
    if enlace and enlace.startswith("/"):
        enlace = BASE + enlace

    imagen = primera_imagen(tarjeta)
    precio_venta = a_numero(primer_texto(tarjeta, SELECTORES["precio_venta"]))
    precio_regular = a_numero(primer_texto(tarjeta, SELECTORES["precio_regular"]))
    precio_oh = a_numero(primer_texto(tarjeta, SELECTORES["precio_oh"]))

    # Red de seguridad: si los selectores de precio fallan, se leen todos los "S/" del texto
    # de la tarjeta y se toma el menor como precio de venta.
    if precio_venta is None:
        montos = [a_numero(m) for m in re.findall(r"S/\s*[\d.,]+", tarjeta.get_text(" ", strip=True))]
        montos = [m for m in montos if m]
        if montos:
            precio_venta = min(montos)
            precio_regular = precio_regular or (max(montos) if len(montos) > 1 else None)

    # Sin oferta activa, el precio regular es el mismo precio de venta (0% de descuento, no nulo).
    descuento = 0.0
    if precio_venta and precio_regular and precio_regular > precio_venta:
        descuento = round((1 - precio_venta / precio_regular) * 100, 2)
    else:
        precio_regular = precio_venta

    sku = None
    if enlace:
        m = re.search(r"/(\d{4,})/?p?/?$", enlace) or re.search(r"/([^/]+)/p$", enlace)
        sku = m.group(1) if m else None

    return {
        "sku": sku,
        "nombre": nombre,
        "marca": primer_texto(tarjeta, SELECTORES["marca"]),
        "categoria": categoria,
        "precio_venta": precio_venta,
        "precio_regular": precio_regular,
        "tiene_precio_oh": precio_oh is not None,
        "descuento_pct": descuento,
        "url_producto": enlace,
        "url_imagen": imagen,
        "fecha_extraccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def scrapear_categoria(driver, url, categoria, max_productos=150, max_paginas=15, intentos=3, pausa=2.0,
                        verbose=True):
    """Recorre una categoría página por página hasta agotar `max_productos`, llegar a
    `max_paginas` o encontrar una página sin productos nuevos (fin del catálogo)."""
    vistos, filas = set(), []

    for pagina in range(1, max_paginas + 1):
        url_pagina = construir_url_pagina(url, pagina)
        cargo = False

        for intento in range(1, intentos + 1):
            try:
                if verbose:
                    print(f"[{categoria}] página {pagina} intento {intento} -> {url_pagina}")
                driver.get(url_pagina)
                WebDriverWait(driver, 30).until(lambda d: d.execute_script("return document.readyState") == "complete")
                cerrar_modales(driver)
                time.sleep(pausa)
                if contar_tarjetas(driver) == 0:
                    raise ValueError("cero tarjetas")
                cargo = True
                break
            except Exception as e:
                if pagina > 1:
                    # en páginas > 1, cero tarjetas suele ser el final natural del catálogo
                    break
                print(f"[{categoria}] falló intento {intento}: {type(e).__name__}: {e}")
                time.sleep(pausa * intento * 2)

        if not cargo:
            if pagina == 1:
                print(f"[{categoria}] se abandona la categoría: no responde ni la página 1")
            elif verbose:
                print(f"[{categoria}] fin del catálogo en la página {pagina}")
            break

        desplazar_para_cargar_imagenes(driver)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        tarjetas, sel = seleccionar_tarjetas(soup)

        nuevas = 0
        for t in tarjetas:
            fila = extraer_tarjeta(t, categoria)
            if not fila["nombre"] or not fila["url_producto"]:
                continue
            if fila["url_producto"] in vistos:
                continue
            vistos.add(fila["url_producto"])
            filas.append(fila)
            nuevas += 1

        if verbose:
            print(f"[{categoria}] selector={sel} | tarjetas={len(tarjetas)} | nuevas={nuevas} | total={len(filas)}")

        if nuevas == 0 or len(filas) >= max_productos:
            break
        time.sleep(1)

    return filas[:max_productos]


def ejecutar_scraping(categorias=None, max_productos=150, headless=True, carpeta_salida="data/raw"):
    """Extrae todas las categorías y guarda un CSV parcial por categoría más el crudo
    consolidado y deduplicado (`plazavea_crudo_<timestamp>.csv`). Devuelve la ruta del crudo.
    Tarda varias horas: solo se llama con `python run_pipeline.py --scrape`.
    """
    categorias = categorias or CATEGORIAS
    carpeta = Path(carpeta_salida)
    carpeta.mkdir(parents=True, exist_ok=True)

    driver = crear_driver(headless=headless)
    todo = []
    try:
        for cat, url in categorias.items():
            filas = scrapear_categoria(driver, url, cat, max_productos=max_productos)
            if filas:
                pd.DataFrame(filas).to_csv(carpeta / f"parcial_{cat}.csv", index=False, encoding="utf-8-sig")
                todo.extend(filas)
            time.sleep(3)
    finally:
        driver.quit()

    df = pd.DataFrame(todo).drop_duplicates(subset="url_producto").reset_index(drop=True)
    marca = datetime.now().strftime("%Y%m%d_%H%M")
    ruta = carpeta / f"plazavea_crudo_{marca}.csv"
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    print(f"\nextracción terminada: {len(df)} filas -> {ruta}")
    return ruta
