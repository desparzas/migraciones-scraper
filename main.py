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
from flask import Flask, request, jsonify

app = Flask(__name__)

BASE_URL = "https://sel.migraciones.gob.pe/servmig-valreg/VerificarCE"
IMG_SAVE_PATH = './src/temp/screenshot.png'

@app.route('/api/get_carnet_extranjeria_data', methods=['POST'])
def get_carnet_extranjeria_data():
    data = request.get_json()
    numero_carnet = data['numero_carnet']
    dia = data['dia']
    mes = data['mes']
    anio = data['anio']
    res_scrap = scrape_data(numero_carnet, dia, mes, anio)
    return jsonify(res_scrap)

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

def invalid_form_response(driver):
    try:
        data_element = driver.find_element(By.ID, "ctl00_bodypage_pnlAlerta")

        texto_alerta = data_element.get_attribute('innerText')
        texto_alerta = texto_alerta.strip()
        if texto_alerta != "" and "El código de verificación no es correcto." not in texto_alerta:
            print("MENSAJE DE ALERTA: '", texto_alerta, "'")
            return True, texto_alerta
        return False, ""
    except Exception as e:
        print("NO SE MOSTRÓ PANEL DE ALERTA")
        return False, ""

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
    captcha_text = pytesseract.image_to_string(original, config='--psm 6')
    captcha_text = ''.join(e for e in captcha_text if e.isalnum())
    captcha_text = captcha_text.replace(" ", "")
    captcha_text = captcha_text.upper()
    return captcha_text

def get_data(driver):
    wait_elements = WebDriverWait(driver, 10)
    try:
        nombre_completo = wait_elements.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_lblnombre")))
        nacionalidad = wait_elements.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_lblnacionalidad")))
        fecha_nacimiento = wait_elements.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_lblfecnac")))
        calidad_migratoria = wait_elements.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_lblmensaje_CM")))
        vencimiento_residencia = wait_elements.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_lblfecha_residencia")))
        caducidad_carnet = wait_elements.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_lblmensaje_cad")))
        emision_carnet = wait_elements.until(EC.presence_of_element_located((By.ID, "ctl00_bodypage_lblmensaje_emi")))
        nombre_completo = nombre_completo.get_attribute('innerText')
        nacionalidad = nacionalidad.get_attribute('innerText')
        fecha_nacimiento = fecha_nacimiento.get_attribute('innerText')
        calidad_migratoria = calidad_migratoria.get_attribute('innerText')
        vencimiento_residencia = vencimiento_residencia.get_attribute('innerText')
        caducidad_carnet = caducidad_carnet.get_attribute('innerText')
        emision_carnet = emision_carnet.get_attribute('innerText')
#         {
# 	"caducidad_carnet": "21/02/2019",
# 	"calidad_migratoria": "TRABAJADOR",
# 	"emision_carnet": "21/02/2014",
# 	"fecha_nacimiento": "24-12-1977",
# 	"nacionalidad": "ESPAÑOLA",
# 	"nombre_completo": "MARTINEZ CAMPO, PLACIDO",
# 	"vencimiento_residencia": "18/02/2016"
# }
        # format the data
        # dates will use - not /
        caducidad_carnet = caducidad_carnet.replace("/", "-")
        emision_carnet = emision_carnet.replace("/", "-")
        fecha_nacimiento = fecha_nacimiento.replace("/", "-")
        vencimiento_residencia = vencimiento_residencia.replace("/", "-")
        nombre_completo = nombre_completo.replace(",", "")
        nombre_array = nombre_completo.split(" ")
        apellido1 = nombre_array[0]
        apellido2 = nombre_array[1]
        nombre1 = nombre_array[2]
        nombre2 = ""
        nombre3 = ""
        # si hay mas de 3 nombres
        if len(nombre_array) > 3:
            nombre2 = nombre_array[3]
        if len(nombre_array) > 4:
            nombre2 = nombre_array[3]
            nombre3 = nombre_array[4]
        data = {
                "nacionalidad": nacionalidad,
                "fecha_nacimiento": fecha_nacimiento,
                "calidad_migratoria": calidad_migratoria,
                "vencimiento_residencia": vencimiento_residencia,
                "caducidad_carnet": caducidad_carnet,
                "emision_carnet": emision_carnet,
                "apellido1": apellido1,
                "apellido2": apellido2,
                "nombre1": nombre1,
                "nombre2": nombre2,
                "nombre3": nombre3
        }
        print('-----------------------------------------')
        print("Data RESPONSE: ", data)
        print('-----------------------------------------')
        return data
    except NoSuchElementException:
        print("No se encontraron elementos en la página. Saliendo...")
    except TimeoutException:
        print("Tiempo de espera excedido. Saliendo...")
    except StaleElementReferenceException:
        print("Algunos elementos ya no están en el DOM. Saliendo...")

def validate_input(numero_carnet, dia, mes, anio):
    if numero_carnet == "" or dia == "" or mes == "" or anio == "":
        return False, "Los campos no deben estar vacíos"
    if len(numero_carnet) != 9:
        return False, "El número de carnet debe tener 9 dígitos"
    try:
        dia = int(dia)
        mes = int(mes)
        anio = int(anio)
        if dia < 1 or dia > 31:
            return False, "El día debe estar entre 1 y 31"
        if mes < 1 or mes > 12:
            return False, "El mes debe estar entre 1 y 12"
        if anio < 1900 or anio > 2024:
            return False, "El año debe estar entre 1900 y 2024"
    except ValueError:
        return False, "Los campos de fecha deben ser numéricos"
    try:
        int(numero_carnet)
    except ValueError:
        return False, "El número de carnet debe ser numérico"

    return True, ""

def scrape_data (numero_carnet, dia, mes, anio):

    valid_input, error_message = validate_input(numero_carnet, dia, mes, anio)

    if not valid_input:
        json_response = {
            "error": error_message
        }
        print('--------------------------------')
        print(json_response)
        print ('--------------------------------')
        return json_response

    data_res = {}

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
            if verificar_llenado(driver):
                print("Formulario llenado correctamente")
                send_form(driver)
                datos_enviados_invalidos, mensaje_alerta = invalid_form_response(driver)
                if (datos_enviados_invalidos):
                    print("Datos enviados inválidos")
                    break
                if (valid_form_response(driver)):
                    vfr = True
                    data_res = get_data(driver)
            else:
                print("Error al llenar el formulario")
            print('--------------------------------')
            print('--------------------------------')
        except Exception as e:
            print("Error al conectar a la página:", e)
            driver.quit()

    driver.quit()

    if datos_enviados_invalidos:
        # CREAR UN JSON
        json_response = {
            "error": mensaje_alerta
        }
        print('--------------------------------')
        print(json_response)
        print('--------------------------------')
        return json_response
    else:
        print('--------------------------------')
        print(data_res)
        print('--------------------------------')
        return data_res
        

def main():
    numero_carnet = "001043328"
    dia = "24"
    mes = "12"
    anio = "1977"
    scrape_data(numero_carnet, dia, mes, anio)

if __name__ == "__main__":
    app.run(debug=True)
    # main()