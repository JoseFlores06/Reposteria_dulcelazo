import os
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from models.usuario import Usuario
from models.configuracion_google import ConfiguracionGoogle
from auth import requerir_admin
from services.google_calendar import (
    get_auth_url, exchange_code_for_tokens, esta_conectado,
    get_calendar_service, get_account_email,
)

router = APIRouter()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


@router.get("/estado")
def estado_calendario(
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    from models.configuracion_google import ConfiguracionGoogle
    cfg = db.query(ConfiguracionGoogle).first()
    conectado = cfg is not None and bool(cfg.refresh_token)
    return {
        "conectado": conectado,
        "cuenta_email": cfg.cuenta_email if (cfg and cfg.cuenta_email) else None,
        "mensaje": f"Conectado como {cfg.cuenta_email}" if (conectado and cfg and cfg.cuenta_email) else (
            "Conectado a Google Calendar" if conectado else "No conectado — haz clic en 'Conectar Google Calendar'"
        ),
    }


@router.get("/auth-url")
def obtener_auth_url(_: Usuario = Depends(requerir_admin)):
    """Genera la URL de autorización de Google."""
    try:
        url = get_auth_url()
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando URL: {e}")


@router.get("/callback")
def callback_google(code: str, db: Session = Depends(get_db)):
    """Google redirige aquí con el código de autorización."""
    try:
        tokens = exchange_code_for_tokens(code)

        cfg = db.query(ConfiguracionGoogle).first()
        if not cfg:
            cfg = ConfiguracionGoogle()
            db.add(cfg)

        cfg.refresh_token = tokens.get("refresh_token") or (cfg.refresh_token if cfg else None)
        cfg.access_token = tokens.get("access_token")
        cfg.expiry = tokens.get("expiry")
        if tokens.get("access_token"):
            cfg.cuenta_email = get_account_email(tokens["access_token"])
        db.commit()

        return RedirectResponse(url=f"{FRONTEND_URL}/calendario?conectado=true")
    except Exception as e:
        print(f"[Calendar] Error en callback OAuth: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}/calendario?error={quote(str(e)[:300])}")


@router.delete("/desconectar")
def desconectar_google(db: Session = Depends(get_db), _: Usuario = Depends(requerir_admin)):
    """Elimina los tokens de Google."""
    cfg = db.query(ConfiguracionGoogle).first()
    if cfg:
        cfg.refresh_token = None
        cfg.access_token = None
        cfg.expiry = None
        db.commit()
    return {"mensaje": "Google Calendar desconectado"}


@router.get("/eventos")
def listar_eventos(db: Session = Depends(get_db), _: Usuario = Depends(requerir_admin)):
    """Lista los próximos 10 eventos del calendario."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    cfg = db.query(ConfiguracionGoogle).first()
    if not cfg or not cfg.refresh_token:
        return {"eventos": [], "conectado": False}

    try:
        service = get_calendar_service(cfg.refresh_token)
        ahora = datetime.now(ZoneInfo("America/Lima")).isoformat()
        result = service.events().list(
            calendarId="primary",
            timeMin=ahora,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        eventos = []
        for e in result.get("items", []):
            start = e.get("start", {})
            eventos.append({
                "id": e.get("id"),
                "titulo": e.get("summary"),
                "descripcion": e.get("description"),
                "inicio": start.get("dateTime") or start.get("date"),
                "color": e.get("colorId"),
            })
        return {"eventos": eventos, "conectado": True}
    except Exception as ex:
        return {"eventos": [], "conectado": True, "error": str(ex)}
