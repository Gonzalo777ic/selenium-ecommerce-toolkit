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

def scroll_infotec(driver):
    """
    Scroll para Infotec (PrestaShop).
    Baja para asegurar que el Lazy Load de las imágenes (data-src) se active.
    """
    print("   -> Bajando para cargar imágenes...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    step = 400
    
    for pos in range(0, last_height, step):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(0.1) 
        
        if pos % 2000 == 0:
            last_height = driver.execute_script("return document.body.scrollHeight")

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)

def extract_page_data(html_content):
    """
    Extrae datos de Infotec usando selectores estándar de PrestaShop.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    page_products = []


    cards = soup.select('article.product-miniature')

    for card in cards:
        item = {}
        


        name_tag = card.select_one('.product-title a')
        item['name'] = name_tag.get_text(strip=True) if name_tag else "Sin Nombre"
        


        price_tag = card.select_one('.product-price')
        item['price'] = price_tag.get_text(strip=True) if price_tag else "Agotado"




        img_tag = card.select_one('img.product-thumbnail-first')
        image_url = "No imagen"
        
        if img_tag:

            if img_tag.get('data-src'):
                image_url = img_tag.get('data-src')

            elif img_tag.get('src'):
                image_url = img_tag.get('src')
        
        item['image_url'] = image_url
        


        link_tag = card.select_one('.thumbnail.product-thumbnail')
        if not link_tag:
             link_tag = card.select_one('.product-title a')

        item['url'] = link_tag.get('href') if link_tag else ""
        

        brand_tag = card.select_one('.product-brand a')
        item['brand'] = brand_tag.get_text(strip=True) if brand_tag else "Genérico"

        page_products.append(item)
        
    return page_products

def main():
    base_url = "https://www.infotec.com.pe/10-laptop"
    total_pages = 3 
    
    all_products = []
    driver = None

    try:
        print("--- Iniciando Scraping Infotec (3 Páginas) ---")
        driver = setup_driver()

        for page in range(1, total_pages + 1):
            target_url = f"{base_url}?page={page}"
            print(f"\nProcesando Página {page}/{total_pages}: {target_url}")
            
            try:
                driver.get(target_url)
                

                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "product-miniature"))
                    )
                except TimeoutException:
                    print("   -> Alerta: Tiempo de espera agotado.")
                

                scroll_infotec(driver)
                

                current_products = extract_page_data(driver.page_source)
                print(f"   -> Encontrados: {len(current_products)} productos.")
                
                all_products.extend(current_products)
                

                time.sleep(random.uniform(2, 4))

            except Exception as e:
                print(f"   -> Error en página {page}: {e}")


        output_file = 'infotec_laptops.json'
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