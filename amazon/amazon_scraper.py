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
    

    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    chrome_options.add_argument("--log-level=3")
    
    service = Service(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def scroll_amazon(driver):
    """
    Scroll aleatorio y humano para Amazon.
    """
    print("   -> Comportamiento humano: Bajando para ver productos...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    

    current_pos = 0
    while current_pos < last_height:
        step = random.randint(400, 800)
        current_pos += step
        driver.execute_script(f"window.scrollTo(0, {current_pos});")
        time.sleep(random.uniform(0.1, 0.4))
        

        if current_pos > last_height * 0.8:
            last_height = driver.execute_script("return document.body.scrollHeight")
            
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.5)

def extract_page_data(html_content):
    """
    Extrae datos de Amazon manejando su estructura de rejilla (Grid).
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    page_products = []


    if "Enter the characters you see below" in soup.get_text() or "Robot Check" in soup.title.string:
        print("   !!! ALERTA: Amazon detectó tráfico inusual (CAPTCHA). !!!")
        return []



    cards = soup.select('div[data-component-type="s-search-result"]')

    if not cards:

        cards = soup.select('.s-result-item')

    for card in cards:
        item = {}
        


        title_tag = card.select_one('h2 span')
        if not title_tag:
            continue 
            
        item['name'] = title_tag.get_text(strip=True)
        

        price_text = "Agotado / No disponible"

        price_tag = card.select_one('.a-price .a-offscreen')
        
        if price_tag:
            price_text = price_tag.get_text(strip=True)
        else:

            alt_price = card.select_one('.a-color-price')
            if alt_price:
                price_text = alt_price.get_text(strip=True)
                
        item['price'] = price_text



        img_tag = card.select_one('img.s-image')
        item['image_url'] = img_tag.get('src') if img_tag else "No imagen"
        


        link_tag = card.select_one('h2 a')
        product_url = ""
        if link_tag:
            href = link_tag.get('href')
            if href:
                if href.startswith("http"):
                    product_url = href
                else:
                    product_url = "https://www.amazon.com" + href
        item['url'] = product_url
        

        rating_tag = card.select_one('span[aria-label*="stars"]') or card.select_one('i[class*="a-star-small"]')
        item['rating'] = rating_tag.get_text(strip=True) if rating_tag else "Sin calificación"

        page_products.append(item)
        
    return page_products

def main():

    urls = [
        "https://www.amazon.com/s?i=computers&rh=n%3A565108&s=popularity-rank&fs=true&language=es&ref=lp_565108_sar",
        "https://www.amazon.com/s?i=computers&rh=n%3A565108&s=popularity-rank&fs=true&page=2&language=es&qid=1764484056&xpid=KnbWhSpQY3doM&ref=sr_pg_2",
        "https://www.amazon.com/-/es/s?i=computers&rh=n%3A565108&s=popularity-rank&fs=true&page=3&language=es&qid=1764484803&xpid=KnbWhSpQY3doM&ref=sr_pg_3",
        "https://www.amazon.com/-/es/s?i=computers&rh=n%3A565108&s=popularity-rank&fs=true&page=4&language=es&qid=1764485164&xpid=YFF_xqLNeb_f6&ref=sr_pg_4",
        "https://www.amazon.com/-/es/s?i=computers&rh=n%3A565108&s=popularity-rank&fs=true&page=5&language=es&qid=1764485172&xpid=YFF_xqLNeb_f6&ref=sr_pg_5",
        "https://www.amazon.com/-/es/s?i=computers&rh=n%3A565108&s=popularity-rank&fs=true&page=6&language=es&qid=1764485180&xpid=YFF_xqLNeb_f6&ref=sr_pg_6",
        "https://www.amazon.com/-/es/s?i=computers&rh=n%3A565108&s=popularity-rank&fs=true&page=7&language=es&qid=1764485224&xpid=YFF_xqLNeb_f6&ref=sr_pg_7",
        "https://www.amazon.com/-/es/s?i=computers&rh=n%3A565108&s=popularity-rank&fs=true&page=8&language=es&qid=1764485233&xpid=YFF_xqLNeb_f6&ref=sr_pg_8",
        "https://www.amazon.com/-/es/s?i=computers&rh=n%3A565108&s=popularity-rank&fs=true&page=9&language=es&qid=1764485240&xpid=YFF_xqLNeb_f6&ref=sr_pg_9",
        "https://www.amazon.com/-/es/s?i=computers&rh=n%3A565108&s=popularity-rank&fs=true&page=10&language=es&qid=1764485248&xpid=YFF_xqLNeb_f6&ref=sr_pg_10"
    ]
    
    all_products = []
    driver = None

    try:
        print("--- Iniciando Scraping Amazon (Modo Ninja) ---")
        driver = setup_driver()

        for i, url in enumerate(urls):
            print(f"\nProcesando Página {i+1}/10: {url}")
            
            try:
                driver.get(url)
                

                time.sleep(random.uniform(2, 4))
                

                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-component-type='s-search-result']"))
                    )
                except TimeoutException:
                    print("   -> Alerta: No se detectaron productos. Verificando posible CAPTCHA...")
                

                scroll_amazon(driver)
                

                current_products = extract_page_data(driver.page_source)
                print(f"   -> Encontrados: {len(current_products)} productos.")
                
                if len(current_products) == 0:


                    print("   -> Fallo en extracción. Posible bloqueo.")
                else:
                    all_products.extend(current_products)
                

                wait_time = random.uniform(5, 8)
                print(f"   -> Esperando {wait_time:.1f}s antes de la siguiente página...")
                time.sleep(wait_time)

            except Exception as e:
                print(f"   -> Error en página {i+1}: {e}")


        output_file = 'amazon_laptops.json'
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