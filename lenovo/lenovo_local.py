import time
import json
import re
import os
import shutil
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from bs4 import BeautifulSoup

def setup_driver():
    
    chrome_options = Options()

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    service = Service(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scroll_inteligente(driver):
    """
    Baja buscando activamente el botón 'Ver más'.
    Si lo encuentra, hace scroll hasta ponerlo en el CENTRO de la pantalla y lo presiona.
    """
    print("Iniciando scroll inteligente...")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    consecutive_scrolls_without_button = 0

    while True:
        try:
            products_count = len(driver.find_elements(By.CSS_SELECTOR, "li.product_item"))
            print(f"--> Productos visibles actualmente: {products_count}")
        except:
            pass

        boton_encontrado = False
        try:

            btn = driver.find_element(By.XPATH, "//button[contains(@class, 'pc_more') or contains(., 'Ver más')]")
            
            if btn.is_displayed():
                print("Botón 'Ver más' DETECTADO.")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(1) 
                driver.execute_script("arguments[0].click();", btn)
                print("Click realizado. Esperando carga...")
                time.sleep(5) 
                consecutive_scrolls_without_button = 0 
                boton_encontrado = True
            
        except NoSuchElementException:
            pass
        except Exception as e:
            print(f"Error intentando clickear botón: {e}")

        if not boton_encontrado:
            driver.execute_script("window.scrollBy(0, 600);")
            time.sleep(1) 
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            current_pos = driver.execute_script("return window.pageYOffset + window.innerHeight")
            
            if current_pos >= new_height - 200:
                consecutive_scrolls_without_button += 1
                print(f"Llegando al footer... intento {consecutive_scrolls_without_button}/3 sin ver botón.")
                
                if consecutive_scrolls_without_button >= 3:
                    print("Parece que no hay más botones ni productos. Fin del scroll.")
                    break
                
                driver.execute_script("window.scrollBy(0, -300);")
                time.sleep(2)
            else:
                consecutive_scrolls_without_button = 0

def extract_data(html_content):
    
    soup = BeautifulSoup(html_content, 'html.parser')
    products_data = []

    product_cards = soup.select('li.product_item')
    print(f"Análisis final: Se encontraron {len(product_cards)} tarjetas de producto.")

    for card in product_cards:
        item = {}
        

        title_tag = card.select_one('.product_title a')
        item['name'] = title_tag.get_text(strip=True) if title_tag else "Sin Nombre"
        

        price_tag = card.select_one('.price-summary-info .price-title')
        item['price'] = price_tag.get_text(strip=True) if price_tag else "Agotado / No disponible"



        img_tag = card.select_one('.product_img img') or card.select_one('img')
        
        image_url = "No imagen"
        if img_tag:

            src = img_tag.get('src')

            data_src = img_tag.get('data-src') or img_tag.get('data-lazy')
            

            if src and "data:image" not in src and "base64" not in src:
                image_url = src
            elif data_src:
                image_url = data_src
            

            if image_url and image_url.startswith("//"):
                image_url = "https:" + image_url
                
        item['image_url'] = image_url

        products_data.append(item)

    return products_data

def main():
    url = "https://www.lenovo.com/pe/es/d/ofertas/intel/"
    
    driver = None
    try:
        print("Iniciando navegador...")
        driver = setup_driver()
        
        print(f"Navegando a: {url}")
        driver.get(url)
        
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "product_list"))
            )
        except TimeoutException:
            print("Alerta: No se detectó la lista inicial de productos.")

        scroll_inteligente(driver)
        
        print("Obteniendo código fuente final...")
        page_source = driver.page_source
        
        print("Procesando datos...")
        data = extract_data(page_source)
        
        output_file = 'lenovo_completo.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"GUARDADO: {len(data)} productos en {output_file}")
        
        if len(data) > 0:
            print("\nMuestra del último producto:")
            print(f"Nombre: {data[-1]['name']}")
            print(f"Imagen: {data[-1]['image_url']}")

    except Exception as e:
        print(f"Error fatal: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()