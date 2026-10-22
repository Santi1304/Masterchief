"""Configuración: lee las llaves desde variables de entorno o desde el archivo .env.

Nunca escribas una llave dentro del código. En tu computadora van en .env;
en GitHub van en Settings → Secrets and variables → Actions; en Colab, en el panel 🔑.
"""
import os

try:                                    # python-dotenv es opcional: si existe, carga .env
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _texto(nombre, defecto=""):
    return (os.environ.get(nombre) or defecto).strip()


def _bandera(nombre, defecto="0"):
    return _texto(nombre, defecto).lower() in ("1", "true", "si", "sí", "yes")


TELEGRAM_BOT_TOKEN   = _texto("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID     = _texto("TELEGRAM_CHAT_ID")        # tu chat; el bot solo atiende a este chat
ANTHROPIC_API_KEY    = _texto("ANTHROPIC_API_KEY")
ALPHAVANTAGE_API_KEY = _texto("ALPHAVANTAGE_API_KEY")

MODELO     = _texto("MODELO", "claude-haiku-5-5")        # modelo rápido y económico
MODO_CLASE = _bandera("MODO_CLASE", "1")                  # 1 = muestra cada entrega entre agentes

# Modo simulación: sin llaves de IA ni de datos. Se activa solo o con MODO_SIMULACION=1.
MODO_SIMULACION = _bandera("MODO_SIMULACION") or not (ANTHROPIC_API_KEY and ALPHAVANTAGE_API_KEY)

def _entero(nombre, defecto, minimo=0, maximo=10_000):
    """Lee un entero acotado; un valor raro no tumba el programa ni quita los límites."""
    try:
        valor = int(_texto(nombre, str(defecto)))
    except ValueError:
        valor = defecto
    return max(minimo, min(valor, maximo))


MAX_ANALISIS_POR_RUN = _entero("MAX_ANALISIS_POR_RUN", 3, 1, 10)   # cuida la cuota de Alpha Vantage
# [SEGURIDAD] Topes de uso: evitan que un error o un abuso agote la cuota de Alpha Vantage
# (25 consultas/día, ~2 por análisis) o el saldo de la API de Claude.
MAX_ANALISIS_POR_DIA = _entero("MAX_ANALISIS_POR_DIA", 10, 1, 12)
SEGUNDOS_ENTRE_ANALISIS = _entero("SEGUNDOS_ENTRE_ANALISIS", 30, 0, 3600)
CARPETA_SALIDAS = _texto("CARPETA_SALIDAS", "salidas")


def ocultar_secretos(texto):
    """[SEGURIDAD] Sustituye cualquier llave configurada por '***' antes de imprimir o enviar un texto.

    Ejemplo real: un error de red de `requests` incluye la URL completa, y esa URL lleva el
    token del bot (https://api.telegram.org/bot<TOKEN>/getUpdates). Sin este filtro el token
    aparecería en la terminal, en Colab o en una captura de pantalla.
    """
    texto = str(texto)
    for secreto in (TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, ALPHAVANTAGE_API_KEY):
        if secreto and len(secreto) >= 6:
            texto = texto.replace(secreto, "***")
    return texto


def resumen():
    """Estado de la configuración sin revelar ningún valor secreto."""
    def estado(valor):
        return "✅ configurada" if valor else "⬜ vacía"
    return {
        "TELEGRAM_BOT_TOKEN": estado(TELEGRAM_BOT_TOKEN),
        "TELEGRAM_CHAT_ID": estado(TELEGRAM_CHAT_ID),
        "ANTHROPIC_API_KEY": estado(ANTHROPIC_API_KEY),
        "ALPHAVANTAGE_API_KEY": estado(ALPHAVANTAGE_API_KEY),
        "MODELO": MODELO,
        "MODO_SIMULACION": "sí" if MODO_SIMULACION else "no (datos y agentes reales)",
    }
