az group create --name transport-projects --location eastus

az acr create --resource-group transport-projects --name saadiqm --sku Basic

az acr login --name saadiqm --expose-token

sudo az acr login --name saadiqm

sudo docker compose push

sudo docker context use myacicontext

sudo docker compose -f docker-compose.yml up


