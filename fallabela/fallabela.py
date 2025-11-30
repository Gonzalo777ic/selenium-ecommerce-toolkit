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

def scroll_falabella(driver):
    """
    Scroll específico para Falabella.
    Baja poco a poco para asegurar que las imágenes 'lazy' se rendericen.
    """
    print("   -> Bajando para cargar imágenes...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    

    step = 400
    for pos in range(0, last_height, step):
        driver.execute_script(f"window.scrollTo(0, {pos});")

        time.sleep(0.15)
        

        if pos % 2000 == 0:
            last_height = driver.execute_script("return document.body.scrollHeight")
            

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.5)

def extract_page_data(html_content):
    """
    Extrae datos usando los selectores actualizados de Falabella (data-testid="ssr-pod").
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    page_products = []



    cards = soup.find_all('div', attrs={"data-testid": "ssr-pod"})

    if not cards:

        cards = soup.find_all('div', id=re.compile(r'^testId-pod-\d+'))

    for card in cards:
        item = {}
        



        name_tag = card.find('b', id=re.compile(r'^testId-pod-displaySubTitle'))
        if not name_tag:

            name_tag = card.find('b', class_=re.compile('pod-subTitle'))
            
        item['name'] = name_tag.get_text(strip=True) if name_tag else "Sin Nombre"
        


        price_section = card.find('div', id=re.compile(r'^testId-pod-prices'))
        item['price'] = "Agotado / No disponible"
        
        if price_section:


            li_cmr = price_section.find('li', attrs={"data-cmr-price": True})
            li_internet = price_section.find('li', attrs={"data-internet-price": True})
            li_normal = price_section.find('li', attrs={"data-normal-price": True})
            
            if li_cmr:
                item['price'] = "S/ " + li_cmr['data-cmr-price']
            elif li_internet:
                item['price'] = "S/ " + li_internet['data-internet-price']
            elif li_normal:
                item['price'] = "S/ " + li_normal['data-normal-price']
            else:

                prices = price_section.find_all('span')
                for p in prices:
                    txt = p.get_text(strip=True)
                    if "S/" in txt:
                        item['price'] = txt
                        break
        


        img_tag = card.find('img', id=re.compile(r'^testId-pod-image'))
        image_url = "No imagen"
        
        if img_tag:
            src = img_tag.get('src')
            if src:
                image_url = src

                if image_url.startswith("//"):
                    image_url = "https:" + image_url
            
        item['image_url'] = image_url
        


        link_tag = card.find('a', href=True)
        if link_tag:
            item['url'] = link_tag['href']
        elif card.name == 'a' and card.has_attr('href'):
            item['url'] = card['href']

        page_products.append(item)
        
    return page_products

def main():
    base_url = "https://www.falabella.com.pe/falabella-pe/category/cat40712/Laptops"
    total_pages = 10 
    
    all_products = []
    driver = None

    try:
        print("--- Iniciando Scraping Falabella (10 Páginas) ---")
        driver = setup_driver()

        for page in range(1, total_pages + 1):
            target_url = f"{base_url}?page={page}"
            print(f"\nProcesando Página {page}/{total_pages}: {target_url}")
            
            try:
                driver.get(target_url)
                

                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='ssr-pod']"))
                    )
                except TimeoutException:
                    print("   -> Alerta: Tiempo de espera agotado (posiblemente página vacía o bloqueo).")
                

                scroll_falabella(driver)
                

                current_products = extract_page_data(driver.page_source)
                print(f"   -> Encontrados: {len(current_products)} productos.")
                
                all_products.extend(current_products)
                

                sleep_time = random.uniform(2, 5)
                print(f"   -> Pausa de seguridad de {sleep_time:.2f}s...")
                time.sleep(sleep_time)

            except Exception as e:
                print(f"   -> Error en página {page}: {e}")


        output_file = 'falabella_laptops_10paginas.json'
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