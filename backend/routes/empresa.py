from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models.empresa import Empresa
from models.usuario import Usuario
from auth import requerir_admin

router = APIRouter()


class EmpresaSchema(BaseModel):
    nombre: str
    ruc: Optional[str] = None
    numero_yape_plin: Optional[str] = None
    nro_cuenta_banco: Optional[str] = None
    cci: Optional[str] = None
    direccion: Optional[str] = None
    distrito: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None


def empresa_to_dict(empresa: Empresa) -> dict:
    return {
        "id": empresa.id,
        "nombre": empresa.nombre,
        "ruc": empresa.ruc,
        "numero_yape_plin": empresa.numero_yape_plin,
        "nro_cuenta_banco": empresa.nro_cuenta_banco,
        "cci": empresa.cci,
        "direccion": empresa.direccion,
        "distrito": empresa.distrito,
        "telefono": empresa.telefono,
        "correo": empresa.correo,
    }


@router.get("")
def obtener_empresa(db: Session = Depends(get_db), _: Usuario = Depends(requerir_admin)):
    empresa = db.query(Empresa).first()
    if not empresa:
        return {}
    return empresa_to_dict(empresa)


@router.put("")
def actualizar_empresa(data: EmpresaSchema, db: Session = Depends(get_db), _: Usuario = Depends(requerir_admin)):
    empresa = db.query(Empresa).first()
    if not empresa:
        empresa = Empresa()
        db.add(empresa)

    empresa.nombre = data.nombre
    empresa.ruc = data.ruc
    empresa.numero_yape_plin = data.numero_yape_plin
    empresa.nro_cuenta_banco = data.nro_cuenta_banco
    empresa.cci = data.cci
    empresa.direccion = data.direccion
    empresa.distrito = data.distrito
    empresa.telefono = data.telefono
    empresa.correo = data.correo

    db.commit()
    db.refresh(empresa)
    return {"mensaje": "Datos de empresa actualizados correctamente", "empresa": empresa_to_dict(empresa)}
