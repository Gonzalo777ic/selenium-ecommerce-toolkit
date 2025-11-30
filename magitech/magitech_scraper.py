import time
import json
import random
import re
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
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    chrome_options.add_argument("--log-level=3")
    


    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def scroll_magitech(driver):
    """
    Scroll para Magitech.
    Baja más lento para simular comportamiento humano.
    """
    print("   -> Bajando para cargar elementos...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    step = 400
    
    for pos in range(0, last_height, step):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(0.2) 
        
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.5)

def extract_page_data(html_content):
    """
    Extrae datos de Magitech (Magento 1.x) priorizando el precio 'Efectivo'.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    page_products = []


    cards = soup.select('li.item')

    for card in cards:
        item = {}
        


        name_tag = card.select_one('.product-name a')
        if not name_tag:
            continue 
            
        item['name'] = name_tag.get_text(strip=True)
        

        price_text = "Agotado"
        


        cash_price = card.select_one('.minimal-price-link .price')
        

        special_price = card.select_one('.special-price .price')
        

        regular_price = card.select_one('.regular-price .price')

        if cash_price:
            price_text = cash_price.get_text(strip=True) + " (Efectivo)"
        elif special_price:
            price_text = special_price.get_text(strip=True)
        elif regular_price:
            price_text = regular_price.get_text(strip=True)
        else:

            any_price = card.select_one('.price')
            if any_price:
                price_text = any_price.get_text(strip=True)

        item['price'] = price_text



        img_tag = card.select_one('a.product-image img')
        image_url = "No imagen"
        
        if img_tag:
            src = img_tag.get('src')
            if src:
                image_url = src
        
        item['image_url'] = image_url
        

        item['url'] = name_tag.get('href') if name_tag else ""
        



        sku_text = "No SKU"
        sku_span = card.find('span', string=re.compile(r'SKU'))
        if sku_span:
            sku_text = sku_span.get_text(strip=True).replace("SKU", "").strip()
        item['sku'] = sku_text

        page_products.append(item)
        
    return page_products

def main():
    base_url = "https://www.magitech.pe/laptops.html"
    total_pages = 3 
    all_products = []
    driver = None

    try:
        print("--- Iniciando Scraping Magitech (10 Páginas - Modo Robusto) ---")
        driver = setup_driver()

        for page in range(1, total_pages + 1):
            target_url = f"{base_url}?p={page}"
            

            max_retries = 3
            success = False
            
            for attempt in range(max_retries):
                print(f"\nProcesando Página {page}/{total_pages} (Intento {attempt + 1}): {target_url}")
                
                try:
                    driver.get(target_url)
                    

                    try:
                        WebDriverWait(driver, 30).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "li.item"))
                        )
                    except TimeoutException:
                        print("   -> Alerta: Tiempo de espera agotado. Verificando si es un error 404 o carga lenta...")

                        if "404" in driver.title:
                             print("   -> Error 404 detectado. Página no existe.")

                             break 
                    

                    scroll_magitech(driver)
                    

                    current_products = extract_page_data(driver.page_source)
                    count = len(current_products)
                    print(f"   -> Encontrados: {count} productos.")
                    
                    if count > 0:
                        all_products.extend(current_products)
                        success = True

                        time.sleep(random.uniform(3, 6)) 
                        break 
                    else:
                        print("   -> 0 productos encontrados. Posible fallo de carga.")
                        if attempt < max_retries - 1:
                            wait_time = random.uniform(8, 12)
                            print(f"   -> Esperando {wait_time:.1f}s antes de reintentar...")
                            time.sleep(wait_time)
                            driver.refresh() 
                
                except Exception as e:
                    print(f"   -> Error en intento {attempt + 1}: {e}")
                    time.sleep(5)

            if not success:
                print(f"   -> ADVERTENCIA: No se pudo extraer la página {page} después de {max_retries} intentos.")


        output_file = 'magitech_laptops.json'
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