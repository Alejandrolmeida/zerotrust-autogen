![Global Azure 2025 - Securizando Azure con AI Foundry y Zero Trust](resources/Global%20Azure%202025%20-%20Securizando%20Azure%20con%20AI%20Foundry%20y%20Zero%20Trust.png)

# Landing Zone Express

**Landing Zone Express** es una solución multi-agente diseñada para simplificar y automatizar el despliegue de infraestructuras empresariales en Azure, aplicando principios de Zero Trust. Esta herramienta combina la potencia de Bicep, Azure CLI y agentes generativos basados en OpenAI para garantizar un entorno seguro, escalable y fácil de gestionar.

> Demo oficial para la sesión **"Securizando Azure con AI Foundry y Zero Trust"** – Global Azure 2025 (Madrid) por **Alejandro Almeida, Microsoft MVP Azure & AI**.

---

## Índice

- [Descripción](#landing-zone-express)
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

1. **Despliegue automatizado**: Implementación de Azure Landing Zones empresariales utilizando Bicep y Azure CLI.
2. **Seguridad Zero Trust**: Aplicación de controles como RBAC mínimo, políticas *deny-by-default*, NSG/UDR, JIT y uso de identidades administradas.
3. **Supervisión avanzada**: Generación de informes de postura de seguridad y creación automática de incidencias en GitHub para hallazgos críticos.
4. **Escalabilidad y modularidad**: Uso de módulos Bicep para facilitar la personalización y el mantenimiento de la infraestructura.

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
                   │            └─────┬──────┘ │             │
          ┌────────▼─────────┐        │        │    ┌────────▼─────────┐
          │ Azure Resources  │◀──-────┘        └-──▶│  Markdown Report │
          │  (Landing Zone)  │                      │  + GitHub Issue  │
          └──────────────────┘                      └──────────────────┘
```

Cada agente hereda de **`autogen.agentchat`** y opera con el principio de mínimo privilegio. El equipo colaborativo (Magentic-One) divide la tarea en subtareas y sincroniza resultados de forma asíncrona.

## Requisitos

- **Python ≥ 3.11**: Compatibilidad con asyncio nativo.
- **Azure CLI v2**: Configurado y autenticado (`az login`).
- **Bicep ≥ 0.25**: Para la gestión de plantillas de infraestructura como código.
- **Cuenta OpenAI o Azure OpenAI**: Recomendado el modelo *gpt-4o*.
- **Herramientas opcionales**: `make`, `direnv`, `pre-commit`, `playwright` (para WebSurfer).

> **Nota:** Solo necesitas **Entra ID Basic**. Los controles Zero Trust se implementan con políticas y RBAC.

## Instalación rápida

```bash
git clone https://github.com/your-org/landing-zone-express.git
cd landing-zone-express
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configuración de variables de entorno
export OPENAI_API_KEY=sk-...
export AZURE_SUBSCRIPTION_ID=<tu-sub>
```

## Uso de la CLI

```bash
# Desplegar una Landing Zone en el entorno de producción
python main.py deploy --env prod

# Realizar una auditoría rápida de un Resource Group
python main.py audit --rg my-landingzone-rg --verbose
```

> ⚡ **Tip:** Usa `--dry-run` para simular la ejecución sin realizar cambios.

## Configuración

| Variable                  | Descripción                                             |
|---------------------------|---------------------------------------------------------|
| `OPENAI_API_KEY`          | Clave OpenAI o Azure OpenAI.                            |
| `AZURE_SUBSCRIPTION_ID`   | ID de la suscripción donde se desplegará la Landing Zone.|
| `LZE_OPENAI_MODEL`        | (Opc.) Modelo a usar. Por defecto `gpt-4o`.            |
| `LZE_REPORT_PATH`         | (Opc.) Carpeta donde guardar los informes Markdown.     |

Configura valores persistentes con [direnv](https://direnv.net/) o añade un fichero `.env`.

## Flujo de demo

1. **Despliegue**: Ejecuta `deploy` para crear la infraestructura básica (hub/spoke, NSG, GW, etc.).
2. **Aplicación de políticas**: **PolicyAgent** aplica políticas Zero Trust y RBAC mínimo.
3. **Supervisión**: **MonitorAgent** escanea la postura de seguridad, genera un informe Markdown y crea una *issue* en GitHub si encuentra hallazgos críticos.
4. **Revisión**: Visualiza el informe en VS Code y revisa las incidencias creadas.

## Estructura del repositorio

```text
landing-zone-express/
├── main.py            # CLI principal
├── agents/            # Orquestador y agentes especializados
├── tools/             # Herramientas auxiliares
├── infra/             # Plantillas Bicep, scripts y módulos
│   ├── main.bicep
│   ├── main.parameters.json
│   ├── deploy_landing_zone.sh
│   └── modules/
├── reports/           # Informes generados (excluidos del control de versiones)
├── tests/             # Pruebas automatizadas con pytest
└── README.md          # Este archivo
```

## Pruebas

```bash
pytest -s -q
```

Las pruebas se ejecutan con `mock_openai=True` para evitar llamadas reales y validan la creación de recursos como grupos de recursos, políticas y configuraciones de NSG.

## Contribuir

¡Se aceptan *pull requests*! Por favor:

1. Crea una rama desde `main`.
2. Asegúrate de que las herramientas de linting (`ruff`, `flake8`) pasen sin errores.
3. Verifica que todas las pruebas (`pytest`) sean exitosas.

## Licencia

Distribuido bajo licencia **MIT**. Consulta `LICENSE` para más detalles.

---

> *Inspirado por Microsoft Cloud Adoption Framework, Magentic-One y el espíritu de Global Azure.*
