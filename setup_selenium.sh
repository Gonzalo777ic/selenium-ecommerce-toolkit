#!/bin/bash

echo "=== Instalando Dependencias para Selenium en Linux ==="

# 1. Actualizar repositorios
sudo apt-get update

# 2. Instalar Chromium (versión open source de Chrome) y su driver
# Esto es necesario porque Selenium necesita controlar un navegador real
echo "Instalando Chromium y Chromedriver..."
sudo apt-get install -y chromium-browser chromium-chromedriver

# 3. Instalar librerías de Python
echo "Instalando librerías Python..."
source venv/bin/activate
pip install selenium webdriver-manager beautifulsoup4

echo "=== Instalación Completa ==="
echo "Ahora puedes ejecutar: python3 scraper_dynamic.py"