# Recomendaciones de seguridad · Mesa Financiera en Telegram

Revisión del código de la plantilla (commit `ec27a90`) y cambios aplicados en este repositorio.
Cada hallazgo cita el archivo y la línea **del código original** donde se observó el riesgo.

**Convención:** **Dato** = lo que se observa en el código o se reprodujo · **Inferencia** = consecuencia
probable · **Supuesto** = condición que no se pudo verificar.

## Resumen ejecutivo

| # | Prioridad | Hallazgo | Evidencia (código original) | Corrección aplicada | Cómo se verifica |
|---|---|---|---|---|---|
| S1 | 🔴 Alta | El bot atendía a **cualquier persona** si `TELEGRAM_CHAT_ID` estaba vacío (falla abierta). | `mesa/telegram_io.py:55` → `return not config.TELEGRAM_CHAT_ID or ...` | Falla cerrada: sin chat configurado no atiende a nadie. | `test_sin_chat_id_no_atiende_a_nadie` |
| S2 | 🔴 Alta | Un error de red **mostraba el token del bot** en pantalla. **Dato (reproducido):** `requests` devuelve `Max retries exceeded with url: /bot<TOKEN>/getMe`. | `bot_continuo.py:30`, `bot_continuo.py:28`, `revisar_telegram.py:40`, `verificar_configuracion.py` (rama ❌ de Telegram) | `_peticion()` en `telegram_io.py` convierte el error en uno genérico sin URL; `config.ocultar_secretos()` reemplaza cualquier llave por `***` antes de imprimir. | `test_error_de_red_no_muestra_el_token`, `test_ocultar_secretos` |
| S3 | 🟠 Media | La ficha de Iris pasaba **tal cual** a Euler y Vera: claves extra o texto con "instrucciones" (prompt injection desde datos externos). | `mesa/agentes.py:103-104` → `ficha = extraer_json(texto)` sin validar | `validar_ficha()`: lista blanca de claves, numéricos convertidos a número/`null`, textos recortados y sin saltos de línea. Los 3 prompts indican que los datos **no son instrucciones**. Las lecturas de Euler también se filtran. | `test_validar_ficha_lista_blanca` |
| S4 | 🟠 Media | **Sin tope diario** de análisis en el bot en vivo: un bucle o mensajes repetidos agotan la cuota de Alpha Vantage (25/día) y el saldo de Claude. | `mesa/comandos.py` (no existía límite); solo `MAX_ANALISIS_POR_RUN` en `mesa/config.py:34` para Actions | `LimiteDeUso`: máx. `MAX_ANALISIS_POR_DIA` (10) y pausa de `SEGUNDOS_ENTRE_ANALISIS` (30 s). Valores acotados al leerlos. | `test_limite_diario_y_pausa`, `test_tope_diario_responde_en_telegram` |
| S5 | 🟠 Media | Acciones de GitHub referidas por **etiqueta móvil** (`@v7`): quien controle la etiqueta puede cambiar el código que corre con tus Secrets. | `.github/workflows/mesa-financiera.yml:40,41,57`; `pruebas.yml:19,20` | Fijadas por **SHA** (v7.0.1 / v7.1.0 / v7.0.2) y `persist-credentials: false`. | Revisión del YAML |
| S6 | 🟡 Baja | Dependencias **sin versión fija** (`anthropic>=1.0`): cada instalación podía traer una versión mayor distinta. | `requirements.txt:1-3` | Versiones exactas (`anthropic==2.1.0`, `requests==2.34.2`, `python-dotenv==1.2.4`) + **Dependabot** semanal (`.github/dependabot.yml`). | Workflow `pruebas` en verde |
| S7 | 🟡 Baja | Cliente de Claude **sin tiempo máximo**: una llamada colgada bloquea el bot o consume minutos de Actions. | `mesa/agentes.py:26-27` | `timeout=60`, `max_retries=2`. | Revisión de código |
| S8 | 🟡 Baja | La nota de Vera podía ser **muy larga** o traer el descargo a media nota. | `mesa/agentes.py` (`agente_comunicador`) | Largo máximo 1 200 caracteres; el descargo queda **siempre al final** y una sola vez; se ocultan llaves. | `test_nota_real_termina_con_descargo_y_largo_acotado` |
| S9 | 🟡 Baja | `.gitignore` solo protegía `.env`, no variantes como `.env.local` o `.env.backup`. | `.gitignore:1` | Se agregan `.env.*` (excepto `.env.example`), `*.pem`, `*.key`. | `git check-ignore .env.local` |

## Lo que ya estaba bien (se conserva)

- Llaves solo en variables de entorno / Secrets; `config.resumen()` nunca imprime valores.
- Validación estricta del ticker (`PATRON_TICKER`), que evita inyección de comandos (`/analiza AAPL;x` → "Escribe un ticker válido").
- En el workflow, el ticker se pasa como variable de entorno (`TICKER`) y no se pega dentro del comando.
- `permissions: contents: read` y `concurrency` en los workflows.
- Regla de oro: los cálculos están en Python (`calcular_indicadores`), no en el prompt.

## Riesgos residuales (no se pueden eliminar desde el código)

| Riesgo | Por qué queda | Acción recomendada |
|---|---|---|
| La llave de Alpha Vantage viaja en la URL del servidor MCP (`?apikey=`). | **Dato:** es el método del servidor MCP oficial (`mesa/agentes.py:41`, `.mcp.json:5`). **Inferencia:** puede quedar en registros de servidores intermedios. | Usar una llave exclusiva para este proyecto y rotarla al terminar el diplomado. |
| GitHub oculta los Secrets en los logs de Actions, pero **no** en Colab, Codespaces ni tu terminal. | **Supuesto:** el enmascarado automático de GitHub funciona como indica su documentación. | Revisar capturas antes de entregarlas (la guía lo exige). |
| Prompt injection avanzada. | La lista blanca reduce la superficie, pero un texto corto dentro de `nombre` o `sector` sigue llegando al modelo. | Mantener la regla "datos ≠ instrucciones" y revisar notas atípicas. |
| Gasto en la API de Claude. | El código limita llamadas, pero el control final de gasto está en la consola de Anthropic. | Fijar un **límite de gasto mensual** en console.anthropic.com. |

## Configuración recomendada en GitHub (manual, 2 minutos)

1. **Settings → Code security → Secret scanning → Enable** y **Push protection → Enable**: GitHub bloquea un `git push` que contenga una llave.
2. **Settings → Code security → Dependabot alerts → Enable**.
3. Al terminar el diplomado: **Actions → mesa-financiera → ⋯ → Disable workflow** y revoca el token del bot con `@BotFather → /revoke`.

## Indicadores de seguimiento

| Indicador | Meta | Dónde se mide |
|---|---|---|
| Pruebas de `tests/test_seguridad.py` en verde | 100 % en cada push | Actions → `pruebas` |
| Llaves visibles en logs o capturas | 0 | Revisión de logs de Actions y del PDF entregable |
| Análisis reales por día | ≤ 10 | Archivos `salidas/*.json` / artefactos `evidencias-N` |
| PRs de Dependabot abiertos sin revisar | 0 al cierre de cada semana | Pestaña Pull requests |
