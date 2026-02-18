import csv
import time
import os
import re
import random
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN ---
chrome_options = Options()
# chrome_options.add_argument("--headless") 
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# --- UTILIDADES VISUALES ---
def print_header(text):
    print("\n" + "═"*70)
    print(f" {text}")
    print("═"*70)

def print_step(step, text):
    print(f"\n📍 PASO {step}: {text}")

def clean_price(price_text):
    if not price_text: return 0.0
    clean = re.sub(r'[^\d.]', '', price_text)
    try: return float(clean)
    except: return 0.0

def extract_asin(url):
    """Extrae ASIN (ID Producto) de la URL"""
    if not url: return None
    match = re.search(r'/(?:dp|product)/([A-Z0-9]{10})', url)
    return match.group(1) if match else None

def find_details_link(card_element):
    """Busca enlace de detalles tolerante a fallos"""
    strategies = [
        ("css", "a.yohtmlc-order-details-link"),
        ("xpath", ".//a[contains(text(), 'detalles') or contains(text(), 'details')]"),
        ("xpath", ".//a[contains(@href, 'order-details')]")
    ]
    for method, selector in strategies:
        try:
            if method == "css": el = card_element.find_element(By.CSS_SELECTOR, selector)
            else: el = card_element.find_element(By.XPATH, selector)
            return el.get_attribute('href')
        except: pass
    return None

