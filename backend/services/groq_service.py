"""
Servicio de IA con Groq API.
Usos: sugerencias de promociones, nombres de productos, resumen de ventas, análisis de stock.
"""
import os
import json

# Los modelos Llama 3.x fueron retirados de Groq; el catálogo actual expone
# la familia GPT-OSS. Configurable por env para cambiar de modelo sin tocar código.
MODELO = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


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
