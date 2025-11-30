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
    
    service = Service(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scroll_memorykings(driver):
    """
    Scroll para asegurar que las imágenes 'lazy' de Memory Kings se carguen.
    """
    print("   -> Bajando para cargar catálogo...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    step = 400
    
    for pos in range(0, last_height, step):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(0.1)
        
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.5)

def extract_category_data(html_content):
    """
    Extrae datos de Memory Kings basándose en la estructura de lista <li>.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    page_products = []
    base_url = "https://www.memorykings.pe"





    
    items = soup.select('li div a')
    
    for item_link in items:

        content_div = item_link.select_one('.content')
        if not content_div:
            continue

        item = {}
        


        title_tag = content_div.select_one('.title h4')
        item['name'] = title_tag.get_text(strip=True) if title_tag else "Sin Nombre"
        



        price_text = "Agotado"
        price_div = content_div.select_one('.price')
        
        if price_div:
            price_text = price_div.get_text(strip=True)
        else:


            pass
            
        item['price'] = price_text



        img_div = item_link.select_one('.image img')
        image_url = "No imagen"
        
        if img_div:
            src = img_div.get('src')
            if src:
                if not src.startswith('http'):
                    image_url = base_url + src if src.startswith('/') else base_url + '/' + src
                else:
                    image_url = src
        
        item['image_url'] = image_url
        

        href = item_link.get('href')
        product_url = ""
        if href:
            if not href.startswith('http'):
                product_url = base_url + href if href.startswith('/') else base_url + '/' + href
            else:
                product_url = href
        item['url'] = product_url
        


        stock_div = content_div.select_one('.stock')
        if stock_div:

            item['stock'] = stock_div.get_text(strip=True).replace("Stock:", "").strip()
        else:
            item['stock'] = "No especificado"
            

        code_div = content_div.select_one('.code')
        if code_div:
            item['internal_code'] = code_div.get_text(strip=True).replace("Código interno:", "").strip()

        page_products.append(item)
        
    return page_products

def main():

    categories = [
        "https://www.memorykings.pe/listados/247/laptops-intel-core-i3", 
        "https://www.memorykings.pe/listados/258/laptops-intel-core-i5",
        "https://www.memorykings.pe/listados/257/laptops-intel-core-i7",
        "https://www.memorykings.pe/listados/464/laptops-intel-core-ultra-5",
        "https://www.memorykings.pe/listados/927/laptops-intel-core-i9",
        "https://www.memorykings.pe/listados/465/laptops-intel-core-ultra-7",
        "https://www.memorykings.pe/listados/1263/laptops-intel-core-ultra-9"
    ]
    
    all_products = []
    driver = None

    try:
        print("--- Iniciando Scraping Memory Kings ---")
        driver = setup_driver()

        for url in categories:
            print(f"\nProcesando Categoría: {url}")
            
            try:
                driver.get(url)
                

                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "content"))
                    )
                except TimeoutException:
                    print("   -> Alerta: Tiempo de espera agotado (posible categoría vacía).")
                

                scroll_memorykings(driver)
                

                current_products = extract_category_data(driver.page_source)
                print(f"   -> Encontrados: {len(current_products)} productos.")
                
                all_products.extend(current_products)
                

                time.sleep(random.uniform(3, 5))

            except Exception as e:
                print(f"   -> Error procesando URL: {e}")


        output_file = 'memorykings_laptops.json'
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