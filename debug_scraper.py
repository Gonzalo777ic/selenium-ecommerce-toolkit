import requests
import time
import os

# URL objetivo
TARGET_URL = "https://www.lenovo.com/pe/es/d/ofertas/intel/"

def download_html():
    print(f"[{time.strftime('%H:%M:%S')}] Descargando código fuente...")
    
    # Usamos headers para parecer un navegador real (Chrome en Windows)
    # A veces cambiar el User-Agent es suficiente para engañar al servidor
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "es-PE,es;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/"
    }

    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=20)
        
        # Guardamos el contenido en un archivo
        filename = "lenovo_dump.html"
        
        # Encoding utf-8 para que no fallen las tildes ni caracteres especiales
        with open(filename, "w", encoding="utf-8") as f:
            f.write(response.text)
            
        print(f"SUCCESS: HTML guardado en '{filename}'")
        print(f"Tamaño del archivo: {len(response.text)} caracteres")
        
        # ANÁLISIS RÁPIDO EN CONSOLA
        print("\n--- ANÁLISIS PRELIMINAR ---")
        if "Access Denied" in response.text or "Access to this page has been denied" in response.text:
            print("[ALERTA] Lenovo nos bloqueó (Error 403/Access Denied).")
        elif "dlp-product-card" in response.text:
            print("[BIEN] Se encontraron tarjetas de producto en el HTML.")
        elif "product_item" in response.text:
            print("[BIEN] Se encontraron items de producto en el HTML.")
        else:
            print("[INFO] No se encontraron productos. Probablemente usan JavaScript para cargar el contenido.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    download_html()