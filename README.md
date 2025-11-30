🕷️ E-Commerce Scraper Suite (Perú & Global)

Este repositorio contiene una suite de web scrapers diseñados para extraer información de productos (laptops, hardware, tecnología) de los principales e-commerce de Perú y sitios globales.

El proyecto está optimizado para ejecutarse en entornos Cloud (GCP) y Docker, manejando desafíos modernos como Lazy Loading, renderizado dinámico (SPA/React), paginación por AJAX y evasión básica de anti-bots.

🚀 Tecnologías

Python 3.9+

Selenium WebDriver: Automatización de navegador y renderizado JS.

BeautifulSoup4: Parsing estático de HTML.

Docker: Contenerización para despliegue Serverless.

Google Cloud Platform (GCP): Compatible con Cloud Run/Functions.

🛒 Sitios Soportados

Sitio

Tecnología Detectada

Desafíos Superados

Amazon

Custom

Anti-bot severo, detección de CAPTCHA, selectores ofuscados.

Falabella

React / Next.js

SPA, carga diferida compleja, selectores dinámicos (testId).

Real Plaza

VTEX IO

Clases dinámicas, shadow DOM, scroll infinito.

Oechsle

VTEX Legacy

Multi-precios (Tarjeta Oh!), imágenes lazy.

Memory Kings

Custom / Legacy

Precios duales (Soles/Dólares), estructura de tablas antigua.

Magitech

Magento 1.x

Servidor lento, timeouts, precios ocultos por login/click.

Supertec

Custom

Paginación vía AJAX (sin cambio de URL), filtrado de basura en DOM.

Infotec

PrestaShop

Estructura semántica, lazy loading vía atributos data.

ASUS ROG

Custom / Vue

Clases CSS Modules (__1HpeZ), navegación por filtros.

⚙️ Instalación

Clonar el repositorio:

git clone [https://github.com/tu-usuario/ecommerce-scrapers.git](https://github.com/tu-usuario/ecommerce-scrapers.git)
cd ecommerce-scrapers


Crear entorno virtual:

python3 -m venv venv
source venv/bin/activate  


Instalar dependencias:

pip install -r requirements.txt


🏃‍♂️ Ejecución

Cada scraper funciona de manera independiente. Ejemplo para correr el de Amazon:

python3 amazon/amazon_scraper.py


El resultado se guardará como un archivo JSON en la raíz del proyecto (ej: amazon_laptops.json), el cual es ignorado por git para mantener limpio el repositorio.

🐳 Docker / Cloud

El proyecto incluye configuración para ejecutarse en contenedores sin interfaz gráfica (--headless=new).


docker build -t scraper-suite .


docker run -v $(pwd):/app/data scraper-suite python3 falabella/falabella.py


📝 Notas Técnicas

Evasión: Se utilizan técnicas para ocultar la huella de automatización de Selenium (navigator.webdriver).

Resiliencia: Los scripts incluyen lógica de reintentos (retries) y esperas explícitas (WebDriverWait) para manejar conexiones inestables.

Desarrollado con fines educativos y de análisis de datos.