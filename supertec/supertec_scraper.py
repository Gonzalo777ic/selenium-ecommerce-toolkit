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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
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

def scroll_supertec(driver):
    """
    Scroll para asegurar carga de imágenes.
    """
    print("   -> Bajando para cargar catálogo...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    step = 400
    
    for pos in range(0, last_height, step):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(0.1)
        
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)

def extract_products(html_content):
    """
    Extrae datos y FILTRA la basura (enlaces de marcas).
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    page_products = []
    base_url = "https://supertec.com.pe/"


    cards = soup.select('a.prods')

    for card in cards:
        item = {}
        

        href = card.get('href')
        product_url = ""
        if href:
            if not href.startswith('http'):
                product_url = base_url + href
            else:
                product_url = href
        

        if "productos-por-marcas" in product_url:
            continue

        item['url'] = product_url


        name_tag = card.select_one('.nproducts')
        if not name_tag:
            continue 
        item['name'] = name_tag.get_text(strip=True)
        

        price_text = "Agotado"
        price_tag = card.select_one('.precioactual')
        
        if price_tag:
            raw_price = price_tag.get_text(strip=True)

            if "S/." in raw_price:
                parts = raw_price.split('|')
                for part in parts:
                    if "S/." in part:
                        price_text = part.strip()
            else:
                price_text = raw_price
        
        item['price'] = price_text


        img_tag = card.select_one('img.img80')
        image_url = "No imagen"
        
        if img_tag:
            src = img_tag.get('src')
            if src:
                if not src.startswith('http'):
                    image_url = base_url + src if not src.startswith('/') else base_url + src[1:]
                else:
                    image_url = src
        
        item['image_url'] = image_url
        

        stock_tag = card.select_one('.stock strong')
        item['stock'] = stock_tag.get_text(strip=True) if stock_tag else "No especificado"

        page_products.append(item)
        
    return page_products

def main():
    start_url = "https://supertec.com.pe/productos-categorias/1/PORTATILES"
    all_products = []
    driver = None

    try:
        print("--- Iniciando Scraping Supertec (Navegación AJAX) ---")
        driver = setup_driver()
        
        print(f"Cargando sitio principal: {start_url}")
        driver.get(start_url)
        

        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "prods"))
            )
        except TimeoutException:
            print("Alerta: No cargaron productos iniciales.")


        print("\nProcesando Página 1...")
        scroll_supertec(driver) 
        

        products_p1 = extract_products(driver.page_source)
        print(f"   -> Encontrados (limpios): {len(products_p1)}")
        all_products.extend(products_p1)


        print("\nIntentando ir a la Página 2...")
        try:


            next_page_btn = driver.find_element(By.XPATH, "//li[contains(@class, 'paginate')]/a[text()='2']")
            

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_page_btn)
            time.sleep(1)
            

            next_page_btn.click()
            print("   -> Click realizado en página 2. Esperando carga AJAX...")
            


            time.sleep(5) 
            

            

            scroll_supertec(driver)
            

            products_p2 = extract_products(driver.page_source)
            print(f"   -> Encontrados en P2 (limpios): {len(products_p2)}")
            


            existing_urls = set(p['url'] for p in all_products)
            new_products_count = 0
            
            for p in products_p2:
                if p['url'] not in existing_urls:
                    all_products.append(p)
                    new_products_count += 1
            
            print(f"   -> Nuevos productos agregados: {new_products_count}")

        except NoSuchElementException:
            print("   -> No se encontró el botón de la página 2 (¿Quizás solo hay una página?).")
        except Exception as e:
            print(f"   -> Error intentando cambiar de página: {e}")


        output_file = 'supertec_laptops.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, indent=4, ensure_ascii=False)
            
        print(f"\nRESUMEN: Se extrajeron {len(all_products)} productos válidos.")
        print(f"Archivo guardado: {output_file}")

    except Exception as e:
        print(f"Error Crítico: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()