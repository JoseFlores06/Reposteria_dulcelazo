from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models.cliente import Cliente
from models.venta import Venta
from models.usuario import Usuario
from models.direccion_cliente import DireccionCliente
from auth import requerir_autenticado, requerir_admin

router = APIRouter()


class ClienteCreate(BaseModel):
    nombres: str
    apellidos: str
    direccion: Optional[str] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None
    whatsapp: Optional[str] = None
    edad_aproximada: Optional[int] = None


class ClienteUpdate(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    direccion: Optional[str] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None
    whatsapp: Optional[str] = None
    edad_aproximada: Optional[int] = None


def dir_to_dict(d: DireccionCliente) -> dict:
    label = f"{d.etiqueta.capitalize()}: {d.direccion}"
    if d.distrito:
        label += f", {d.distrito}"
    return {
        "id": d.id,
        "cliente_id": d.cliente_id,
        "etiqueta": d.etiqueta,
        "direccion": d.direccion,
        "distrito": d.distrito,
        "referencia": d.referencia,
        "principal": d.principal,
        "label": label,
    }


def cliente_to_dict(c: Cliente, num_compras: int = 0):
    return {
        "id": c.id,
        "nombres": c.nombres,
        "apellidos": c.apellidos,
        "direccion": c.direccion,
        "correo": c.correo,
        "telefono": c.telefono,
        "whatsapp": c.whatsapp,
        "edad_aproximada": c.edad_aproximada,
        "creado_en": c.creado_en.isoformat() if c.creado_en else None,
        "num_compras": num_compras,
        "direcciones": [dir_to_dict(d) for d in (c.direcciones or [])],
        "num_direcciones": len(c.direcciones or []),
    }


@router.get("")
def listar_clientes(db: Session = Depends(get_db), _: Usuario = Depends(requerir_autenticado)):
    clientes = db.query(Cliente).options(joinedload(Cliente.direcciones)).order_by(Cliente.nombres).all()
    return [cliente_to_dict(c) for c in clientes]


@router.get("/recurrentes")
def clientes_recurrentes(db: Session = Depends(get_db), _: Usuario = Depends(requerir_autenticado)):
    resultados = (
        db.query(Cliente, func.count(Venta.id).label("num_compras"))
        .join(Venta, Venta.cliente_id == Cliente.id, isouter=True)
        .group_by(Cliente.id)
        .having(func.count(Venta.id) > 1)
        .order_by(func.count(Venta.id).desc())
        .all()
    )
    return [cliente_to_dict(c, num_compras) for c, num_compras in resultados]


@router.get("/{cliente_id}")
def obtener_cliente(cliente_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requerir_autenticado)):
    c = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    num_compras = db.query(func.count(Venta.id)).filter(Venta.cliente_id == cliente_id).scalar()
    return cliente_to_dict(c, num_compras)


@router.post("")
def crear_cliente(data: ClienteCreate, db: Session = Depends(get_db), _: Usuario = Depends(requerir_autenticado)):
    cliente = Cliente(**data.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return {"mensaje": "Cliente registrado correctamente", "id": cliente.id, "cliente": cliente_to_dict(cliente)}


@router.put("/{cliente_id}")
def actualizar_cliente(
    cliente_id: int,
    data: ClienteUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_autenticado)
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(cliente, field, value)

    db.commit()
    return {"mensaje": "Cliente actualizado correctamente"}


@router.delete("/{cliente_id}")
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requerir_admin)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    db.delete(cliente)
    db.commit()
    return {"mensaje": "Cliente eliminado correctamente"}


# Direcciones de clientes

class DireccionCreate(BaseModel):
    etiqueta: str = "casa"
    direccion: str
    distrito: Optional[str] = None
    referencia: Optional[str] = None
    principal: bool = False


class DireccionUpdate(BaseModel):
    etiqueta: Optional[str] = None
    direccion: Optional[str] = None
    distrito: Optional[str] = None
    referencia: Optional[str] = None
    principal: Optional[bool] = None


@router.get("/{cliente_id}/direcciones")
def listar_direcciones(cliente_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requerir_autenticado)):
    dirs = db.query(DireccionCliente).filter(DireccionCliente.cliente_id == cliente_id).order_by(DireccionCliente.principal.desc()).all()
    return [dir_to_dict(d) for d in dirs]


@router.post("/{cliente_id}/direcciones")
def crear_direccion(cliente_id: int, data: DireccionCreate, db: Session = Depends(get_db), _: Usuario = Depends(requerir_autenticado)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(404, detail="Cliente no encontrado")
    # Si se marca principal, desmarca las demás
    if data.principal:
        db.query(DireccionCliente).filter(DireccionCliente.cliente_id == cliente_id).update({"principal": False})
    d = DireccionCliente(cliente_id=cliente_id, **data.model_dump())
    db.add(d)
    db.commit()
    db.refresh(d)
    return dir_to_dict(d)


@router.put("/{cliente_id}/direcciones/{dir_id}")
def actualizar_direccion(cliente_id: int, dir_id: int, data: DireccionUpdate, db: Session = Depends(get_db), _: Usuario = Depends(requerir_autenticado)):
    d = db.query(DireccionCliente).filter(DireccionCliente.id == dir_id, DireccionCliente.cliente_id == cliente_id).first()
    if not d:
        raise HTTPException(404, detail="Dirección no encontrada")
    if data.principal:
        db.query(DireccionCliente).filter(DireccionCliente.cliente_id == cliente_id).update({"principal": False})
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(d, field, value)
    db.commit()
    db.refresh(d)
    return dir_to_dict(d)


@router.delete("/{cliente_id}/direcciones/{dir_id}")
def eliminar_direccion(cliente_id: int, dir_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requerir_autenticado)):
    d = db.query(DireccionCliente).filter(DireccionCliente.id == dir_id, DireccionCliente.cliente_id == cliente_id).first()
    if not d:
        raise HTTPException(404, detail="Dirección no encontrada")
    db.delete(d)
    db.commit()
    return {"mensaje": "Dirección eliminada"}
