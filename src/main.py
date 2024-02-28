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
    wait_page = WebDriverWait(driver, 10)
    while not conectado:
        try:
            driver.get(url)
            wait_page.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_btnverificar")))
            print("Página cargada")
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

def get_captcha_text():
    original = Image.open(IMG_SAVE_PATH)
    captcha_text = pytesseract.image_to_string(original, config='--psm 6')
    captcha_text = ''.join(e for e in captcha_text if e.isalnum())
    captcha_text = captcha_text.replace(" ", "")
    captcha_text = captcha_text.upper()
    return captcha_text

def fill_form(driver, numero_carnet, dia, mes, anio, captcha_text):

    try:
        input_numero_carnet = driver.find_element(By.ID, "ctl00_bodypage_txtnumerodoc")
        select_dia = Select(driver.find_element(By.ID, "ctl00_bodypage_cbodia"))
        select_mes = Select(driver.find_element(By.ID, "ctl00_bodypage_cbomes"))
        select_anio = Select(driver.find_element(By.ID, "ctl00_bodypage_cboanio"))
        input_captcha = driver.find_element(By.ID, "ctl00_bodypage_txtvalidator")
        input_numero_carnet.send_keys(numero_carnet)
        select_dia.select_by_value(dia)
        select_mes.select_by_value(mes)
        select_anio.select_by_value(anio)
        input_captcha.send_keys(captcha_text)
    except Exception as e:
        print("Error al llenar el formulario:", e)
        time.sleep(5)

    print("Formulario llenado")
def scrape_data (numero_carnet, dia, mes, anio):
    valid_form_response = False
    # Configuración de Chrome
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    # options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    driver.maximize_window()

    while not valid_form_response:
        conectar(driver, BASE_URL)
        save_captcha_image(driver)
        captcha_text = get_captcha_text()
        print("'", captcha_text, "'", sep='')
        fill_form(driver, numero_carnet, dia, mes, anio, captcha_text)
        valid_form_response = True
        time.sleep(5)
    
    # Cerro la ventana
    driver.quit()

def main():
    numero_carnet = "001043328"
    dia = "24"
    mes = "12"
    anio = "1977"
    scrape_data(numero_carnet, dia, mes, anio)

if __name__ == "__main__":
    main()
