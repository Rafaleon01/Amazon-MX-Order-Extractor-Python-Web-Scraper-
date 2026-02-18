# Amazon-MX-Order-Extractor-Python-Web-Scraper- English Version
This is a Python script designed to automate the detailed extraction of your Amazon purchase history (specifically optimized for Amazon Mexico).

## Key Features

* **Multi-Page Extraction:** Define how many pages of your order history you want to scan, and the script will automatically paginate through them.
* **ASIN Precision Matching:** Prevents price mix-ups between different products in the same order. The script tracks the unique Amazon ID (ASIN) in the source code to ensure every price matches its corresponding product perfectly.
* **Visual Quantity Detection:** Captures exact quantities by extracting data from dynamic visual badges (`.product-image_qty`) directly from the grid view.
* **Exact Financial Calculation:** Calculates the exact line total (Quantity x Unit Price).
* **Clean CSV Output:** Generates a structured and properly ordered `.csv` file automatically, ready to be used in Excel, PowerBI, or any data analytics pipeline.

## ⚙️ How it Works (The "Neighborhood" Logic)

Amazon often hides or scrambles prices within the DOM. To bypass this, the script doesn't look for the price globally on the page. Instead:
1. It finds the link containing the product's **ASIN**.
2. It climbs up the HTML tree (using XPath `ancestor`) until it finds the "parent" container that wraps the entire row for that specific product.
3. It searches for the price **exclusively** inside that isolated box.

# 🛒 Amazon MX Order Extractor (Python Web Scraper) Versión en Español

Este es un script de Python diseñado para automatizar la extracción detallada de tu historial de compras de Amazon (optimizado para Amazon México).
## Características Principales

* **Extracción Multi-Página:** Define cuántas páginas de tu historial deseas escanear y el script navegará por ellas automáticamente.
* **Precisión por ASIN (Identificador Único):** Evita el cruce de precios de productos diferentes en un mismo pedido. El script rastrea el ID único de Amazon (ASIN) en el código fuente para asegurar que cada precio corresponda a su producto.
* **Detección Visual de Cantidades:** Captura las cantidades exactas extrayendo los datos de las etiquetas dinámicas (`.product-image_qty`) directamente desde la vista en cuadrícula.
* **Cálculo Financiero Exacto:** Calcula el total exacto por línea (Cantidad x Precio Unitario).
* **Salida Limpia en CSV:** Genera un archivo `.csv` estructurado y ordenado de forma automática, listo para ser utilizado en Excel, PowerBI o cualquier pipeline de análisis de datos.

## ⚙️ Cómo Funciona

Amazon suele ocultar o mezclar los precios en el DOM. Para solucionar esto, el script no busca el precio a nivel general en la página. En su lugar:
1. Encuentra el enlace con el **ASIN** del producto.
2. Sube por el árbol HTML (usando XPath `ancestor`) hasta encontrar el contenedor "padre" que engloba toda la fila de ese producto específico.
3. Busca el precio **exclusivamente** dentro de esa caja aislada.


## 🚀 Requirements and Installation / Requisitos e Instalación
You will need Python installed on your machine along with the following libraries / Necesitarás Python instalado en tu computadora y las siguientes librerías:

```bash
pip install selenium webdriver-manager
