
import time
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://www.lenovo.com/pe/es/d/ofertas/intel/"

def scroll_inteligente(driver):
    """ lógica de scroll probada localmente."""
    print("   [Lenovo] Iniciando scroll inteligente...")
    consecutive_scrolls_without_button = 0

    while True:
        try:



            pass
        except: pass

        boton_encontrado = False
        try:
            btn = driver.find_element(By.XPATH, "//button[contains(@class, 'pc_more') or contains(., 'Ver más')]")
            if btn.is_displayed():
                print("   [JS] Botón 'Ver más' DETECTADO.")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", btn)
                print("   [JS] Click realizado. Esperando carga...")
                time.sleep(5)
                consecutive_scrolls_without_button = 0
                boton_encontrado = True
        except (NoSuchElementException, Exception):
            pass

        if not boton_encontrado:
            driver.execute_script("window.scrollBy(0, 600);")
            time.sleep(1)
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            current_pos = driver.execute_script("return window.pageYOffset + window.innerHeight")
            
            if current_pos >= new_height - 200:
                consecutive_scrolls_without_button += 1
                print(f"   [JS] Footer alcanzado ({consecutive_scrolls_without_button}/3).")
                if consecutive_scrolls_without_button >= 3:
                    print("   [JS] Fin del scroll.")
                    break
                driver.execute_script("window.scrollBy(0, -300);")
                time.sleep(2)
            else:
                consecutive_scrolls_without_button = 0

def scrape(driver):
    """Función principal llamada por el orquestador."""
    print(f"--- Scrapeando LENOVO ({URL}) ---")
    driver.get(URL)
    

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product_list"))
        )
    except TimeoutException:
        print("   [Alerta] No se detectó la lista inicial (Timeout). Continuando...")


    scroll_inteligente(driver)

    print("   [Lenovo] Procesando HTML final...")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    products = []
    

    items = soup.select('li.product_item')
    if not items: items = soup.find_all("div", class_="dlp-product-card") 

    print(f"   [Lenovo] Se encontraron {len(items)} tarjetas.")

    for item in items:
        try:

            title_tag = item.select_one(".product_title a") or item.select_one("a.lazy_href")
            if not title_tag: continue
            name = title_tag.get_text(strip=True)


            price_tag = item.select_one(".price-summary-info .price-title") or item.select_one(".price-title")
            price = 0.0
            if price_tag:
                raw_text = price_tag.get_text(strip=True)

                clean_text = re.sub(r'[^\d,]', '', raw_text).replace(",", "")
                try: price = float(clean_text)
                except: price = 0.0


            img_tag = item.select_one('.product_img img') or item.select_one('img')
            image_url = None
            
            if img_tag:
                src = img_tag.get('src')
                data_src = img_tag.get('data-src') or img_tag.get('data-lazy')
                
                if src and "data:image" not in src and "base64" not in src:
                    image_url = src
                elif data_src:
                    image_url = data_src
                
                if image_url and image_url.startswith("//"):
                    image_url = "https:" + image_url


            pid = item.get("data-product-code") or re.sub(r'\W+', '', name)[:20].upper()

            if price > 0:
                products.append({
                    "product_id": pid,
                    "name": name,
                    "price": price,
                    "image_url": image_url,
                    "currency": "PEN",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "store": "Lenovo"
                })
        except: continue
            
    return products