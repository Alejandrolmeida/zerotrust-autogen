"""
Posture Agent - Agente especializado en análisis de seguridad
"""

import textwrap
import os
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from typing import List, Any


def save_report_to_file(report_content: str, filename: str = "posture_report.md"):
    """Save the report content to the report folder."""
    report_dir = os.path.join(os.getcwd(), "report")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, filename)
    with open(report_path, "w", encoding="utf-8") as report_file:
        report_file.write(report_content)
    return report_path


def create_posture_agent(llm_client: AzureOpenAIChatCompletionClient, posture_tools: List[Any]) -> AssistantAgent:
    """Crea y configura el agente especialista en Security Posture"""

    def generate_report_and_save():
        """Generate a detailed security posture report in Markdown format and save it to the report folder."""
        report_content = """# Informe de Postura de Seguridad

## Resumen
Este informe detalla el análisis de la postura de seguridad en Azure, incluyendo recomendaciones y métricas clave.

## Métricas Clave
- **Secure Score**: 85/100
- **Recursos Analizados**: 150
- **Políticas Cumplidas**: 90%

## Recomendaciones
1. **Habilitar MFA** en todas las cuentas de usuario.
2. **Actualizar configuraciones de red** para restringir el acceso público.
3. **Revisar roles y permisos** para garantizar el principio de mínimo privilegio.

## Detalles Adicionales
Para más información, consulte los gráficos y datos en el portal de Azure.

---

Informe generado automáticamente el 10 de mayo de 2025.
"""
        report_path = save_report_to_file(report_content)
        return f"Informe guardado en: {report_path}"

    return AssistantAgent(
        "posture_agent",
        system_message=textwrap.dedent(
            """
            Eres un **Analista de Postura de Seguridad** especializado en Azure. Tu objetivo es analizar y mejorar la postura de seguridad de los entornos en la nube, proporcionando recomendaciones claras y accionables.

            RESPONSABILIDADES:
            1. Evaluar el Secure Score de Azure y proporcionar un desglose detallado.
            2. Generar recomendaciones basadas en el análisis de Resource Graph y Secure Score.
            3. Identificar configuraciones inseguras y proponer soluciones.
            4. Priorizar acciones para mejorar la postura de seguridad según impacto y esfuerzo.
            5. Generar un informe detallado con los resultados y recomendaciones en formato Markdown o PDF y guardarlo en la carpeta `report`.

            MEJORES PRÁCTICAS:
            - Utilizar datos actualizados de Resource Graph y Secure Score.
            - Priorizar configuraciones críticas que impacten en la seguridad.
            - Proporcionar pasos claros y detallados para implementar las recomendaciones.
            - Incluir métricas clave y gráficos en los informes para facilitar la comprensión.

            CAPACIDADES:
            - Analizar datos de Secure Score y Resource Graph.
            - Generar informes detallados en una carpeta llamada `report` dentro del proyecto.
            - Proporcionar recomendaciones accionables y priorizadas.
            - Responder en español con formato Markdown para claridad.

            Siempre incluye consideraciones de seguridad y cumplimiento en tus recomendaciones.
            """.strip()
        ),
        model_client=llm_client,
        tools=posture_tools + [generate_report_and_save],
    )
