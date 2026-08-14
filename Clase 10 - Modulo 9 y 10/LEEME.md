# Módulos 9 y 10 — Comité de Selección Gobernado

El comité de selección de la Clase 7 (un Manager que orquesta dos workers especialistas)
reconstruido desde cero con la capa de gobernanza del **Módulo 9** y la lógica de
despliegue por fases del **Módulo 10**.

La arquitectura agéntica no cambió. Lo que se agregó es todo lo que hace falta para
poder ponerlo en producción y hacerse cargo.

## Los cuatro workflows

| Workflow | ID | Nodos |
|---|---|---|
| `[Modulos 9-10] - Comite de Seleccion Gobernado (Manager)` | `FEhMimdfkSdQqpDZ` | 34 + 9 notas |
| `[Modulos 9-10] - Worker - Cribado de Elegibilidad` | `cc1da6FBuh76ROY3` | 5 + 3 notas |
| `[Modulos 9-10] - Worker - Scorecard de Match` | `w8tc4rPcwdvO1hvk` | 5 + 3 notas |
| `[Modulos 9-10] - Tablero de KPIs, TCO y ROI` | `OZzdgfhRXrCKKVtI` | 4 + 3 notas |

**Data Table:** `M9-10 - Log de Auditoria Agentica` — ID `gdN7CzQWjLkNjAkw`, 28 columnas.
Es nativa de n8n: no necesita credenciales ni planillas externas.

Los cuatro validan con `n8n_validate_workflow` (perfil runtime, 0 errores).

## Qué agrega cada bloque

| Bloque del Manager | Qué resuelve | Módulo |
|---|---|---|
| `Gobernanza: abrir traza` | `trace_id` único propagado a los dos sub-workflows | M9 · lectura 3 |
| `Minimizacion: enmascarar PII` | el nombre, el mail y el teléfono nunca llegan al modelo | M9 · lectura 1 |
| `Guardia de prompt injection` | seis patrones que frenan un CV con instrucciones | M9 · lectura 1 |
| `Gasto del dia` + `Burn rate` | corta si el gasto del día superó el presupuesto, por entorno | M9 · lectura 2 |
| `Instrumentacion y fila de auditoria` | tokens, costo, escenario y latencia por ejecución | M9 · lecturas 2 y 3 |
| `Registrar en el log de auditoria` | una fila JSON de 28 campos por ejecución | M9 · lectura 3 |
| `Nivel de autonomia` | las cuatro fases del despliegue en un solo Switch | M10 · lectura 3 |
| `Resumen ejecutivo` | la salida traducida a lenguaje de negocio | M10 · lectura 2 |
| Tablero | KPIs, matriz de TCO, ROI y payback | M9 · dim. 1 y M10 |

## Estado (13/08/2026) — corriendo end-to-end

El sistema completo se ejecutó y quedó verificado. Dos corridas reales:

| Caso | Resultado | Escenario | Costo | Tiempo |
|---|---|---|---|---|
| Martina Ochoa (fase 3) | VERDE · 94/100 · confianza 0,88 | `standard_loop` (2 inferencias) | 0,004182 USD | 57 s |
| Sofía Rinaldi (fase 0) | NO_ELEGIBLE | `cold_run` (1 inferencia) | 0,000937 USD | 22 s |

Las dos filas están en la Data Table con su `trace_id`, su razonamiento citando textualmente
el CV y el detalle de la PII enmascarada. **El cribado cortando antes del paso caro se paga
solo: 4,5 veces más barato.**

**La aprobación humana pasó de correo a Telegram** (13/08). Los tres nodos de Gmail se
reemplazaron por Telegram y el par `Wait` + `Switch` desapareció: la operación
**Send and Wait for Response** manda el mensaje con dos botones y espera la respuesta en
un solo nodo. Además de ser más simple, evita el trámite de OAuth que tenía la credencial
de Gmail rota.

**Para que corra hacen falta tres pasos de tu lado:**

1. Crear un bot con **@BotFather** (`/newbot`) y guardar el token.
2. En n8n › Credentials, crear una credencial **Telegram account** con ese token y
   asignarla a los tres nodos de Telegram del Manager.
3. Escribirle algo al bot y sacar el chat id de
   `https://api.telegram.org/bot<TOKEN>/getUpdates` (o con @userinfobot). Reemplazar
   `REEMPLAZAR_CHAT_ID` en el nodo **Gobernanza: abrir traza**.

Después, activar el workflow: la espera por respuesta solo funciona con el workflow activo.
Quedó desactivado porque n8n no publica nodos sin credencial.

Pendiente menor: los precios por millón de tokens del nodo de traza son **valores de
ejemplo**, hay que poner los vigentes del proveedor.

## Dos cosas que la primera corrida real cambió

**Estrategia de fallback en los nodos de correo.** El fallo de Gmail tumbaba toda la
ejecución *después* de que la decisión ya estuviera tomada y registrada. Los tres nodos de
correo ahora tienen `onError: continueRegularOutput`: si el canal de aviso falla, el flujo
sigue y responde igual. Es exactamente lo que el Módulo 10 pide declarar en la oferta
técnica —qué pasa cuando algo se cae— y acá se ve por qué importa.

**El log escrito antes de ramificar demostró su valor.** En la corrida que falló por Gmail,
la evaluación completa ya estaba guardada en la tabla. Si el log estuviera al final, esa
ejecución no habría dejado rastro: justo el caso que hay que poder auditar.

## Una trampa de n8n que este ejercicio destapó

En un nodo **Set en modo raw**, `={{ { ...$json, "campo": 1 } }}` **falla en tiempo de
ejecución** con *"Cannot convert undefined or null to object"*, aunque la validación no
marque nada: `$json` es un Proxy que no soporta el spread. Hay que escribir
`{ ...$input.item.json, ... }` o `Object.assign({}, $json, { ... })`.

En los nodos **Code** no pasa: ahí `$input.first().json` es un objeto plano y el spread
funciona sin problema.

## Cómo probarlo

```bash
python3 "Probar el comite.py"          # los 4 casos de prueba
python3 "Probar el comite.py" fases    # el mismo candidato en las 4 fases de despliegue
```

El segundo comando es la demostración central: **el mismo workflow se comporta de cuatro
maneras distintas sin tocar un nodo**, según el campo `fase_despliegue` del POST.

## Los dos documentos

- `PreEntrega Modulo 9 - de que trata.pdf` — las tres dimensiones, el formato exacto del
  entregable, la rúbrica con su errata, los cinco errores que hacen perder puntos y el mapeo
  de cada requisito al nodo que lo produce.
- `PreEntrega Modulo 10 - de que trata.pdf` — la advertencia sobre el enunciado mal copiado,
  los cuatro criterios que sí se corrigen, la estructura del brochure página por página, el
  pricing híbrido y cómo defenderlo ante el comité.

## Si se importa en otra instancia de n8n

Los JSON traen los IDs reales de esta instancia. Al importarlos en otra hay que actualizar:

- En el Manager: el `workflowId` de los dos nodos `Worker:` y el `dataTableId` de los tres
  nodos de Data Table (dos en el Manager, uno en el Tablero).
- Las credenciales de OpenAI y Gmail.
