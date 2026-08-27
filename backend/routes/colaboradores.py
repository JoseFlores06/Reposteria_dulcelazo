from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models.colaborador import Colaborador
from models.usuario import Usuario
from auth import requerir_autenticado, requerir_admin

router = APIRouter()


class ColaboradorCreate(BaseModel):
    nombres: str
    apellidos: str
    direccion: Optional[str] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None
    whatsapp: Optional[str] = None
    edad_aproximada: Optional[int] = None
    rol_descripcion: Optional[str] = None
    usuario_sistema_id: Optional[int] = None


class ColaboradorUpdate(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    direccion: Optional[str] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None
    whatsapp: Optional[str] = None
    edad_aproximada: Optional[int] = None
    rol_descripcion: Optional[str] = None
    usuario_sistema_id: Optional[int] = None


def colaborador_to_dict(c: Colaborador):
    return {
        "id": c.id,
        "nombres": c.nombres,
        "apellidos": c.apellidos,
        "direccion": c.direccion,
        "correo": c.correo,
        "telefono": c.telefono,
        "whatsapp": c.whatsapp,
        "edad_aproximada": c.edad_aproximada,
        "rol_descripcion": c.rol_descripcion,
        "usuario_sistema_id": c.usuario_sistema_id,
        "creado_en": c.creado_en.isoformat() if c.creado_en else None,
    }


@router.get("")
def listar_colaboradores(db: Session = Depends(get_db), _: Usuario = Depends(requerir_autenticado)):
    colaboradores = db.query(Colaborador).order_by(Colaborador.nombres).all()
    return [colaborador_to_dict(c) for c in colaboradores]


@router.get("/{colaborador_id}")
def obtener_colaborador(colaborador_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requerir_autenticado)):
    c = db.query(Colaborador).filter(Colaborador.id == colaborador_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Colaborador no encontrado")
    return colaborador_to_dict(c)


@router.post("")
def crear_colaborador(data: ColaboradorCreate, db: Session = Depends(get_db), _: Usuario = Depends(requerir_admin)):
    if data.usuario_sistema_id:
        usuario = db.query(Usuario).filter(Usuario.id == data.usuario_sistema_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario del sistema no encontrado")
    colaborador = Colaborador(**data.model_dump())
    db.add(colaborador)
    db.commit()
    db.refresh(colaborador)
    return {"mensaje": "Colaborador registrado correctamente", "id": colaborador.id}


@router.put("/{colaborador_id}")
def actualizar_colaborador(
    colaborador_id: int,
    data: ColaboradorUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin)
):
    colaborador = db.query(Colaborador).filter(Colaborador.id == colaborador_id).first()
    if not colaborador:
        raise HTTPException(status_code=404, detail="Colaborador no encontrado")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(colaborador, field, value)

    db.commit()
    return {"mensaje": "Colaborador actualizado correctamente"}


@router.delete("/{colaborador_id}")
def eliminar_colaborador(colaborador_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requerir_admin)):
    colaborador = db.query(Colaborador).filter(Colaborador.id == colaborador_id).first()
    if not colaborador:
        raise HTTPException(status_code=404, detail="Colaborador no encontrado")
    db.delete(colaborador)
    db.commit()
    return {"mensaje": "Colaborador eliminado correctamente"}
