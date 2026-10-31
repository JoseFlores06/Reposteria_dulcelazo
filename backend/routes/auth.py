from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import re
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import timedelta

from database import get_db
from models.usuario import Usuario, RolUsuario
from auth import (
    verificar_password, hashear_password, crear_access_token,
    obtener_usuario_actual, requerir_admin,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    usuario: dict


# ---------------------------------------------------------------------------
# DEF-DL-008: reglas de validación del registro de usuario. Antes UsuarioCreate
# aceptaba cualquier texto (30 de las 42 pruebas unitarias del TC7 fallaban).
#   · nombres / apellidos: 2 a 100 letras (se permiten tildes, ñ y espacios
#     entre palabras); sin números ni símbolos; se quitan espacios extremos.
#   · correo: formato usuario@dominio.ext, sin espacios; se guarda en minúsculas.
#   · contraseña: 8 a 64 caracteres, con al menos una letra y un número.
# ---------------------------------------------------------------------------
_PATRON_NOMBRE = re.compile(r"^[^\W\d_]+(?: [^\W\d_]+)*$")
_PATRON_CORREO = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")


def _validar_nombre(valor: str, campo: str) -> str:
    valor = " ".join((valor or "").split())
    if not valor:
        raise ValueError(f"{campo} es obligatorio")
    if not 2 <= len(valor) <= 100:
        raise ValueError(f"{campo} debe tener entre 2 y 100 caracteres")
    if not _PATRON_NOMBRE.match(valor):
        raise ValueError(f"{campo} solo puede contener letras y espacios")
    return valor


def _validar_correo(valor: str) -> str:
    valor = (valor or "").strip().lower()
    if not _PATRON_CORREO.match(valor):
        raise ValueError("Ingrese un correo válido (ejemplo: nombre@dulcelazo.pe)")
    return valor


def _validar_password(valor: str) -> str:
    if not 8 <= len(valor or "") <= 64:
        raise ValueError("La contraseña debe tener entre 8 y 64 caracteres")
    if not (re.search(r"[A-Za-z]", valor) and re.search(r"\d", valor)):
        raise ValueError("La contraseña debe combinar letras y números")
    return valor


class UsuarioCreate(BaseModel):
    nombres: str
    apellidos: str
    correo: str
    password: str
    rol: RolUsuario = RolUsuario.vendedor

    @field_validator("nombres")
    @classmethod
    def _nombres(cls, v):
        return _validar_nombre(v, "El nombre")

    @field_validator("apellidos")
    @classmethod
    def _apellidos(cls, v):
        return _validar_nombre(v, "El apellido")

    @field_validator("correo")
    @classmethod
    def _correo(cls, v):
        return _validar_correo(v)

    @field_validator("password")
    @classmethod
    def _password(cls, v):
        return _validar_password(v)


class UsuarioUpdate(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    correo: Optional[str] = None
    password: Optional[str] = None
    rol: Optional[RolUsuario] = None
    activo: Optional[bool] = None

    # Mismas reglas que el alta, solo para los campos que se envían
    @field_validator("nombres")
    @classmethod
    def _nombres(cls, v):
        return None if v is None else _validar_nombre(v, "El nombre")

    @field_validator("apellidos")
    @classmethod
    def _apellidos(cls, v):
        return None if v is None else _validar_nombre(v, "El apellido")

    @field_validator("correo")
    @classmethod
    def _correo(cls, v):
        return None if v is None else _validar_correo(v)

    @field_validator("password")
    @classmethod
    def _password(cls, v):
        return None if v in (None, "") else _validar_password(v)


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(
        Usuario.correo == form_data.username,
        Usuario.activo == True
    ).first()

    if not usuario or not verificar_password(form_data.password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = crear_access_token(
        data={"sub": usuario.correo},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": {
            "id": usuario.id,
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "correo": usuario.correo,
            "rol": usuario.rol,
        }
    }


@router.get("/me")
def obtener_perfil(usuario: Usuario = Depends(obtener_usuario_actual)):
    return {
        "id": usuario.id,
        "nombres": usuario.nombres,
        "apellidos": usuario.apellidos,
        "correo": usuario.correo,
        "rol": usuario.rol,
    }


@router.get("/usuarios")
def listar_usuarios(db: Session = Depends(get_db), _: Usuario = Depends(requerir_admin)):
    usuarios = db.query(Usuario).all()
    return [
        {
            "id": u.id,
            "nombres": u.nombres,
            "apellidos": u.apellidos,
            "correo": u.correo,
            "rol": u.rol,
            "activo": u.activo,
        }
        for u in usuarios
    ]


@router.post("/usuarios")
def crear_usuario(data: UsuarioCreate, db: Session = Depends(get_db), _: Usuario = Depends(requerir_admin)):
    existente = db.query(Usuario).filter(Usuario.correo == data.correo).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese correo")

    usuario = Usuario(
        nombres=data.nombres,
        apellidos=data.apellidos,
        correo=data.correo,
        hashed_password=hashear_password(data.password),
        rol=data.rol,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return {"mensaje": "Usuario creado correctamente", "id": usuario.id}


@router.put("/usuarios/{usuario_id}")
def actualizar_usuario(
    usuario_id: int,
    data: UsuarioUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin)
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if data.nombres is not None:
        usuario.nombres = data.nombres
    if data.apellidos is not None:
        usuario.apellidos = data.apellidos
    if data.correo is not None:
        usuario.correo = data.correo
    if data.password is not None:
        usuario.hashed_password = hashear_password(data.password)
    if data.rol is not None:
        usuario.rol = data.rol
    if data.activo is not None:
        usuario.activo = data.activo

    db.commit()
    return {"mensaje": "Usuario actualizado correctamente"}
