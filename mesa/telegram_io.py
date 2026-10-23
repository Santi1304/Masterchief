"""Comunicación con Telegram mediante la Bot API (solo peticiones HTTP, sin librerías extra)."""
import requests

from . import config

LIMITE_MENSAJE = 4000          # Telegram acepta hasta 4096 caracteres por mensaje


def _url(metodo):
    if not config.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN (créalo con @BotFather).")
    return f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/{metodo}"


def _peticion(verbo, metodo, timeout=20, **kwargs):
    """[SEGURIDAD] Llama a la Bot API sin filtrar el token en los errores.

    Los errores de `requests` incluyen la URL, y la URL incluye el token. Aquí se reemplaza
    por un error genérico (sin URL) y con cualquier secreto oculto.
    """
    try:
        respuesta = requests.request(verbo, _url(metodo), timeout=timeout, **kwargs)
        return respuesta.json()
    except (requests.RequestException, ValueError) as error:
        raise ConnectionError(
            f"Fallo de red con Telegram en {metodo} ({type(error).__name__}): "
            + config.ocultar_secretos(error)[:200]) from None


def _explicar_error(datos):
    """Traduce los errores más comunes de Telegram a una indicación concreta."""
    descripcion = str(datos.get("description", ""))
    if datos.get("error_code") in (401, 404) or descripcion in ("Not Found", "Unauthorized"):
        return ("Telegram no reconoce TELEGRAM_BOT_TOKEN (respuesta: " + descripcion + "). "
                "Diagnóstico del formato (sin mostrar el valor): " + "; ".join(config.diagnostico_token()))
    if "chat not found" in descripcion.lower():
        return ("Telegram no encuentra TELEGRAM_CHAT_ID. Escribe 'hola' a tu bot y ejecuta "
                "python obtener_chat_id.py para obtener el número correcto.")
    return f"Telegram rechazó el mensaje: {descripcion}"


def enviar(chat_id, texto):
    datos = _peticion("POST", "sendMessage",
                      data={"chat_id": chat_id, "text": str(texto)[:LIMITE_MENSAJE],
                            "disable_web_page_preview": "true"})
    if not datos.get("ok"):
        raise RuntimeError(_explicar_error(datos))
    return datos


def verificar_bot():
    """Devuelve el @usuario del bot o lanza un error claro si el token es inválido."""
    datos = _peticion("GET", "getMe")
    if not datos.get("ok"):
        raise RuntimeError(_explicar_error(datos))
    return datos["result"]["username"]


def preparar_polling():
    """Quita un webhook previo; si existe, getUpdates no funciona."""
    _peticion("GET", "deleteWebhook")


def obtener_mensajes(offset=None, espera=0):
    """Mensajes pendientes. Telegram los guarda hasta 24 h si nadie los lee."""
    parametros = {"timeout": espera}
    if offset is not None:
        parametros["offset"] = offset
    datos = _peticion("GET", "getUpdates", params=parametros, timeout=espera + 15)
    if not datos.get("ok"):
        raise RuntimeError(f"getUpdates falló: {datos.get('description')}")
    return datos["result"]


def confirmar_leidos(ultimo_update_id):
    """Marca como leídos todos los mensajes hasta ese id, para no procesarlos dos veces."""
    obtener_mensajes(offset=ultimo_update_id + 1)


def chat_autorizado(chat_id):
    """[SEGURIDAD] Solo el chat de TELEGRAM_CHAT_ID puede usar el bot.

    Antes, si TELEGRAM_CHAT_ID estaba vacío el bot atendía a CUALQUIER persona que lo encontrara
    (y gastaba tu cuota y tu saldo). Ahora falla cerrado: sin chat configurado, no atiende a nadie.
    """
    return bool(config.TELEGRAM_CHAT_ID) and str(chat_id) == config.TELEGRAM_CHAT_ID
