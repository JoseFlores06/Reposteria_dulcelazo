import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

# Permite importar los módulos del backend (routes, auth, models) al correr pytest desde cualquier carpeta.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from auth import hashear_password, verificar_password
from models.usuario import RolUsuario
from routes.auth import UsuarioCreate


DATOS_VALIDOS = {
    "nombres": "Juan",
    "apellidos": "Pérez",
    "correo": "juan@dulcelazo.pe",
    "password": "Password123!",
}


def crear(**cambios):
    """Crea un UsuarioCreate con datos válidos, cambiando solo los campos indicados."""
    return UsuarioCreate(**{**DATOS_VALIDOS, **cambios})


# ------------------------------------------------------------------ caso feliz

def test_datos_validos_se_devuelven_limpios():
    usuario = crear(nombres="  Juan Carlos ", apellidos=" Pérez Gómez  ", correo="  juan.perez@dulcelazo.pe ")
    assert usuario.nombres == "Juan Carlos"
    assert usuario.apellidos == "Pérez Gómez"
    assert usuario.correo == "juan.perez@dulcelazo.pe"


def test_contrasena_se_guarda_hasheada_y_es_verificable():
    hash_guardado = hashear_password("Password123!")
    assert hash_guardado != "Password123!"
    assert verificar_password("Password123!", hash_guardado) is True


def test_contrasena_incorrecta_no_coincide_con_el_hash():
    hash_guardado = hashear_password("Password123!")
    assert verificar_password("OtraClave456", hash_guardado) is False


def test_misma_contrasena_genera_hashes_distintos():
    assert hashear_password("Password123!") != hashear_password("Password123!")


def test_rol_por_defecto_es_vendedor():
    assert crear().rol == RolUsuario.vendedor


def test_rol_inexistente_lanza_excepcion():
    with pytest.raises(ValidationError):
        crear(rol="superadmin")


# ------------------------------------------------------------ nombres/apellidos

def test_nombre_vacio_lanza_excepcion():
    with pytest.raises(ValidationError):
        crear(nombres="")


def test_nombre_solo_espacios_lanza_excepcion():
    with pytest.raises(ValidationError):
        crear(nombres="   ")


def test_apellido_vacio_lanza_excepcion():
    with pytest.raises(ValidationError):
        crear(apellidos="")


def test_apellido_solo_espacios_lanza_excepcion():
    with pytest.raises(ValidationError):
        crear(apellidos="   ")


@pytest.mark.parametrize("longitud, es_valida", [
    pytest.param(1, False, id="1-caracter-invalido"),      # justo por debajo del minimo
    pytest.param(2, True, id="2-caracteres-valido"),       # minimo valido (limite incluido)
    pytest.param(100, True, id="100-caracteres-valido"),   # maximo valido (limite incluido)
    pytest.param(101, False, id="101-caracteres-invalido"),  # justo por encima del maximo
])
def test_longitud_del_nombre_en_sus_valores_limite(longitud, es_valida):
    if es_valida:
        crear(nombres="A" * longitud)
    else:
        with pytest.raises(ValidationError):
            crear(nombres="A" * longitud)


@pytest.mark.parametrize("longitud, es_valida", [
    pytest.param(1, False, id="1-caracter-invalido"),
    pytest.param(2, True, id="2-caracteres-valido"),
    pytest.param(100, True, id="100-caracteres-valido"),
    pytest.param(101, False, id="101-caracteres-invalido"),
])
def test_longitud_del_apellido_en_sus_valores_limite(longitud, es_valida):
    if es_valida:
        crear(apellidos="A" * longitud)
    else:
        with pytest.raises(ValidationError):
            crear(apellidos="A" * longitud)


@pytest.mark.parametrize("valor_invalido", [
    pytest.param("Juan3", id="con-numero"),
    pytest.param("Juan.123", id="punto-y-numeros"),
    pytest.param("Juan_Perez", id="guion-bajo"),
    pytest.param("'; DROP TABLE users;--", id="inyeccion-sql"),
    pytest.param("<script>alert(1)</script>", id="inyeccion-script"),
])
def test_nombre_con_caracteres_no_permitidos_lanza_excepcion(valor_invalido):
    with pytest.raises(ValidationError):
        crear(nombres=valor_invalido)


@pytest.mark.parametrize("valor_invalido", [
    pytest.param("Pérez99", id="con-numeros"),
    pytest.param("Pérez-", id="con-guion"),
    pytest.param("Pérez@", id="con-arroba"),
])
def test_apellido_con_caracteres_no_permitidos_lanza_excepcion(valor_invalido):
    with pytest.raises(ValidationError):
        crear(apellidos=valor_invalido)


def test_nombre_y_apellido_con_tildes_y_enie_son_validos():
    usuario = crear(nombres="Ñandú", apellidos="Peña Muñoz", correo="nandu@dulcelazo.pe")
    assert usuario.nombres == "Ñandú"
    assert usuario.apellidos == "Peña Muñoz"


# ----------------------------------------------------------------------- correo

@pytest.mark.parametrize("correo_invalido", [
    pytest.param("", id="vacio"),
    pytest.param("   ", id="solo-espacios"),
    pytest.param("juan.perez.dulcelazo.pe", id="sin-arroba"),
    pytest.param("juan@dulcelazo", id="dominio-sin-punto"),
    pytest.param("@dulcelazo.pe", id="sin-parte-local"),
    pytest.param("juan@@dulcelazo.pe", id="doble-arroba"),
    pytest.param("juan@dulcelazo.", id="termina-en-punto"),
    pytest.param("juan perez@dulcelazo.pe", id="espacio-interno"),
])
def test_correo_con_formato_invalido_lanza_excepcion(correo_invalido):
    with pytest.raises(ValidationError):
        crear(correo=correo_invalido)


# ------------------------------------------------------------------- contraseña

@pytest.mark.parametrize("password, es_valida", [
    pytest.param("abcdef1", False, id="7-caracteres-invalida"),         # justo por debajo del minimo
    pytest.param("abcdefg1", True, id="8-caracteres-valida"),           # minimo valido
    pytest.param("a1" * 32, True, id="64-caracteres-valida"),           # maximo valido
    pytest.param("a1" * 32 + "x", False, id="65-caracteres-invalida"),  # justo por encima del maximo
])
def test_longitud_de_la_contrasena_en_sus_valores_limite(password, es_valida):
    if es_valida:
        crear(password=password)
    else:
        with pytest.raises(ValidationError):
            crear(password=password)


@pytest.mark.parametrize("password_debil", [
    pytest.param("", id="vacia"),
    pytest.param("12345678", id="solo-numeros"),
    pytest.param("sololetras", id="solo-letras"),
])
def test_contrasena_sin_letras_y_numeros_lanza_excepcion(password_debil):
    with pytest.raises(ValidationError):
        crear(password=password_debil)