/home/almeida/source/github/alejandrolmeida/zerotrust-autogen/Infra/deploy_landing_zone.shanding-zone-rg"
LOCATION="westeurope"

# Crear grupo de recursos
az group create --name $RESOURCE_GROUP --location $LOCATION

# Desplegar plantillas Bicep
az deployment group create   --resource-group $RESOURCE_GROUP   --template-file main.bicep   --parameters @main.parameters.json
