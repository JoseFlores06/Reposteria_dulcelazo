from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
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


class UsuarioCreate(BaseModel):
    nombres: str
    apellidos: str
    correo: str
    password: str
    rol: RolUsuario = RolUsuario.vendedor


class UsuarioUpdate(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    correo: Optional[str] = None
    password: Optional[str] = None
    rol: Optional[RolUsuario] = None
    activo: Optional[bool] = None


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
