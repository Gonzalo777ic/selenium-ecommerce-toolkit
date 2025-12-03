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
        time.sleep(0.15) 
        

        if pos % 2000 == 0:
            last_height = driver.execute_script("return document.body.scrollHeight")


    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.5)
    driver.execute_script("window.scrollBy(0, -500);") 
    time.sleep(1)

def extract_page_data(html_content):
    """
    Extrae datos de Real Plaza (VTEX IO) usando selectores de clase específicos.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    page_products = []



    cards = soup.select('.vtex-product-summary-2-x-container')
    

    if not cards:
        cards = soup.select('.vtex-search-result-3-x-galleryItem')

    for card in cards:
        item = {}
        


        name_tag = card.select_one('.vtex-product-summary-2-x-productBrand')
        item['name'] = name_tag.get_text(strip=True) if name_tag else "Sin Nombre"
        


        price_text = "Agotado"
        

        oh_price = card.select_one('.realplaza-product-custom-0-x-productSummaryPrice__Option__ThirdPrice .realplaza-product-custom-0-x-productSummaryPrice__Option__Price span')
        

        online_price = card.select_one('.realplaza-product-custom-0-x-productSummaryPrice__Option__OfferPrice .realplaza-product-custom-0-x-productSummaryPrice__Option__Price span')
        

        regular_price = card.select_one('.realplaza-product-custom-0-x-productSummaryPrice__Option__RegularPrice .realplaza-product-custom-0-x-productSummaryPrice__Option__Price span')

        if oh_price:
            price_text = oh_price.get_text(strip=True) + " (Tarjeta Oh!)"
        elif online_price:
            price_text = online_price.get_text(strip=True)
        elif regular_price:
            price_text = regular_price.get_text(strip=True)
        else:

            generic_price = card.select_one('.vtex-product-summary-2-x-sellingPrice')
            if generic_price:
                price_text = generic_price.get_text(strip=True)

        item['price'] = price_text



        img_tag = card.select_one('img.vtex-product-summary-2-x-imageNormal')
        image_url = "No imagen"
        
        if img_tag:
            src = img_tag.get('src')
            if src:
                image_url = src
        
        item['image_url'] = image_url
        


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

            generic_link = card.find('a', href=True)
            if generic_link:
                href = generic_link['href']
                if href.startswith("http"):
                    product_url = href
                else:
                    product_url = "https://www.realplaza.com" + href
                    
        item['url'] = product_url
        

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
                

                try:
                    WebDriverWait(driver, 25).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "vtex-product-summary-2-x-container"))
                    )
                except TimeoutException:
                    print("   -> Alerta: Tiempo de espera agotado (posible página vacía).")
                

                scroll_realplaza(driver)
                

                current_products = extract_page_data(driver.page_source)
                count = len(current_products)
                print(f"   -> Encontrados: {count} productos.")
                
                all_products.extend(current_products)
                

                sleep_time = random.uniform(2, 4)
                time.sleep(sleep_time)

            except Exception as e:
                print(f"   -> Error en página {page}: {e}")


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