# 📖 Diccionario de Datos — Dataset Final (`plazavea_final.csv`)

Este documento describe la estructura completa del dataset final `plazavea_final.csv`, integrando tanto las variables originales obtenidas durante las fases de extracción y limpieza como las nuevas variables creadas durante la etapa de **Ingeniería de Características**.

---

## I. Variables Heredadas (Extracción y Preprocesamiento)

| Variable | Descripción | Tipo de Dato | Rango / Valores Observados | Unidad |
| :--- | :--- | :--- | :--- | :--- |
| `id_producto` | Identificador único del producto generado a partir del slug de su URL. | Categórico (String) | Texto único por producto | - |
| `nombre` | Nombre comercial completo del producto, incluyendo marca y presentación. | Categórico (String) | Texto libre | - |
| `marca` | Marca comercial del producto, unificada y normalizada a mayúsculas. | Categórico (String) | Ej. `BELL'S`, `GLORIA`, `OREO`, `GENERICO` | - |
| `categoria` | Categoría principal del catálogo de PlazaVea desde la cual se extrajo. | Categórico (String) | `Abarrotes`, `Bebidas`, `Lácteos`, `Cuidado Personal`, etc. | - |
| `precio_venta` | Precio vigente de venta en soles al momento de la extracción (incluye oferta). | Numérico (Float) | 0.90 a 999.00 | Soles (S/) |
| `precio_regular` | Precio de lista en soles antes de aplicar descuentos promocionales. | Numérico (Float) | 0.90 a 999.00 | Soles (S/) |
| `tiene_precio_oh` | Indica si el producto cuenta con un precio exclusivo con Tarjeta Oh!. | Categórico (Bool) | `True`, `False` | - |
| `descuento_pct` | Porcentaje de descuento aplicado sobre el precio regular. | Numérico (Float) | 0.00 a 100.00 | Porcentaje (%) |
| `url_producto` | Dirección web directa a la página del producto en plazavea.com.pe. | Categórico (String) | URL (`https://www.plazavea.com.pe/...`) | - |
| `fecha_extraccion` | Marca temporal (*timestamp*) en que se realizó la recolección de los datos. | Fecha/Hora | `AAAA-MM-DD hh:mm:ss` | - |
| `tiene_descuento` | Indica si el producto cuenta con una oferta activa. | Categórico (Bool) | `True`, `False` | - |
| `ahorro_soles` | Monto absoluto de ahorro por unidad (`precio_regular - precio_venta`). | Numérico (Float) | 0.00 en adelante | Soles (S/) |
| `es_outlier_precio` | Indicador booleano de detección de valor atípico mediante el método IQR. | Categórico (Bool) | `True`, `False` | - |
| `macro_grupo` | Agrupación general de categorías para análisis a alto nivel. | Categórico (String) | Ej. `Alimentos`, `Bebidas`, `Limpieza` | - |

---

## II. Variables de Ingeniería de Características (Nuevas Características)

| Variable | Descripción | Tipo de Dato | Rango / Valores Observados | Unidad |
| :--- | :--- | :--- | :--- | :--- |
| `cantidad_base` | Contenido numérico extraído directamente del nombre del producto mediante expresiones regulares (peso, volumen o piezas). | Numérico (Float) | Valores mayores a 0 (ej. `100.0`, `500.0`, `1000.0`) | Gramos (g), Mililitros (ml) o Unidades |
| `tipo_unidad_medida` | Unidad estándar de referencia asignada para la normalización equitativa según la naturaleza del producto. | Categórico (String) | `100g`, `100ml`, `unidad`, `desconocido` | - |
| `precio_unitario_normalizado` | **Métrica clave de comparación justa:** Precio estandarizado por cada 100 gramos, 100 mililitros o por unidad individual. | Numérico (Float) | Valores continuos | Soles (S/) por unidad de medida |
| `rango_descuento` | Clasificación categórica según la magnitud del porcentaje de descuento. | Categórico (String) | `Sin descuento`, `Bajo (<10%)`, `Moderado (10%-25%)`, `Alto (>25%)` | - |