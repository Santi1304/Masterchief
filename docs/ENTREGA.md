# Entrega · Mesa Financiera en Telegram

> Borrador preparado con apoyo de Claude. **Ajusta la reflexión con tu propia experiencia** antes de entregarla.

## 1. Cambio de LLM
El ecosistema ya usaba la **API de Anthropic (Claude)**, así que no fue necesario migrar de proveedor.
Se mantuvo `claude-haiku-5-5` (rápido y económico para 3 llamadas por análisis) y se reforzó la integración:
SDK fijado en `anthropic==2.1.0`, `timeout=60 s` y `max_retries=2` (`mesa/agentes.py`, `_cliente_claude`).

## 2. Personalidad y tema de investigación
| Agente | Antes | Después |
|---|---|---|
| **Vera** | Clara, breve y honesta; nota para principiantes, 3-5 emojis, 900 caracteres | **"Mesa de dinero"**: directa, sobria y escéptica; para inversionista experimentado; formato tipo terminal (`TICKER \| precio \| cambio`), máx. 700 caracteres y 2 emojis; agrega siempre el **punto ciego** del análisis; nunca dice comprar/vender/mantener |
| **Euler** | Interpreta para principiantes; pregunta sobre el P/E del sector | Tema: **momentum frente al rango anual** y valuación frente a competidores. Nuevo indicador **en Python**: distancia al máximo anual = (P_max − Pₜ) / P_max × 100. Ejemplo: (180 − 150) / 180 × 100 = **16.7 %** |

## 3. Cron
| | Antes | Después |
|---|---|---|
| Expresión | `*/10 * * * *` | `*/15 13-21 * * 1-5` + `7 15 * * 0,6` |
| Significado | Cada 10 min, 24 h, 7 días | Cada 15 min lun-vie 07:00-15:45 CDMX + 1 vez sáb/dom (09:07 CDMX) |
| Ejecuciones al día | 144 | 36 (hábil) / 1 (fin de semana) |
| Por qué | — | Los precios solo cambian con la bolsa de NY abierta; se ahorran ~75 % de ejecuciones. La revisión del fin de semana evita perder mensajes (Telegram los guarda solo 24 h). |

## 4. Seguridad
Ver [`SECURITY.md`](../SECURITY.md): 9 hallazgos con evidencia (archivo:línea), corrección y prueba automática.

## 5. Liga a GitHub
`https://github.com/<TU_USUARIO>/mesa-financiera-telegram` ← sustituir

## 6. Screenshot de Telegram en tiempo real
Opción recomendada, **Codespaces** (usa este código actualizado):
1. Code → Codespaces → Create codespace on main (con tus 4 Codespaces secrets).
2. En la terminal: `python bot_continuo.py` → debe decir `✅ Bot @tu_bot escuchando`.
3. En Telegram: `/analiza AAPL` → verás Batuta, Iris, las entregas 1→2 y 2→3 y la nota de Vera en formato "mesa de dinero".
4. Captura con la **hora visible**. Prueba también `/analiza AAPL;x` → "Escribe un ticker válido".
5. Revisa que la captura **no muestre ninguna llave**.

> Nota: el notebook de Colab (Ruta A) tiene su propia copia del código y **no** incluye estos cambios.

## 7. Reflexión y conclusión (borrador)

**¿Por qué los cálculos los hace Python y no la IA?**
Porque un modelo de lenguaje predice texto: puede escribir una cifra plausible pero incorrecta. Python es
determinista y verificable con pruebas (`test_formula_posicion_rango_52_semanas`, `test_distancia_al_maximo_anual`).
Por eso el indicador nuevo se agregó en `calcular_indicadores` y no en el prompt.

**¿Qué pasaría si Iris inventara un dato?**
El error se propagaría por toda la cadena, porque la salida de un agente es la entrada del siguiente. Lo reducen:
la regla "si no existe, `null`", la fuente marcada en la ficha, la validación por lista blanca que agregué
(`validar_ficha`) y que Euler y Vera no puedan recalcular cifras.

**¿En qué se diferencia Telegram de Batuta?**
Telegram es la ventanilla: recibe la orden y muestra el resultado. Batuta (`pipeline.py`) decide el orden de los
agentes y pasa cada entrega. Se podría cambiar Telegram por otra interfaz sin tocar a Batuta.

**Ruta A frente a Ruta B.**
En la nube gano disponibilidad con la computadora apagada; pierdo inmediatez (la respuesta llega en la siguiente
revisión del cron). Al cambiar el cron vi el trade-off: menos ejecuciones ahorran recursos, pero fuera del
horario de mercado la respuesta tarda más.

**¿Para qué sirve que las pruebas corran en cada push?**
Al aplicar las mejoras de seguridad, una prueba existente falló: la nueva pausa de 30 s bloqueaba el segundo
mensaje del lote de GitHub Actions. Sin las pruebas, ese error habría llegado a producción.

**¿Por qué el descargo?**
Porque la nota puede leerse como recomendación. Ahora el código garantiza que el descargo quede siempre **al final**,
aunque el modelo lo olvide o lo ponga a la mitad.

**Conclusión.**
La actividad muestra que un sistema multiagente confiable depende menos del modelo y más del diseño a su alrededor:
contratos claros entre agentes (JSON), cálculos deterministas, validación de lo que entra y sale, y controles de
seguridad. La revisión encontró riesgos reales que no eran evidentes, como el token del bot expuesto en un mensaje de
error de red o un bot abierto a cualquiera si faltaba el `TELEGRAM_CHAT_ID`. Cambiar la personalidad de Vera solo
requirió modificar un prompt, sin tocar las cifras. Esto confirma que separar "quién calcula" de "quién comunica"
permite personalizar sin perder exactitud.
