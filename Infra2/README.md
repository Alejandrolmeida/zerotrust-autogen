# Azure Landing Zones con Bicep

Este directorio contiene las plantillas Bicep para implementar Azure Landing Zones siguiendo un enfoque Zero-Trust.

## Estructura

- `main.bicep`: Plantilla principal que orquesta todos los módulos
- `main.parameters.json`: Archivo de parámetros para personalizar el despliegue
- `modules/`: Directorio con módulos especializados
  - `networking.bicep`: Recursos de red (VNet, subnets, NSGs, etc)
  - `security.bicep`: Recursos de seguridad (Key Vault, Log Analytics, etc)
  - `governance.bicep`: Recursos de gobernanza (RBAC, políticas, etc)

## Componentes de Landing Zone

Una Landing Zone típica incluye:

1. **Networking**: Redes virtuales segmentadas con zonas DMZ, subredes para aplicaciones, bases de datos y servicios compartidos
2. **Security**: Log Analytics, Key Vault, Microsoft Defender for Cloud
3. **Governance**: Políticas de Azure, etiquetado, control de acceso RBAC
4. **Monitoring**: Alertas, diagnóstico y visibilidad

## Despliegue

Para desplegar la landing zone:

```bash
./deploy.sh
```

Para ver los cambios sin aplicarlos:

```bash
./deploy.sh --what-if
```

## Personalización

Edita el archivo `main.parameters.json` para adaptar los valores a tu entorno.

## Zero-Trust

Las plantillas implementan prácticas Zero-Trust como:

- Segmentación de red
- Comunicación cifrada con Private Link
- Control de acceso basado en identidad
- Monitorización continua
- Políticas de cumplimiento
