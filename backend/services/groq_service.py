"""
Servicio de IA con Groq API.
Usos: sugerencias de promociones, nombres de productos, resumen de ventas, análisis de stock.
"""
import os
import json

# Modelo de Groq. `llama3-8b-8192` fue descomisionado (jun-2026); usamos el
# sucesor actual. Configurable por env para futuros cambios sin tocar código.
# Modelos activos: llama-3.1-8b-instant (rápido), llama-3.3-70b-versatile (potente).
MODELO = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


def _get_client():
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key == "tu_groq_api_key_aqui":
        return None
    from groq import Groq
    return Groq(api_key=api_key)


# 1. Sugerencias de promociones

def sugerir_promociones(nombre_item: str, precio_original: float, costo_real: float) -> list:
    """Sugiere 3 niveles de descuento para un item."""
    client = _get_client()
    if not client:
        return _sugerencias_locales_promo(nombre_item, precio_original, costo_real)

    try:
        prompt = f"""Eres un experto en marketing de pastelerías peruanas.
Para el producto "{nombre_item}" con precio S/ {precio_original:.2f} y costo S/ {costo_real:.2f},
sugiere 3 niveles de promoción en JSON exacto:
[
  {{"nivel": "Oferta Suave", "porcentaje_descuento": X, "descripcion": "..."}},
  {{"nivel": "Oferta Atractiva", "porcentaje_descuento": X, "descripcion": "..."}},
  {{"nivel": "Oferta Agresiva", "porcentaje_descuento": X, "descripcion": "..."}}
]
Oferta Suave: 5-10%. Oferta Atractiva: 15-20%. Oferta Agresiva: 25-35%.
Solo responde con el JSON."""

        resp = client.chat.completions.create(
            model=MODELO,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        sugerencias_raw = json.loads(resp.choices[0].message.content.strip())
        resultado = []
        for s in sugerencias_raw:
            pct = float(s["porcentaje_descuento"])
            precio_promo = precio_original * (1 - pct / 100)
            margen = ((precio_promo - costo_real) / precio_promo * 100) if precio_promo > 0 else 0
            resultado.append({
                "nivel": s["nivel"],
                "porcentaje_descuento": pct,
                "precio_promocion": round(precio_promo, 2),
                "margen_restante": round(margen, 1),
                "descripcion": s.get("descripcion", ""),
            })
        return resultado
    except Exception:
        return _sugerencias_locales_promo(nombre_item, precio_original, costo_real)


def _sugerencias_locales_promo(nombre_item: str, precio_original: float, costo_real: float) -> list:
    niveles = [
        ("Oferta Suave", 7, "Descuento leve, ideal para fidelizar clientes frecuentes."),
        ("Oferta Atractiva", 17, "Descuento moderado, atrae nuevos clientes sin sacrificar margen."),
        ("Oferta Agresiva", 30, "Descuento fuerte, útil para liquidar stock o eventos especiales."),
    ]
    resultado = []
    for nivel, pct, desc in niveles:
        precio_promo = precio_original * (1 - pct / 100)
        margen = ((precio_promo - costo_real) / precio_promo * 100) if precio_promo > 0 else 0
        resultado.append({
            "nivel": nivel,
            "porcentaje_descuento": pct,
            "precio_promocion": round(precio_promo, 2),
            "margen_restante": round(margen, 1),
            "descripcion": desc,
        })
    return resultado


# 2. Sugerencias de nombres para productos

def sugerir_nombres_producto(descripcion: str, insumos: list[str]) -> list[str]:
    """Sugiere 5 nombres creativos para un nuevo producto de pastelería."""
    client = _get_client()
    insumos_str = ", ".join(insumos) if insumos else "varios ingredientes"

    if not client:
        return [f"{descripcion} Artesanal", f"Delicias de {descripcion}", f"{descripcion} Premium",
                f"Especialidad Dulce Lazo: {descripcion}", f"{descripcion} Casero"]

    try:
        prompt = f"""Eres un experto en naming de pastelerías peruanas artesanales.
Sugiere exactamente 5 nombres creativos y atractivos para un producto de pastelería.
Descripción del producto: {descripcion}
Ingredientes principales: {insumos_str}
Responde SOLO con un JSON de lista: ["nombre1", "nombre2", "nombre3", "nombre4", "nombre5"]
Los nombres deben ser en español, creativos, evocadores y apropiados para una pastelería artesanal peruana."""

        resp = client.chat.completions.create(
            model=MODELO,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return json.loads(resp.choices[0].message.content.strip())
    except Exception:
        return [f"{descripcion} Artesanal", f"Delicia de {descripcion}", f"{descripcion} Especial",
                f"Clásico de Dulce Lazo: {descripcion}", f"{descripcion} Premium"]


# 3. Análisis de ventas y recomendaciones

def analizar_ventas(resumen: dict) -> str:
    """
    Analiza un resumen de ventas y genera recomendaciones de negocio.
    resumen = {total_ventas: int, ingresos: float, producto_top: str, mes: str}
    """
    client = _get_client()
    if not client:
        return _analisis_local(resumen)

    try:
        prompt = f"""Eres un consultor de negocios especializado en pastelerías peruanas artesanales.
Analiza este resumen de ventas de la pastelería "Dulce Lazo" y da 3-4 recomendaciones concretas:

Período: {resumen.get('mes', 'último mes')}
Total de ventas: {resumen.get('total_ventas', 0)} pedidos
Ingresos totales: S/ {resumen.get('ingresos', 0):.2f}
Producto más vendido: {resumen.get('producto_top', 'N/A')}
Ingresos promedio por venta: S/ {resumen.get('promedio', 0):.2f}

Responde en español con recomendaciones prácticas y específicas para una pastelería pequeña.
Máximo 150 palabras. Formato: párrafo directo, sin bullets."""

        resp = client.chat.completions.create(
            model=MODELO,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return _analisis_local(resumen)


def _analisis_local(resumen: dict) -> str:
    ingresos = resumen.get("ingresos", 0)
    ventas = resumen.get("total_ventas", 0)
    if ventas == 0:
        return "No hay ventas registradas en este período. Considera activar promociones para atraer clientes."
    promedio = ingresos / ventas
    if promedio < 20:
        return "El ticket promedio es bajo. Considera crear paquetes combinados para aumentar el valor por pedido."
    return f"Con {ventas} ventas y S/ {ingresos:.2f} en ingresos, el ticket promedio es S/ {promedio:.2f}. Buen rendimiento — considera fidelizar a los clientes frecuentes con promociones exclusivas."


# 4. Alerta inteligente de stock bajo

def generar_mensajes_whatsapp(productos: list, paquetes: list, promociones: list) -> list:
    """
    Genera 5 mensajes de WhatsApp humanizados y coloquiales para enviar a clientes,
    basados en los productos, paquetes y promociones actuales.
    Retorna lista de dicts con: {titulo, mensaje, tipo, emoji}
    """
    client = _get_client()

    def _fallback():
        msgs = []
        if promociones:
            p = promociones[0]
            msgs.append({
                "titulo": "Oferta del día",
                "mensaje": f"Hola! 👋 Hoy tenemos {p['nombre']} con descuento especial. No te lo pierdas, hecho con mucho amor en Dulce Lazo 🧁",
                "tipo": "promocion", "emoji": "🎉"
            })
        if paquetes:
            pk = paquetes[0]
            msgs.append({
                "titulo": "Pack especial",
                "mensaje": f"¿Buscas el regalo perfecto? 🎁 Tenemos el pack '{pk['nombre']}' perfecto para cualquier ocasión. Escríbenos!",
                "tipo": "paquete", "emoji": "🎁"
            })
        msgs.append({
            "titulo": "Recordatorio de pedidos",
            "mensaje": "Hola! 😊 ¿Ya pensaste en el postre para tu próximo evento? En Dulce Lazo hacemos tortas, cupcakes y más con mucho amor artesanal. Cotiza con nosotros!",
            "tipo": "general", "emoji": "💝"
        })
        return msgs

    if not client:
        return _fallback()

    try:
        prods_str = ", ".join(p['nombre'] for p in productos[:5]) if productos else "variedad de postres artesanales"
        packs_str = ", ".join(p['nombre'] for p in paquetes[:3]) if paquetes else "packs especiales"
        promos_str = ", ".join(f"{p['nombre']} ({p.get('descuento_porcentaje', 0)}% off)" for p in promociones[:3]) if promociones else "sin promociones activas"

        prompt = f"""Eres el community manager de Dulce Lazo, una pastelería artesanal peruana pequeña y amorosa.
Crea exactamente 5 mensajes de WhatsApp para enviar a clientes potenciales.

Productos disponibles: {prods_str}
Packs/paquetes: {packs_str}
Promociones activas: {promos_str}

REGLAS IMPORTANTES:
- Usa lenguaje coloquial peruano, cálido y cercano (puedes usar "pe", "causa", "chévere", "bacán" con moderación)
- Máximo 80 palabras por mensaje
- Incluye emojis apropiados pero sin exceso (1-3 por mensaje)
- Varía los estilos: urgencia, emocional, informativo, pregunta, celebración
- Menciona productos o promos específicas cuando sea relevante
- NO uses frases genéricas de marketing corporativo

Responde SOLO con JSON:
[
  {{"titulo": "...", "mensaje": "...", "tipo": "promocion|producto|paquete|fidelizacion|general", "emoji": "🧁"}},
  ...5 items...
]"""

        resp = client.chat.completions.create(
            model=MODELO,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
        )
        raw = resp.choices[0].message.content.strip()
        # Extraer JSON si viene con texto extra
        inicio = raw.find('[')
        fin = raw.rfind(']') + 1
        if inicio >= 0 and fin > inicio:
            raw = raw[inicio:fin]
        return json.loads(raw)
    except Exception:
        return _fallback()


def generar_mensaje_stock_bajo(insumos_bajos: list[dict]) -> str:
    """
    Genera un mensaje amigable de alerta de stock bajo usando IA.
    insumos_bajos = [{"nombre": str, "stock_actual": float, "unidad": str}, ...]
    """
    client = _get_client()
    if not client:
        nombres = ", ".join(i["nombre"] for i in insumos_bajos)
        return f"Stock bajo en: {nombres}. Reabastecer pronto para no interrumpir la producción."

    try:
        lista_str = "\n".join(
            f"- {i['nombre']}: {i['stock_actual']:.2f} {i['unidad']} restantes"
            for i in insumos_bajos
        )
        prompt = f"""Eres la asistente de una pastelería artesanal peruana llamada Dulce Lazo.
Escribe un mensaje de alerta breve y amigable (máximo 60 palabras) avisando que estos insumos tienen poco stock:
{lista_str}
El mensaje debe ser directo, urgente pero amable, en español, sin emojis excesivos."""

        resp = client.chat.completions.create(
            model=MODELO,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        nombres = ", ".join(i["nombre"] for i in insumos_bajos)
        return f"Stock bajo en: {nombres}. Reabastecer pronto para no interrumpir la producción."


# 5. Prompts publicitarios para Canva/ChatGPT (a medida del negocio)

def generar_prompts_canva(productos: list, promociones: list,
                          peticion: str = None, plataforma: str = None) -> list:
    """
    Genera prompts de publicidad LISTOS para usar en Canva/ChatGPT, a medida del
    negocio según sus productos y promociones activas. Opcionalmente enfocados en
    un pedido del usuario (texto libre) y/o una plataforma específica.
    Retorna lista de dicts: {titulo, plataforma, prompt, emoji}
    """
    client = _get_client()
    if not client:
        return _prompts_canva_fallback()

    try:
        prods_str = ", ".join(p["nombre"] for p in productos[:8]) if productos else \
            "variedad de postres artesanales (tortas, cupcakes, postres)"
        if promociones:
            promos_str = ", ".join(
                p["nombre"] + (f" ({p.get('descuento_porcentaje', 0):.0f}% dcto)" if p.get("descuento_porcentaje") else "")
                for p in promociones[:5]
            )
        else:
            promos_str = "sin promociones activas por ahora"

        pet = f'\nPedido específico del usuario (priorízalo): "{peticion.strip()}"' if peticion and peticion.strip() else ""
        plat = (f"\nEnfoca TODOS los prompts en la plataforma: {plataforma}."
                if plataforma else
                "\nVaría las plataformas entre Instagram, Facebook, TikTok y Canva.")

        prompt = f"""Eres director creativo de marketing de "Dulce Lazo", una pastelería artesanal peruana.
Genera exactamente 4 prompts LISTOS PARA COPIAR Y PEGAR en Canva o ChatGPT, para crear piezas publicitarias reales de este negocio.

Productos actuales: {prods_str}
Promociones activas: {promos_str}{pet}{plat}

REGLAS:
- Cada prompt debe ser detallado y específico (3 a 5 frases), mencionando productos o promociones REALES de las listas cuando tenga sentido.
- Incluye indicaciones de diseño: formato/medidas, paleta rosa pastel de la marca (#fdf2f8, #ec4899, #9d174d), tono cálido peruano y una llamada a la acción por WhatsApp.
- Deben ser accionables de inmediato.

Responde SOLO con un objeto JSON válido con esta forma exacta:
{{"prompts": [
  {{"titulo": "...", "plataforma": "Instagram|Facebook|TikTok|Canva|ChatGPT", "prompt": "...", "emoji": "🎨"}}
]}}
(exactamente 4 elementos en "prompts")"""

        resp = client.chat.completions.create(
            model=MODELO,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.85,
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content.strip())
        prompts = data.get("prompts") if isinstance(data, dict) else data
        prompts = [d for d in (prompts or []) if isinstance(d, dict) and d.get("prompt")]
        return prompts or _prompts_canva_fallback()
    except Exception:
        return _prompts_canva_fallback()


def _prompts_canva_fallback() -> list:
    return [
        {
            "titulo": "Flyer de promoción en Instagram",
            "plataforma": "Canva + ChatGPT",
            "prompt": "Crea un diseño de flyer para Instagram de la pastelería 'Dulce Lazo'. Fondo rosa pastel (#fdf2f8), tipografía elegante en rosa oscuro (#9d174d). Incluye: nombre del producto, precio con descuento tachando el precio original, y el texto 'Hecho con amor artesanal'. Formato cuadrado 1080x1080px.",
            "emoji": "📸",
        },
        {
            "titulo": "Historia de Facebook con oferta del día",
            "plataforma": "Canva",
            "prompt": "Diseña una historia para Facebook de 9:16 para Dulce Lazo. Usa gradiente rosa (#ec4899 a #be185d). Texto grande 'OFERTA DEL DÍA' en blanco, foto del producto al centro, precio destacado en círculo dorado. Añade urgencia: '¡Solo hoy!'.",
            "emoji": "📱",
        },
        {
            "titulo": "Post de catálogo de productos",
            "plataforma": "ChatGPT + Canva",
            "prompt": "Ayúdame a crear un carrusel de 5 slides para Instagram mostrando el catálogo de Dulce Lazo. Slide 1: portada con logo. Slides 2-4: un producto por slide con foto, nombre y precio. Slide 5: llamada a la acción con WhatsApp. Paleta: rosado suave y blanco.",
            "emoji": "🎨",
        },
        {
            "titulo": "Reels/TikTok - guion de video",
            "plataforma": "ChatGPT",
            "prompt": "Crea un guion de 30 segundos para un Reel de Instagram o TikTok de Dulce Lazo mostrando el proceso de preparación de un producto. Incluye: narración en off coloquial peruana, sugerencias de tomas (close-up, manos, producto final), música sugerida (tipo 'happy cooking'), y texto overlay. Termina con precio y WhatsApp.",
            "emoji": "🎬",
        },
    ]
