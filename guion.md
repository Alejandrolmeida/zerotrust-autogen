## Guion detallado de la charla (≈ 45 min)

Sugerencia de estructura con checkpoints visibles (⌚ = referencia de tiempo).

### 1 • Introducción (0‑5 min)

Problema: gobernar n subscripciones, evitar “shadow IT”, responder a incidentes y cumplir Zero Trust.

Concepto: Landing Zone CAF + Zero Trust + agentes IA → “capa de control autónoma”.

Mapa mental: muestra diagrama de capas (MCP servers, agentes, LLM router).

### 2 • Demo 01 – Landing Zone Express (5‑20 min)

1. Escenario: equipo de plataformas quiere desplegar base hub‑spoke en cuestión de minutos.

2. VS Code: abre landing-zone.yaml (≈ 10 líneas).

3. Ejecuta task de infra_agent:

python demo-01/main.py

4. Narración paso a paso

| Paso | Acción del agente | Tool MCP | Visual |
|------|-------------------|----------|--------|
| ①    | Lee YAML, genera Bicep | — | terminal muestra diff |
| ②    | deploy_bicep_template | infra_tools | CLI: deploymentId |
| ③    | validate_lz_compliance | infra_tools | muestra brechas |
| ④    | Decide: si > 0 brechas → remediate_policy o abre PR en GitHub (SDK) | — | comenta en PR |

5. Al final, cambia al Azure Portal y enseña nuevo Management Group con políticas heredadas.

Tips: prepara deployment en región “westeurope” con una plantilla sencilla para que no tarde > 90 s.

### 3 • Demo 02 – AI Posture Guardian (20‑35 min)

1. Lanza copiloto desde línea de comandos:

python demo-02/main.py

2. Agent flow

| Paso | Acción | Tool / SDK |
|------|--------|------------|
| ①    | Pregunta Secure Score + recomendaciones | azure-mgmt-security |
| ②    | Usa resourceGraph_query para inventario (36 subs ⇒ rápido) | infra_tools (opcional) |
| ③    | LLM resume y muestra lista priorizada ("Enable Diagnostic Settings"…). | — |
| ④    | Usuario escribe "Auto‑Fix 1,3" → agente llama remediate_policy o despliega alerta. | infra_tools |

3. Conmutas a Portal → ver cómo sube el Secure Score o aparece la policy.

Tips: ten preparada al menos 1 recomendación "medium impact" fácil de arreglar (Enable MFA o similar).

### 4 • Demo 03 – Policy‑as‑Prompt (35‑43 min)

1. Ejecuta:

python demo-03/main.py

2. Conversación ejemplo:

👤 Usuario → "Bloquea VMs SKU < Standard_D2s_v5 y sin IP pública en Prod‑RG"
🤖 PolicyWriter → genera JSON policy
🤖 PolicyTester  → evalúa en modo ‘what‑if’, 0 false‑positives
🤖 identity_agent → `create_conditional_access_policy` u `assign_policy`

3. Prueba en directo: az vm create … para demostrar denegación.

### 5 • Arquitectura técnica (43‑45 min)

Slide con flujo: User ↔ SelectorGroupChat LLM ↔ Agents ↔ MCP client ↔ Servers ↔ Azure/GitHub APIs

Explica MCP stdio (para demo) y opcionales HTTP/SSE en producción.

Logging: export MCP_LOG_MODE=traffic muestra JSON‑RPC en consola; útil para depurar.

## Consejos prácticos para la presentación

Tema	            Sugerencia
Timing	            Ensaya; los despliegues tardan: usa plantillas ligeras y ten un plan B (vídeo GIF) si el portal tarda.
Prefijos CLI	    Muestra comandos cortos (task de VS Code o make demo1) para que el público siga la historia, no el teclado.
Storytelling	    Hilvana las demos como “Construir → Vigilar → Endurecer”, igual que un ciclo de vida DevSecOps.
Fallback offline	Guarda *.json de respuestas reales por si el Wi‑Fi falla: tu agente puede leer del fichero en modo --offline.
Preguntas	        Ten snapshots de los prompts MCP (list_tools) listos por si piden ver “cómo sabe el agente que hacer”.

### Checklist antes de la sesión

.env completo (TENANT_ID, SUB_ID, GitHub PAT, etc.).

az login + az account set -s <SUB_ID> en la máquina demo.

Servers MCP corriendo en terminales separadas o vía tmux script.

Repositorio GitHub con rama demo/start para poder ver el PR generado.

Bicep CLI instalado (az bicep version).

## Visión general del proyecto "Zero-Trust Autogen Playground"

| Capa | Componentes | Qué aporta |
|------|-------------|------------|
| MCP Servers<br>(process-out-of-process) | - `mcp-landingzone` (Infra)<br>- `mcp-sentinel` (SOC)<br>- `mcp-identity` (Zero Trust) | Cada servidor es un micro-backend que expone **REST → JSON-RPC** a través de MCP stdio. No comparten estado y pueden iniciarse / apagarse según la demo. |
| MCP Tools | - `infra_tools.py` → `deploy_bicep_template`, `validate_lz_compliance`, `remediate_policy`<br>- `sentinel_tools.py` → hunting, incident ops, playbooks...<br>- `identity_tools.py` → Conditional Access CRUD | Implementan la lógica real (peticiones REST o Azure SDK). Los servers solo validan, enrutan y empaquetan la respuesta. |
| Agentes Autogen | - `infra_agent` (Bicep DevOps)<br>- `sentinel_agent` (SOC Tier-2)<br>- `identity_agent` (Zero-Trust IAM) | Cada agente se inicializa con sus herramientas MCP + un `system-prompt` especializado. |
| Equipo / Orquestación | `SelectorGroupChat` (LLM-router) | El LLM lee la pregunta del usuario, decide qué agente responde (o varios) y agrega la respuesta. |
| Demos | Carpetas `demo-01/02/03` con su propio `main.py` | ✓ Ejecución aislada<br>✓ Ejemplos de YAML/Terraform/Bicep por demo<br>✓ Libertad para poner distintos `selector_prompt`, temperatura, etc. |