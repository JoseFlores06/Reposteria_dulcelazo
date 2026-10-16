import os
import time

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

def test_login_y_registrar_usuario():
    driver = webdriver.Edge()
    driver.maximize_window()
    try:
        #LOGIN
        driver.get(f"{URL}/login")
        pausa()
        esperar(driver, By.CSS_SELECTOR, 'input[type="email"]').send_keys(ADMIN_EMAIL)
        pausa()
        esperar(driver, By.CSS_SELECTOR, 'input[type="password"]').send_keys(ADMIN_PASSWORD)
        pausa()
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        WebDriverWait(driver, 10).until(EC.url_contains("/ventas"))
        assert "/ventas" in driver.current_url
        pausa(3)

        #IR A USUARIOS Y ABRIR EL FORMULARIO
        driver.get(f"{URL}/usuarios")
        pausa()
        esperar(driver, By.XPATH, "//button[contains(., 'Nuevo usuario')]").click()
        pausa()

        #LLENAR Y GUARDAR
        correo ="rosa.paredes@test.com"
        campo(driver, "Nombres *").send_keys("Rosa")
        pausa()
        campo(driver, "Apellidos *").send_keys("Päredes")
        pausa()
        campo(driver, "Correo *").send_keys(correo)
        pausa()
        campo(driver, "Contraseña *").send_keys("Prueba12345")
        pausa()
        driver.find_element(By.XPATH, "//button[@type='submit']").click()

        #VERIFICAR
        esperar(driver, By.XPATH, "//*[contains(., 'Usuario creado')]")
        assert esperar(driver, By.XPATH, f"//p[normalize-space()='{correo}']").is_displayed()
        pausa(3)
    finally:
        driver.quit()