try:
    # 1. PREPARAR CARPETA
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    folder = os.path.join(desktop, "Pedidos")
    if not os.path.exists(folder): os.makedirs(folder)

    # 2. INICIO
    print_header("AMAZON - CAPTURA DE PEDIDOS")
    driver.get('https://www.amazon.com.mx/gp/css/order-history?ref_=nav_orders_first')
    
    print("🔑 ACCIÓN REQUERIDA: Inicia sesión en el navegador.")
    input("👉 Presiona ENTER aquí cuando veas la lista de 'Mis Pedidos'... ")

    # --- PREGUNTA DE PÁGINAS ---
    while True:
        try:
            pages_to_scan = int(input("\n📄 ¿Hasta que página de pedidos desea escanear? (Ingresa número): "))
            if pages_to_scan > 0: break
        except:
            print("   ⚠️ Por favor ingresa un número válido.")

    # ---------------------------------------------------------
    # FASE 1: ESCANEO DE LISTA (MULTI-PÁGINA)
    # ---------------------------------------------------------
    all_orders_data = []
    
    for current_page in range(1, pages_to_scan + 1):
        print_step(1, f"Escaneando Página {current_page} de {pages_to_scan}...")
        
        # Esperar a que carguen las tarjetas
        time.sleep(3) 
        order_cards = driver.find_elements(By.CSS_SELECTOR, 'div.a-box-group')
        
        print(f"   ℹ️  Página {current_page}: Detectadas {len(order_cards)} tarjetas.")
        print("   " + "-"*60)
        print(f"   {'CANT':<6} | {'PRODUCTO (Recortado)':<50}")
        print("   " + "-"*60)

        page_has_data = False

        for card in order_cards:
            try:
                card_text = card.text
                
                # ID y Fecha
                id_match = re.search(r'[A-Z0-9]{3}-\d{7}-\d{7}', card_text)
                order_id = id_match.group(0) if id_match else "N/A"
                
                date_match = re.search(r'(\d{1,2}\s+de\s+[a-zA-Z]+\s+de\s+\d{4})', card_text)
                order_date = date_match.group(0) if date_match else "N/A"

                # Enlace de detalle
                detail_url = find_details_link(card)
                is_digital = False if detail_url else True

                # Productos
                product_links = card.find_elements(By.XPATH, ".//a[contains(@href, '/dp/') or contains(@href, '/product/')]")
                seen_asins = set()

                for link in product_links:
                    p_url = link.get_attribute('href')
                    asin = extract_asin(p_url)
                    name = link.text.strip()

                    if not asin or asin in seen_asins: continue
                    if not name: continue 

                    seen_asins.add(asin)
                    page_has_data = True

                    # Cantidad Visual
                    qty = 1
                    try:
                        row_context = link.find_element(By.XPATH, "./../../../../..")
                        badges = row_context.find_elements(By.CSS_SELECTOR, ".product-image__qty") # Siempre asegurarse que aqui tiene doble guion bajo
                        if badges:
                            qty = int(badges[0].text.strip())
                    except: pass

                    all_orders_data.append({
                        'ID': order_id,
                        'Fecha': order_date,
                        'Producto': name,
                        'ASIN': asin,
                        'Link_Detalle': detail_url,
                        'Cantidad': qty,
                        'Precio': 0.0,
                        'Pago': "N/A",
                        'Es_Digital': is_digital
                    })
                    
                    prod_short = (name[:48] + '..') if len(name) > 48 else name
                    print(f"   {qty:<6} | {prod_short:<50}")

            except: continue
        
        # --- LÓGICA DE PAGINACIÓN ---
        if current_page < pages_to_scan:
            try:
                # Buscar el botón "Siguiente" (Clase .a-last)
                print(f"\n   ➡️ Buscando botón 'Siguiente' para ir a la página {current_page + 1}...")
                next_button = driver.find_element(By.CSS_SELECTOR, "li.a-last a")
                next_button.click()
                
                # Pausa de seguridad para evitar bloqueos
                time.sleep(random.uniform(3, 5))
            except:
                print("   ⚠️ No se encontró el botón 'Siguiente' (Fin del historial).")
                break
        else:
            print("\n   ✅ Escaneo de páginas completado.")

    # ---------------------------------------------------------
    # FASE 2: DETALLES (ITERAR SOBRE TODOS LOS ACUMULADOS)
    # ---------------------------------------------------------
    physical_items = [x for x in all_orders_data if not x['Es_Digital']]
    print_step(2, f"Extrayendo precios de {len(physical_items)} productos físicos...")
    
    details_cache = {}
    processed_count = 0
    total_to_process = len(all_orders_data)
    
    for item in all_orders_data:
        processed_count += 1
        progress = f"[{processed_count}/{total_to_process}]"
        
        # Saltar digitales
        if item['Es_Digital']: continue

        url = item['Link_Detalle']
        
        # Cache Check
        if url in details_cache:
            cache = details_cache[url]
            item['Pago'] = cache['pago']
            if item['ASIN'] in cache['precios']:
                item['Precio'] = cache['precios'][item['ASIN']]
            continue

        # Navegación
        driver.get(url)
        time.sleep(random.uniform(1.5, 2.5))
        
        current_pago = "N/A"
        current_precios = {}

        try:
            # Pago
            try:
                body = driver.find_element(By.TAG_NAME, "body").text
                pay_match = re.search(r'(?:terminada|terminado|ending) (?:en|in)?\s?(\d{4})', body, re.IGNORECASE)
                if pay_match: current_pago = pay_match.group(1)
            except: pass

            # Precios por ASIN
            d_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/dp/') or contains(@href, '/product/')]")
            for dl in d_links:
                try:
                    dasin = extract_asin(dl.get_attribute('href'))
                    if not dasin: continue
                    
                    d_cont = dl.find_element(By.XPATH, "./../../../../..")
                    p_found = 0.0
                    
                    try:
                        p_els = d_cont.find_elements(By.CSS_SELECTOR, ".a-color-price")
                        for p in p_els:
                            val = clean_price(p.text)
                            if val > 0: 
                                p_found = val
                                break
                    except: pass
                    
                    if p_found == 0:
                        m = re.search(r'\$\s?([\d,]+\.\d{2})', d_cont.text)
                        if m: p_found = clean_price(m.group(0))

                    if p_found > 0: current_precios[dasin] = p_found
                except: continue
            
            details_cache[url] = {'pago': current_pago, 'precios': current_precios}
            
            item['Pago'] = current_pago
            if item['ASIN'] in current_precios:
                item['Precio'] = current_precios[item['ASIN']]
                print(f"   🟢 {progress} ${item['Precio']:<8} | {item['Producto'][:40]}...")
            else:
                print(f"   🟡 {progress} No hallado | {item['Producto'][:40]}...")

        except:
            print(f"   🔴 {progress} Error     | {item['Producto'][:40]}...")

    # ---------------------------------------------------------
    # GUARDAR Y RESUMEN
    # ---------------------------------------------------------
    print_step(3, "Generando reporte final...")
    
    final_rows = []
    grand_total = 0.0

    for item in all_orders_data:
        line_total = item['Cantidad'] * item['Precio']
        grand_total += line_total
        
        unit_str = f"${item['Precio']:,.2f}" if item['Precio'] > 0 else "N/A"
        total_str = f"${line_total:,.2f}" if line_total > 0 else "N/A"

        final_rows.append({
            'Producto': item['Producto'],
            'Metodo de pago': item['Pago'],
            'Fecha': item['Fecha'],
            'Número de orden': item['ID'],
            'Cantidad': item['Cantidad'],
            'Costo unitario': unit_str,
            'Total': total_str,
            'ASIN': item['ASIN']
        })

    if final_rows:
        csv_path = os.path.join(folder, "amazon_pedidos_multipage.csv")
        headers = ['Producto', 'Metodo de pago', 'Fecha', 'Número de orden', 'Cantidad', 'Costo unitario', 'Total', 'ASIN']
        
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(final_rows)
        
        print("\n" + "═"*70)
        print(" ✅  PROCESO COMPLETADO EXITOSAMENTE")
        print("═"*70)
        print(f" 📂 Archivo guardado en: {csv_path}")
        print(f" 📦 Total Productos:     {len(final_rows)}")
        print(f" 💰 Monto Total:         ${grand_total:,.2f}")
        print("═"*70)
        
        os.system(f"open '{folder}'")

except Exception as e:
    print("\n" + "═"*70)
    print(f" ❌ ERROR FATAL: {e}")
    print("═"*70)