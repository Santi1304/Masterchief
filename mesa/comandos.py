"""Interpreta los mensajes que el alumno escribe en Telegram (lo comparten el bot continuo y GitHub Actions)."""
import time
from datetime import datetime, timezone

from . import config
from .pipeline import normalizar_ticker, pipeline
from .telegram_io import chat_autorizado, enviar


class LimiteDeUso:
    """[SEGURIDAD] Tope diario y pausa mínima entre análisis.

    Cada análisis real gasta ~2 consultas de Alpha Vantage (25/día gratis) y 3 llamadas a Claude.
    Sin tope, un mensaje repetido (o un bucle) agotaría la cuota y el saldo.
    """

    def __init__(self):
        self.dia, self.usados, self.ultimo = None, 0, 0.0

    def permitir(self, ahora=None):
        """Devuelve None si se permite el análisis, o el motivo por el que se rechaza."""
        ahora = time.time() if ahora is None else ahora
        hoy = datetime.fromtimestamp(ahora, timezone.utc).date()
        if hoy != self.dia:
            self.dia, self.usados = hoy, 0
        if self.usados >= config.MAX_ANALISIS_POR_DIA:
            return (f"⏳ Llegaste al tope de {config.MAX_ANALISIS_POR_DIA} análisis por hoy "
                    "(cuida tu cuota de Alpha Vantage). Intenta mañana.")
        espera = config.SEGUNDOS_ENTRE_ANALISIS - (ahora - self.ultimo)
        if self.ultimo and espera > 0:
            return f"⏳ Espera {int(espera) + 1} s antes del siguiente análisis."
        self.usados, self.ultimo = self.usados + 1, ahora
        return None


LIMITE = LimiteDeUso()

AYUDA = ("🤖 Mesa Financiera de 3 agentes\n"
         "/analiza TICKER → ejemplo: /analiza AAPL\n"
         "Batuta dirige: Iris (datos por MCP) → Euler (análisis) → Vera (nota)\n"
         "Límite gratuito de Alpha Vantage: 25 consultas al día.")


def es_analisis(texto):
    return (texto or "").strip().lower().startswith("/analiza")


def atender(mensaje):
    """Procesa un mensaje de Telegram. Devuelve el resultado del pipeline o None."""
    chat_id = mensaje["chat"]["id"]
    texto = (mensaje.get("text") or "").strip()

    if not chat_autorizado(chat_id):
        enviar(chat_id, "Este bot es privado.")
        return None
    if not es_analisis(texto):
        enviar(chat_id, AYUDA)
        return None

    partes = texto.split()
    try:
        ticker = normalizar_ticker(partes[1] if len(partes) > 1 else "")
    except ValueError:
        enviar(chat_id, "Escribe un ticker válido. Ejemplo: /analiza MSFT")
        return None

    motivo = LIMITE.permitir()
    if motivo:
        enviar(chat_id, motivo)
        return None

    try:
        resultado = pipeline(ticker, avisar=lambda t: enviar(chat_id, t))
        enviar(chat_id, resultado["entrega_3_nota"])
        return resultado
    except Exception as error:
        enviar(chat_id, f"⚠️ No pude completar el análisis ({type(error).__name__}). "
                        "Revisa llaves y saldo, o intenta en unos minutos.")
        raise
