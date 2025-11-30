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
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    chrome_options.add_argument("--log-level=3")
    
    service = Service(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scroll_realplaza(driver):
    """
    Scroll para Real Plaza (VTEX IO).
    Necesario para disparar el renderizado de los componentes de React.
    """
    print("   -> Bajando para renderizar componentes...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    step = 500
    
    for pos in range(0, last_height, step):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(0.15) # Un poco más lento para dar tiempo a React
        
        # Ajuste dinámico de altura
        if pos % 2000 == 0:
            last_height = driver.execute_script("return document.body.scrollHeight")

    # Scroll final y rebote para asegurar
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.5)
    driver.execute_script("window.scrollBy(0, -500);") # Rebote
    time.sleep(1)

def extract_page_data(html_content):
    """
    Extrae datos de Real Plaza (VTEX IO) usando selectores de clase específicos.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    page_products = []

    # Selector del contenedor de cada tarjeta de producto
    # VTEX IO suele usar esta clase para el wrapper principal del producto en listas
    cards = soup.select('.vtex-product-summary-2-x-container')
    
    # Si no encuentra por container, intenta por gallery item
    if not cards:
        cards = soup.select('.vtex-search-result-3-x-galleryItem')

    for card in cards:
        item = {}
        
        # --- NOMBRE ---
        # Clase típica: vtex-product-summary-2-x-productBrand
        name_tag = card.select_one('.vtex-product-summary-2-x-productBrand')
        item['name'] = name_tag.get_text(strip=True) if name_tag else "Sin Nombre"
        
        # --- PRECIO ---
        # Real Plaza tiene estructura compleja de precios custom
        price_text = "Agotado"
        
        # 1. Precio Tarjeta Oh! (Prioridad 1)
        oh_price = card.select_one('.realplaza-product-custom-0-x-productSummaryPrice__Option__ThirdPrice .realplaza-product-custom-0-x-productSummaryPrice__Option__Price span')
        
        # 2. Precio Online (o precio oferta estándar) (Prioridad 2)
        online_price = card.select_one('.realplaza-product-custom-0-x-productSummaryPrice__Option__OfferPrice .realplaza-product-custom-0-x-productSummaryPrice__Option__Price span')
        
        # 3. Precio Regular (Prioridad 3 - Solo si no hay oferta)
        regular_price = card.select_one('.realplaza-product-custom-0-x-productSummaryPrice__Option__RegularPrice .realplaza-product-custom-0-x-productSummaryPrice__Option__Price span')

        if oh_price:
            price_text = oh_price.get_text(strip=True) + " (Tarjeta Oh!)"
        elif online_price:
            price_text = online_price.get_text(strip=True)
        elif regular_price:
            price_text = regular_price.get_text(strip=True)
        else:
            # Fallback a clases genéricas de VTEX si las custom fallan
            generic_price = card.select_one('.vtex-product-summary-2-x-sellingPrice')
            if generic_price:
                price_text = generic_price.get_text(strip=True)

        item['price'] = price_text

        # --- IMAGEN ---
        # Clase: vtex-product-summary-2-x-imageNormal
        img_tag = card.select_one('img.vtex-product-summary-2-x-imageNormal')
        image_url = "No imagen"
        
        if img_tag:
            src = img_tag.get('src')
            if src:
                image_url = src
        
        item['image_url'] = image_url
        
        # --- URL DEL PRODUCTO ---
        # Generalmente hay un <a> con clase vtex-product-summary-2-x-clearLink
        link_tag = card.select_one('a.vtex-product-summary-2-x-clearLink')
        product_url = ""
        
        if link_tag:
            href = link_tag.get('href')
            if href:
                if href.startswith("http"):
                    product_url = href
                else:
                    product_url = "https://www.realplaza.com" + href
        else:
            # Búsqueda genérica de link si no tiene la clase clearLink
            generic_link = card.find('a', href=True)
            if generic_link:
                href = generic_link['href']
                if href.startswith("http"):
                    product_url = href
                else:
                    product_url = "https://www.realplaza.com" + href
                    
        item['url'] = product_url
        
        # --- VENDEDOR ---
        seller_tag = card.select_one('.realplaza-product-custom-0-x-sellerNameParagraph')
        item['seller'] = seller_tag.get_text(strip=True) if seller_tag else "Real Plaza"

        page_products.append(item)
        
    return page_products

def main():
    base_url = "https://www.realplaza.com/computacion/laptops"
    total_pages = 10 
    all_products = []
    driver = None

    try:
        print("--- Iniciando Scraping Real Plaza (10 Páginas) ---")
        driver = setup_driver()

        for page in range(1, total_pages + 1):
            target_url = f"{base_url}?page={page}"
            print(f"\nProcesando Página {page}/{total_pages}: {target_url}")
            
            try:
                driver.get(target_url)
                
                # Esperar a que cargue la grilla (clase de contenedor VTEX)
                try:
                    WebDriverWait(driver, 25).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "vtex-product-summary-2-x-container"))
                    )
                except TimeoutException:
                    print("   -> Alerta: Tiempo de espera agotado (posible página vacía).")
                
                # Scroll
                scroll_realplaza(driver)
                
                # Extraer
                current_products = extract_page_data(driver.page_source)
                count = len(current_products)
                print(f"   -> Encontrados: {count} productos.")
                
                all_products.extend(current_products)
                
                # Pausa
                sleep_time = random.uniform(2, 4)
                time.sleep(sleep_time)

            except Exception as e:
                print(f"   -> Error en página {page}: {e}")

        # Guardar
        output_file = 'realplaza_laptops.json'
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