"""
Servicio de Google Calendar con OAuth2 completo.
"""
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# OAuth en entorno local: permitir redirect por HTTP (no HTTPS) y tolerar que
# Google devuelva los scopes en distinto orden/cantidad (evita "Scope has changed").
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

LIMA_TZ = ZoneInfo("America/Lima")
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

# Debe coincidir EXACTAMENTE con un "URI de redireccionamiento autorizado"
# registrado en Google Cloud Console para este OAuth Client ID.
REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/calendario/callback"
)


def _client_config():
    return {
        "web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
            "redirect_uris": [REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def _build_flow():
    """Crea el Flow de OAuth con PKCE DESACTIVADO.

    El flujo se divide en dos peticiones distintas (generar la URL en /auth-url y
    canjear el código en /callback), cada una con su propio objeto Flow. Con PKCE
    activado, la librería genera un `code_verifier` al crear la URL que se pierde al
    devolver la respuesta, por lo que en el callback no se puede reenviar y Google
    responde `(invalid_grant) Missing code verifier`. Como este es un cliente OAuth
    de tipo "Web" con `client_secret`, PKCE no es necesario; desactivarlo
    (`autogenerate_code_verifier=False`) hace que NO se mande `code_challenge` y el
    canje funcione con el flujo clásico de código de autorización.
    """
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_config(
        _client_config(), scopes=SCOPES, autogenerate_code_verifier=False
    )
    flow.redirect_uri = REDIRECT_URI
    return flow


def get_auth_url() -> str:
    """Genera la URL de autorización de Google."""
    flow = _build_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="select_account consent",
    )
    return auth_url


def exchange_code_for_tokens(code: str) -> dict:
    """Intercambia el código de autorización por tokens."""
    flow = _build_flow()
    flow.fetch_token(code=code)
    creds = flow.credentials
    return {
        "refresh_token": creds.refresh_token,
        "access_token": creds.token,
        "expiry": creds.expiry,
    }


def get_account_email(access_token: str) -> str:
    """Obtiene el email de la cuenta Google autenticada."""
    try:
        import urllib.request, json
        req = urllib.request.Request(
            f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}"
        )
        with urllib.request.urlopen(req) as resp:
            info = json.loads(resp.read())
            return info.get("email", "")
    except Exception:
        return ""


def get_calendar_service(refresh_token: str):
    """Retorna el servicio de Google Calendar autenticado."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=SCOPES,
    )
    return build("calendar", "v3", credentials=creds)


def esta_conectado(db) -> bool:
    """Verifica si hay un refresh_token guardado."""
    from models.configuracion_google import ConfiguracionGoogle
    cfg = db.query(ConfiguracionGoogle).first()
    return cfg is not None and bool(cfg.refresh_token)


def crear_evento_stock_bajo(db, insumos_bajos: list) -> bool:
    """
    Crea un evento en Google Calendar avisando del stock bajo.
    Retorna True si se creó, False si no hay conexión.
    """
    if not insumos_bajos:
        return False

    from models.configuracion_google import ConfiguracionGoogle
    cfg = db.query(ConfiguracionGoogle).first()
    if not cfg or not cfg.refresh_token:
        return False

    try:
        service = get_calendar_service(cfg.refresh_token)

        ahora_lima = datetime.now(LIMA_TZ)
        fecha_str = ahora_lima.strftime("%Y-%m-%d")

        # Construir descripción
        lineas = []
        for ins in insumos_bajos:
            lineas.append(
                f"• {ins.nombre}: {float(ins.stock_actual):.2f} {ins.unidad} restantes"
            )
        descripcion = (
            "⚠️ ALERTA: Los siguientes insumos tienen stock bajo en Dulce Lazo.\n"
            "NO se podrán realizar ventas con estos productos hasta reabastecer.\n\n"
            + "\n".join(lineas)
        )

        evento = {
            "summary": f"⚠️ Stock Bajo — {len(insumos_bajos)} insumo(s) crítico(s)",
            "description": descripcion,
            "start": {"date": fecha_str, "timeZone": "America/Lima"},
            "end": {"date": fecha_str, "timeZone": "America/Lima"},
            "colorId": "11",  # rojo en Google Calendar
            "reminders": {
                "useDefault": False,
                "overrides": [{"method": "popup", "minutes": 0}],
            },
        }

        service.events().insert(calendarId="primary", body=evento).execute()
        return True

    except Exception as e:
        print(f"[Calendar] Error creando evento: {e}")
        return False


def crear_evento_venta(db, venta, fecha_entrega: datetime) -> bool:
    """Crea un recordatorio de entrega en Google Calendar."""
    from models.configuracion_google import ConfiguracionGoogle
    cfg = db.query(ConfiguracionGoogle).first()
    if not cfg or not cfg.refresh_token:
        return False

    try:
        service = get_calendar_service(cfg.refresh_token)

        fecha_entrega_lima = fecha_entrega.astimezone(LIMA_TZ)
        inicio = fecha_entrega_lima.isoformat()
        fin = (fecha_entrega_lima + timedelta(hours=1)).isoformat()

        evento = {
            "summary": f"🧁 Entrega — {venta.cliente.nombres} {venta.cliente.apellidos}",
            "description": (
                f"Entrega de pedido #{venta.id}\n"
                f"Cliente: {venta.cliente.nombres} {venta.cliente.apellidos}\n"
                f"Total: S/ {float(venta.total):.2f}\n"
                f"Notas: {venta.notas or 'Sin notas'}"
            ),
            "start": {"dateTime": inicio, "timeZone": "America/Lima"},
            "end": {"dateTime": fin, "timeZone": "America/Lima"},
            "colorId": "2",  # verde
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 60},
                    {"method": "email", "minutes": 120},
                ],
            },
        }

        service.events().insert(calendarId="primary", body=evento).execute()
        return True

    except Exception as e:
        print(f"[Calendar] Error creando evento venta: {e}")
        return False
