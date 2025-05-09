# Landing Zone Express

**Solución multi-agente Magentic-One para desplegar y securizar Enterprise Landing Zones en Azure aplicando Zero Trust – sin Entra ID Premium.**

![Global Azure Madrid](https://globalazure.es/assets/images/logo-ga.svg)

> Demo oficial para la sesión **"Securizando Azure con AI Foundry y Zero Trust"** – Global Azure 2025 (Madrid) por **Alejandro Almeida, Microsoft MVP Azure & AI**.

---

## Índice

- [Objetivos](#objetivos)
- [Arquitectura](#arquitectura)
- [Requisitos](#requisitos)
- [Instalación rápida](#instalación-rápida)
- [Uso de la CLI](#uso-de-la-cli)
- [Configuración](#configuración)
- [Flujo de demo](#flujo-de-demo)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Pruebas](#pruebas)
- [Contribuir](#contribuir)
- [Licencia](#licencia)

---

## Objetivos

1. **Despliegue automatizado** de una Azure Landing Zone empresarial con Bicep y Azure CLI.
2. **Aplicación de controles Zero Trust** (RBAC mínimo, políticas *deny-by-default*, NSG/UDR, JIT, identidades administradas) sin necesidad de licencias Entra ID P1/P2.
3. **Supervisión proactiva** de la postura de seguridad con agentes generativos basados en OpenAI y Magentic-One.
4. **Generación de informes** Markdown y creación de incidencias en GitHub con recomendaciones de remediación.

## Arquitectura

```ascii
                              ┌─────────────────────────────┐
                              │       OrchestratorAgent     │
                              │ (MagenticOneGroupChat team) │
                              └───────┬────────┬────────────┘
                       deploy task    │        │   monitor task
                                      │        │
          ┌──────────────────┐  ┌────────────┐ │  ┌───────────────────┐
          │  DeployAgent     │  │ PolicyAgent│ │  │  MonitorAgent     │
          │  (Bicep/CLI)     │  │ (Policy &  │ │  │ (Azure Monitor)   │
          └────────┬─────────┘  │  RBAC)     │ │  └──────────┬────────┘
                   │            └───┬────────┘ │             │
          ┌────────▼─────────┐      │          │    ┌────────▼─────────┐
          │ Azure Resources  │◀────┘           └──▶│  Markdown Report │
          │  (Landing Zone)  │                      │  + GitHub Issue  │
          └──────────────────┘                      └──────────────────┘
```

Cada agente hereda de **`autogen.agentchat`** y opera con el principio de mínimo privilegio. El equipo colaborativo (Magentic-One) divide la tarea en subtareas y sincroniza resultados de forma asíncrona.

## Requisitos

- **Python ≥ 3.11** (asyncio nativo)
- **Azure CLI v2** configurado y autenticado (`az login`)
- **Bicep ≥ 0.25**
- Cuenta de **OpenAI** o Azure OpenAI (modelo *gpt-4o* recomendado)
- Herramientas opcionales: `make`, `direnv`, `pre-commit`, `playwright` (para WebSurfer)

> **Nota:** Solo necesitas **Entra ID Basic**. Los controles Zero Trust se implementan con políticas y RBAC.

## Instalación rápida

```bash
git clone https://github.com/your-org/landing-zone-express.git
cd landing-zone-express
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Variables de entorno mínimas
export OPENAI_API_KEY=sk-...
export AZURE_SUBSCRIPTION_ID=<tu-sub>
```

## Uso de la CLI

```bash
# Desplegar Landing Zone en la suscripción por defecto
python main.py deploy --env prod

# Auditoría rápida de un Resource Group
python main.py audit --rg my-landingzone-rg --verbose
```

> ⚡ **Tip:** Añade `--dry-run` para simular la ejecución sin cambios.

## Configuración

| Variable                  | Descripción                                             |
|---------------------------|---------------------------------------------------------|
| `OPENAI_API_KEY`          | Clave OpenAI o Azure OpenAI.                            |
| `AZURE_SUBSCRIPTION_ID`   | ID de la suscripción donde se desplegará la Landing Zone.|
| `LZE_OPENAI_MODEL`        | (Opc.) Modelo a usar. Por defecto `gpt-4o`.            |
| `LZE_REPORT_PATH`         | (Opc.) Carpeta donde guardar los informes Markdown.     |

Configura valores persistentes con [direnv](https://direnv.net/) o añade un fichero `.env`.

## Flujo de demo

1. Ejecuta **`deploy`** para crear la infraestructura básica (hub/spoke, NSG, GW, etc.).
2. **PolicyAgent** aplica políticas Zero Trust y RBAC mínimo.
3. **MonitorAgent** escanea la postura de seguridad, genera un informe Markdown y, si encuentra hallazgos de *high severity*, crea una *issue* en GitHub.
4. Muestra el informe en VS Code y revisa la *issue* creada.

## Estructura del repositorio

```text
landing-zone-express/
├── main.py            # CLI
├── agents/            # Orchestrator + agentes
├── infra/             # Plantillas Bicep + políticas
├── reports/           # Informes generados (git-ignored)
├── tests/             # Pytest-asyncio
└── README.md          # Este archivo
```

## Pruebas

```bash
pytest -s -q
```

Las pruebas se ejecutan con `mock_openai=True` para evitar llamadas reales y validan la creación de RG, políticas y valores NSG.

## Contribuir

¡Se aceptan *pull requests*! Por favor:

1. Crea una rama desde `main`.
2. Asegúrate de que `ruff` y `flake8` pasen.
3. Confirma que `pytest` sea exitoso.

## Licencia

Distribuido bajo licencia **MIT**. Consulta `LICENSE` para más detalles.

---

> *Inspired by Microsoft Cloud Adoption Framework, Magentic-One, and the spirit of Global Azure.*
