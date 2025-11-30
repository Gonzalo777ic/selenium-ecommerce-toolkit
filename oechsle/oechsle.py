import time
import json
import random
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from bs4 import BeautifulSoup

def setup_driver():
    """Configuración optimizada para GCP/Docker (Headless)."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # User Agent para evitar bloqueos de VTEX/Cloudflare
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    chrome_options.add_argument("--log-level=3")
    
    service = Service(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scroll_oechsle(driver):
    """
    Scroll suave para Oechsle (VTEX).
    Es necesario bajar para que las imágenes 'lazy' (data-src) pasen a 'src'.
    """
    print("   -> Bajando para cargar imágenes...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    step = 400
    
    # Bajada progresiva
    for pos in range(0, last_height, step):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(0.1)
        
        # Recalcular altura si es necesario (infinite scroll mixto)
        if pos % 2000 == 0:
            last_height = driver.execute_script("return document.body.scrollHeight")

    # Scroll final y pequeña espera
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.5)

def extract_page_data(html_content):
    """
    Extrae datos de Oechsle basado en el snippet proporcionado.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    page_products = []

    # Selector principal basado en tu snippet
    cards = soup.select('div.resultItem')

    for card in cards:
        item = {}
        
        # --- NOMBRE ---
        # Opción 1: Atributo data-product-name del div principal
        name = card.get('data-product-name')
        if not name:
            # Opción 2: Etiqueta <p class="resultItem__detail--name">
            name_tag = card.select_one('.resultItem__detail--name')
            if name_tag:
                name = name_tag.get_text(strip=True)
        item['name'] = name if name else "Sin Nombre"
        
        # --- PRECIO ---
        # Oechsle tiene: Precio Lista, Precio Oferta, Precio Tarjeta Oh.
        # Priorizamos el "Precio Oferta" (El grande que no es tarjeta Oh).
        
        # Buscamos el contenedor de precios
        price_container = card.select_one('.resultItem__detail--price')
        price_text = "Agotado"
        
        if price_container:
            # Estrategia: Buscar el primer <span class="value"> dentro de un div .price
            # que NO sea .priceTOh (Precio tarjeta) ni .priceList (Precio lista tachado)
            
            # 1. Intento de precio oferta estándar (el más común)
            standard_price = price_container.select_one('.price:not(.priceList):not(.priceTOh) .value')
            
            # 2. Intento de precio con Tarjeta Oh (si es el único disponible o preferido)
            oh_price = price_container.select_one('.priceTOh .value')
            
            if standard_price:
                price_text = standard_price.get_text(strip=True)
            elif oh_price:
                price_text = oh_price.get_text(strip=True) + " (Tarjeta Oh!)"
            else:
                # Fallback: Buscar cualquier valor con "S/"
                all_prices = price_container.get_text()
                if "S/" in all_prices:
                    # Limpieza básica si falla lo anterior
                    import re
                    match = re.search(r'S/\s*[\d,.]+', all_prices)
                    if match:
                        price_text = match.group(0)

        item['price'] = price_text

        # --- IMAGEN ---
        # <img class="resultItem__image" src="...">
        img_tag = card.select_one('img.resultItem__image')
        image_url = "No imagen"
        
        if img_tag:
            src = img_tag.get('src')
            if src:
                image_url = src
                # A veces Oechsle usa imágenes placeholder. Si hay un data-src, úsalo.
                if "arquivos/ids" not in src and img_tag.get('data-src'):
                    image_url = img_tag.get('data-src')
            
        item['image_url'] = image_url
        
        # --- URL DEL PRODUCTO ---
        link_tag = card.select_one('a.resultItem__link')
        product_url = ""
        if link_tag:
            href = link_tag.get('href')
            if href:
                if href.startswith("http"):
                    product_url = href
                else:
                    product_url = "https://www.oechsle.pe" + href
        item['url'] = product_url
        
        # --- VENDEDOR ---
        seller_tag = card.select_one('.resultItem__by-seller')
        item['seller'] = seller_tag.get_text(strip=True) if seller_tag else "Oechsle"

        page_products.append(item)
        
    return page_products

def main():
    # URL base limpia (sin el srsltid de Google que expira)
    # Mantenemos el filtro fq que es la categoría
    base_url = "https://www.oechsle.pe/tecnologia/computo/laptops"
    # Query params constantes
    query_params = "fq=C%3A%2F160%2F168%2F209%2F" 
    
    total_pages = 10 
    all_products = []
    driver = None

    try:
        print("--- Iniciando Scraping Oechsle (10 Páginas) ---")
        driver = setup_driver()

        for page in range(1, total_pages + 1):
            # Construcción limpia de la URL
            target_url = f"{base_url}?{query_params}&page={page}"
            print(f"\nProcesando Página {page}/{total_pages}: {target_url}")
            
            try:
                driver.get(target_url)
                
                # Esperar a que cargue la lista de resultados
                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "resultItem"))
                    )
                except TimeoutException:
                    print("   -> Alerta: Tiempo de espera agotado (posible página vacía).")
                
                # Scroll para imágenes
                scroll_oechsle(driver)
                
                # Extraer
                current_products = extract_page_data(driver.page_source)
                count = len(current_products)
                print(f"   -> Encontrados: {count} productos.")
                
                if count == 0:
                    print("   -> Posible fin de paginación o bloqueo.")
                    # Opcional: break si estás seguro que 0 significa fin
                
                all_products.extend(current_products)
                
                # Pausa aleatoria
                sleep_time = random.uniform(2, 4)
                time.sleep(sleep_time)

            except Exception as e:
                print(f"   -> Error en página {page}: {e}")

        # Guardar todo
        output_file = 'oechsle_laptops.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, indent=4, ensure_ascii=False)
            
        print(f"\nRESUMEN: Se extrajeron {len(all_products)} productos en total.")
        print(f"Archivo guardado: {output_file}")

    except Exception as e:
        print(f"Error Crítico: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()