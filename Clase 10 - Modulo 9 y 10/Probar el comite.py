#!/usr/bin/env python3
"""
Dispara los casos de prueba contra el Comite de Seleccion Gobernado.

    python3 "Probar el comite.py"                 # los 4 casos
    python3 "Probar el comite.py" 1               # solo el caso 1
    python3 "Probar el comite.py" fases           # el caso 1 en las 4 fases de despliegue

Antes de correrlo: el workflow "[Modulos 9-10] - Comite de Seleccion Gobernado (Manager)"
tiene que estar ACTIVO, con la credencial de Gmail asignada y el email del equipo puesto.

Ojo con las corridas que caen en aprobacion humana: la respuesta llega enseguida
("EN_REVISION_HUMANA") pero la ejecucion queda esperando hasta 24 h a que alguien
abra uno de los links del mail. Recien ahi se escribe la segunda fila del log.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

URL = os.environ.get("COMITE_WEBHOOK",
                     "https://n8n.wellesoftware.com/webhook-test/comite-gobernado")
PAUSA = 2
TIMEOUT = 180

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(AQUI, "Casos de prueba.json"), encoding="utf-8"))
CASOS = [{k: v for k, v in c.items() if not k.startswith("_")} for c in DATA["casos"]]
NOMBRES = [c["_nombre"] for c in DATA["casos"]]


def enviar(cuerpo):
    req = urllib.request.Request(
        URL,
        data=json.dumps(cuerpo, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}", "_detalle": e.read().decode("utf-8", "replace")[:300]}
    except Exception as e:                                    # noqa: BLE001
        return {"_error": type(e).__name__, "_detalle": str(e)[:300]}


def mostrar(etiqueta, r):
    if "_error" in r:
        print(f"  {etiqueta}: FALLO {r['_error']} - {r['_detalle']}")
        return
    if r.get("estado") == "EN_REVISION_HUMANA":
        print(f"  {etiqueta}: EN REVISION HUMANA - propuesto {r.get('resultado_propuesto')} "
              f"- traza {r.get('trace_id')}")
        return
    print(f"  {etiqueta}: {r.get('resultado')} | decidio: {r.get('quien_decidio')} | "
          f"{r.get('costo_de_esta_evaluacion_usd')} USD | {r.get('tiempo_de_respuesta_seg')} s")
    print(f"     privacidad: {r.get('privacidad')}")
    print(f"     accion: {r.get('accion_tomada')}")


def main():
    arg = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
    print(f"Webhook: {URL}\n")

    if arg == "fases":
        print("Mismo candidato, cuatro fases de despliegue. Un solo campo cambia.\n")
        for fase in (0, 1, 2, 3):
            cuerpo = dict(CASOS[0], fase_despliegue=fase,
                          candidato_id=f"{CASOS[0]['candidato_id']}-F{fase}")
            print(f"Fase {fase}")
            mostrar(f"fase {fase}", enviar(cuerpo))
            time.sleep(PAUSA)
        return

    indices = [int(arg) - 1] if arg.isdigit() else range(len(CASOS))
    for i in indices:
        print(NOMBRES[i])
        mostrar("resultado", enviar(CASOS[i]))
        print()
        time.sleep(PAUSA)

    print("El detalle completo de cada corrida esta en la Data Table")
    print("'M9-10 - Log de Auditoria Agentica'. Buscala por trace_id.")


if __name__ == "__main__":
    main()
