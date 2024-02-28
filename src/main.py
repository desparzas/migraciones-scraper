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
from selenium.common.exceptions import StaleElementReferenceException

BASE_URL = "https://sel.migraciones.gob.pe/servmig-valreg/VerificarCE"
IMG_SAVE_PATH = './src/temp/screenshot.png'

def conectar(driver):
    wait_page = WebDriverWait(driver, 10)
    conectado = False
    while not conectado:
        try:
            driver.get(BASE_URL)
            print("Conectado a la página")
            print("Cargando Elementos")
            wait_page.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_txtnumerodoc")))
            print("NUMERO DOC ENCONTRADO")
            wait_page.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_cbodia")))
            print('CBODIA')
            wait_page.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_cbomes")))
            print('CBOMES')
            wait_page.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_cboanio")))
            print('CBOAÑO')
            wait_page.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_txtvalidator")))
            print('TEXTO CAPTCHA')
            print("Elementos Cargados")
            print("Cargando Botones")
            wait_page.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_btnverificar")))
            wait_page.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_btnlimpiar")))
            print("Botones cargados")     
            wait_page.until(EC.presence_of_element_located((By.XPATH, "//div[@class='capcha']//img")))   
            print("CAPTCHA CARGADO")
            conectado = True
        except TimeoutException:
            print("No se pudo conectar a la página... Reintando")
            conectado = False
    return conectado

def send_form(driver):
    wait_page = WebDriverWait(driver, 10)
    try:
        btn_verificar = driver.find_element(By.ID, "ctl00_bodypage_btnverificar")
        btn_verificar.click()
        print("Formulario enviado")
        # esperar a que cargue la página
        wait_page.until(EC.staleness_of(btn_verificar))
    except Exception as e:
        print("Error al enviar el formulario:", e)

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
    print("Formulario llenado")

def verificar_llenado(driver):
    try:
        input_numero_carnet = driver.find_element(By.ID, "ctl00_bodypage_txtnumerodoc")
        select_dia = Select(driver.find_element(By.ID, "ctl00_bodypage_cbodia"))
        select_mes = Select(driver.find_element(By.ID, "ctl00_bodypage_cbomes"))
        select_anio = Select(driver.find_element(By.ID, "ctl00_bodypage_cboanio"))
        input_captcha = driver.find_element(By.ID, "ctl00_bodypage_txtvalidator")

        form_data = {
            "numero_carnet": input_numero_carnet.get_attribute("value"),
            "dia": select_dia.first_selected_option.text,
            "mes": select_mes.first_selected_option.text,
            "anio": select_anio.first_selected_option.text,
            "captcha": input_captcha.get_attribute("value")
        }
        # Imprimiendo valores
        print('--------------------------------')
        print('VALORES DEL FORMULARIO')
        print('--------------------------------')
        print("Número de carnet:", input_numero_carnet.get_attribute("value"))
        print("Fecha de nacimiento:", select_dia.first_selected_option.text, select_mes.first_selected_option.text, select_anio.first_selected_option.text)
        print("Captcha:", input_captcha.get_attribute("value"))
        print('--------------------------------')
        print('FORM DATA:', form_data)
        print('--------------------------------')

        if input_numero_carnet.get_attribute("value") != "" and select_dia.first_selected_option.text != "Día" and select_mes.first_selected_option.text != "Mes" and select_anio.first_selected_option.text != "Año" and input_captcha.get_attribute("value") != "":
            return True
        else:
            return False
    except StaleElementReferenceException:
        print("Referencia de elemento caducada")
        return False
    except TimeoutException:
        print("Tiempo de espera excedido")
        return False
    except NoSuchElementException:
        print("Elemento no encontrado")
        return False

def valid_form_response(driver):
    try:
        data_element = driver.find_element(By.ID, "ctl00_bodypage_pnlData")
        print("Formulario válido")
        return True
    except Exception as e:
        print("Datos enviados inválidos")
        return False
    
def get_captcha_text(img_filepath):
    original = Image.open(img_filepath)
    captcha_text = pytesseract.image_to_string(original, config='--psm 7')
    captcha_text = ''.join(e for e in captcha_text if e.isalnum())
    captcha_text = captcha_text.replace(" ", "")
    captcha_text = captcha_text.upper()
    return captcha_text

def save_data(driver):
    wait_elements = WebDriverWait(driver, 10)
    try:
        nombre_completo = wait_elements.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_lblnombre")))
        nacionalidad = wait_elements.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_lblnacionalidad")))
        fecha_nacimiento = wait_elements.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_lblfecnac")))
        calidad_migratoria = wait_elements.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_lblmensaje_CM")))
        vencimiento_residencia = wait_elements.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_lblfecha_residencia")))
        caducidad_carnet = wait_elements.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_lblmensaje_cad")))
        emision_carnet = wait_elements.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_lblmensaje_emi")))
        data = {
                "nombre_completo": nombre_completo.get_attribute('innerHTML'),
                "nacionalidad": nacionalidad.get_attribute('innerHTML'),
                "fecha_nacimiento": fecha_nacimiento.get_attribute('innerHTML'),
                "calidad_migratoria": calidad_migratoria.get_attribute('innerHTML'),
                "vencimiento_residencia": vencimiento_residencia.get_attribute('innerHTML'),
                "caducidad_carnet": caducidad_carnet.get_attribute('innerHTML'),
                "emision_carnet": emision_carnet.get_attribute('innerHTML')
        }
        print('-----------------------------------------')
        print("Data RESPONSE: ", data)
        print('-----------------------------------------')


        with open('./src/data/data.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except NoSuchElementException:
        print("No se encontraron elementos en la página. Saliendo...")
    except TimeoutException:
        print("Tiempo de espera excedido. Saliendo...")
    except StaleElementReferenceException:
        print("Algunos elementos ya no están en el DOM. Saliendo...")
    return True

def scrape_data (numero_carnet, dia, mes, anio):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    # chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--disable-site-isolation-trials')
    chrome_options.add_argument('--disable-default-apps')
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--disable-translate')
    chrome_options.add_argument('--ignore-certificate-errors')
    # options.add_argument('--headless')
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    driver.maximize_window()
    wait_page = WebDriverWait(driver, 10)
    vfr = False
    while not vfr:
        try:
            print('--------------------------------')
            print('--------------------------------')
            conectar(driver)
            img_element = wait_page.until(EC.presence_of_element_located((By.XPATH, "//div[@class='capcha']//img")))
            img_element.screenshot(IMG_SAVE_PATH)
            print("Imagen guardada")
            captcha_text = get_captcha_text(IMG_SAVE_PATH)
            print("Texto del captcha de la imagen:", captcha_text)
            fill_form(driver, numero_carnet, dia, mes, anio, captcha_text)
            print("Formulario llenado")
            if verificar_llenado(driver):
                print("Formulario llenado correctamente")
                send_form(driver)
                if (valid_form_response(driver)):
                    vfr = True
                    save_data(driver)
            else:
                print("Error al llenar el formulario")
            print('--------------------------------')
            print('--------------------------------')
        except Exception as e:
            print("Error al conectar a la página:", e)

def main():
    numero_carnet = "001043328"
    dia = "24"
    mes = "12"
    anio = "1977"
    scrape_data(numero_carnet, dia, mes, anio)

if __name__ == "__main__":
    main()