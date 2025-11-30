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

def scroll_asus(driver):
    """
    Scroll profundo para ASUS.
    ASUS carga muchas imágenes de alta calidad, es vital bajar lento.
    """
    print("   -> Bajando para cargar catálogo ASUS...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    

    step = 400
    for pos in range(0, last_height, step):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(0.1)
        


        if pos % 1500 == 0:
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height > last_height:
                last_height = new_height

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    driver.execute_script("window.scrollBy(0, -600);") 
    time.sleep(1)

def extract_category_data(html_content, category_name):
    """
    Extrae datos usando Regex para manejar las clases dinámicas de ASUS (ej: __1HpeZ).
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    page_products = []


    cards = soup.find_all('div', class_=re.compile(r'ProductCardNormalGrid__productCardContainer'))

    for card in cards:
        item = {}
        item['category'] = category_name 
        



        name_tag = card.find('h2')
        if not name_tag:

            link_heading = card.find('a', class_=re.compile(r'ProductCardNormalGrid__headingRow'))
            if link_heading:
                name_tag = link_heading.find('h2')
        
        if name_tag:

            item['name'] = name_tag.get_text(" ", strip=True) 
        else:
            item['name'] = "Sin Nombre"
        

        price_text = "Agotado"
        

        discount_price = card.find('div', class_=re.compile(r'ProductCardNormalGrid__priceDiscount'))
        

        regular_price = card.find('div', class_=re.compile(r'ProductCardNormalGrid__regularPrice'))
        

        generic_price = card.find('div', class_=re.compile(r'ProductCardNormalGrid__price__'))

        if discount_price:
            price_text = discount_price.get_text(strip=True)
        elif generic_price:
            price_text = generic_price.get_text(strip=True)
        elif regular_price: 
            price_text = regular_price.get_text(strip=True)

        item['price'] = price_text



        img_wrapper = card.find('div', class_=re.compile(r'ProductCardNormalGrid__imageWrapper'))
        image_url = "No imagen"
        
        if img_wrapper:
            img_tag = img_wrapper.find('img')
            if img_tag:
                src = img_tag.get('src')
                if src:
                    image_url = src
        
        item['image_url'] = image_url
        


        link_tag = card.find('a', class_=re.compile(r'ProductCardNormalGrid__headingRow'))
        if not link_tag:
             link_tag = card.find('a', class_=re.compile(r'ProductCardNormalGrid__mainImageRow'))
             
        product_url = ""
        if link_tag and link_tag.get('href'):
            product_url = link_tag.get('href')

            if not product_url.startswith('http'):

                 if product_url.startswith('/'):
                     product_url = "https://rog.asus.com" + product_url
        
        item['url'] = product_url

        page_products.append(item)
        
    return page_products

def main():

    categories = [
        {
            "name": "ROG Zephyrus",
            "url": "https://www.asus.com/pe/laptops/for-gaming/rog-republic-of-gamers/filter?SubSeries=ROG-Zephyrus"
        },
        {
            "name": "ROG Flow",
            "url": "https://www.asus.com/pe/laptops/for-gaming/rog-republic-of-gamers/filter?SubSeries=ROG-Flow"
        },
        {
            "name": "ROG Strix",
            "url": "https://www.asus.com/pe/laptops/for-gaming/rog-republic-of-gamers/filter?SubSeries=ROG-Strix"
        }
    ]
    
    all_products = []
    driver = None

    try:
        print("--- Iniciando Scraping ASUS ROG (Por Categorías) ---")
        driver = setup_driver()

        for cat in categories:
            print(f"\nProcesando Categoría: {cat['name']}")
            print(f"URL: {cat['url']}")
            
            try:
                driver.get(cat['url'])
                


                try:
                    WebDriverWait(driver, 25).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='ProductCardNormalGrid__productCardContainer']"))
                    )
                except TimeoutException:
                    print(f"   -> Alerta: No se detectaron productos en {cat['name']} (Timeout).")
                

                scroll_asus(driver)
                

                current_products = extract_category_data(driver.page_source, cat['name'])
                print(f"   -> Encontrados: {len(current_products)} productos.")
                
                all_products.extend(current_products)
                

                time.sleep(random.uniform(3, 6))

            except Exception as e:
                print(f"   -> Error en categoría {cat['name']}: {e}")


        output_file = 'asus_rog_laptops.json'
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