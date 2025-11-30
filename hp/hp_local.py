import time
import json
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

def scroll_para_imagenes(driver):
    """
    Hace un scroll rápido hacia abajo y luego sube un poco.
    Objetivo: Disparar el 'Lazy Loading' de las imágenes de HP.
    No necesitamos buscar botones, solo asegurarnos de que las imágenes carguen.
    """
    print("   -> Cargando imágenes (scroll)...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    

    for pos in range(0, last_height, 500):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(0.1)
    

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2) 

def extract_page_data(html_content):
    
    soup = BeautifulSoup(html_content, 'html.parser')
    page_products = []



    cards = soup.select('li.product-item')
    
    for card in cards:
        item = {}
        

        name_tag = card.select_one('a.product-item-link')
        if not name_tag:
            continue 
        item['name'] = name_tag.get_text(strip=True)
        



        price_tag = card.select_one('[data-price-type="finalPrice"] .price')
        if not price_tag:

            price_tag = card.select_one('.price-box .price')
            
        item['price'] = price_tag.get_text(strip=True) if price_tag else "No disponible"
        



        img_tag = card.select_one('img.product-image-photo')
        image_url = "No imagen"
        
        if img_tag:
            src = img_tag.get('src')

            if src and "placeholder" not in src and "lazy" not in src:
                image_url = src

            elif img_tag.get('data-src'):
                image_url = img_tag.get('data-src')
            elif img_tag.get('data-original'):
                image_url = img_tag.get('data-original')
                
        item['image_url'] = image_url
        

        item['url'] = name_tag.get('href')

        page_products.append(item)
        
    return page_products

def main():

    base_url = "https://www.hp.com/pe-es/shop/laptops.html"
    total_pages = 4 
    
    all_products = []
    driver = None

    try:
        print("--- Iniciando Scraping HP (Multi-página) ---")
        driver = setup_driver()

        for page in range(1, total_pages + 1):
            target_url = f"{base_url}?p={page}"
            print(f"\nProcesando Página {page}/{total_pages}: {target_url}")
            
            try:
                driver.get(target_url)
                

                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".product-items"))
                )
                

                scroll_para_imagenes(driver)
                

                current_products = extract_page_data(driver.page_source)
                print(f"   -> Encontrados: {len(current_products)} productos.")
                
                all_products.extend(current_products)
                
            except TimeoutException:
                print(f"   -> Error: Tiempo de espera agotado en página {page}.")
            except Exception as e:
                print(f"   -> Error inesperado en página {page}: {e}")


        output_file = 'hp_laptops_completo.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, indent=4, ensure_ascii=False)
            
        print(f"\nRESUMEN FINAL: Se extrajeron {len(all_products)} productos en total.")
        print(f"Datos guardados en: {output_file}")

    except Exception as e:
        print(f"Error Crítico: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()