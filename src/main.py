from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import pytesseract
from PIL import Image
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
import json
import time
from selenium.common.exceptions import StaleElementReferenceException

BASE_URL = "https://sel.migraciones.gob.pe/servmig-valreg/VerificarCE"
IMG_SAVE_PATH = './src/temp/screenshot.png'

def conectar(driver, url):
    conectado = False 
    while not conectado:
        try:
            driver.get(url)
            print("Conectado a:", url)
            driver.implicitly_wait(10)
            driver.save_screenshot(IMG_SAVE_PATH)
            conectado = True
        except Exception as e:
            print("Error al conectar a la página:", e)
            time.sleep(5)
    return conectado

def save_captcha_image(driver):
    image_saved = False
    wait = WebDriverWait(driver, 10)
    print("Guardando imagen...")
    while not image_saved:
        img_element = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='capcha']//img")))
        img_element.screenshot(IMG_SAVE_PATH)
        image_saved = True
    print("Imagen guardada")

def scrape_data (numero_carnet, dia, mes, anio):
    valid_form_response = False

    # Configuración de Chrome
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()

    while not valid_form_response:
        conectar(driver, BASE_URL)
        save_captcha_image(driver)
        valid_form_response = True

def main():
    numero_carnet = "001043328"
    dia = "24"
    mes = "12"
    anio = "1977"
    scrape_data(numero_carnet, dia, mes, anio)

if __name__ == "__main__":
    main()
