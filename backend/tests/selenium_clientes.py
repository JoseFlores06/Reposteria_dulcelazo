import os
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URL = "http://localhost:5173"
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@dulcelazo.pe")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin12345!")


def esperar(driver, by, selector):
    return WebDriverWait(driver, 10).until(EC.visibility_of_element_located((by, selector)))


def campo(driver, etiqueta):
    return esperar(driver, By.XPATH, f"//label[normalize-space()='{etiqueta}']/following-sibling::input")


def pausa(segundos=2):
    time.sleep(segundos)


def test_login_y_registrar_cliente():
    driver = webdriver.Edge()
    driver.maximize_window()
    try:
        #LOGIN
        driver.get(f"{URL}/login")
        pausa()
        esperar(driver, By.CSS_SELECTOR, 'input[type="email"]').send_keys(ADMIN_EMAIL)
        esperar(driver, By.CSS_SELECTOR, 'input[type="password"]').send_keys(ADMIN_PASSWORD)
        pausa()
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        WebDriverWait(driver, 10).until(EC.url_contains("/ventas"))
        pausa()

        #IR A CLIENTES Y ABRIR EL FORMULARIO
        driver.get(f"{URL}/clientes")
        pausa()
        esperar(driver, By.XPATH, "//button[contains(., 'Nuevo cliente')]").click()
        pausa()

        #LLENAR Y GUARDAR
        correo ="daniela.quispe@test.com"
        campo(driver, "Nombres *").send_keys("Daniela")
        pausa(1)
        campo(driver, "Apellidos *").send_keys("Quispe")
        pausa(1)
        campo(driver, "Correo").send_keys(correo)
        pausa(1)
        campo(driver, "Teléfono").send_keys("987654321")
        pausa(1)
        campo(driver, "WhatsApp").send_keys("987654321")
        pausa(1)
        campo(driver, "Edad aproximada").send_keys("30")
        pausa()
        driver.find_element(By.XPATH, "//button[@type='submit']").click()

        #VERIFICAR
        esperar(driver, By.XPATH, "//*[contains(., 'Cliente registrado')]")
        assert esperar(driver, By.XPATH, "//p[normalize-space()='Daniela Quispe']").is_displayed()
        pausa(3)
    finally:
        driver.quit()