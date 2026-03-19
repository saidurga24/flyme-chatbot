#!/bin/bash
# Azure resource management for FlyMe chatbot
# Usage: ./azure_manage.sh [create|deploy|start|stop|status|delete|train]

set -e

# ---- Configuration ----
RESOURCE_GROUP="flyme-rg"
LOCATION="eastus"
APP_NAME="flyme-chatbot"
LANGUAGE_NAME="flyme-language"
APPINSIGHTS_NAME="flyme-appinsights"
BOT_NAME="flyme-bot"
SKU="F0"  # Free tier
PYTHON_RUNTIME="PYTHON:3.11"
CLU_PROJECT="FlyMe-FlightBooking"
CLU_DEPLOYMENT="production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if az CLI is installed and logged in
check_az() {
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI not installed. Install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
    if ! az account show &> /dev/null; then
        log_warn "Not logged in. Running 'az login'..."
        az login
    fi
    log_info "Logged in as: $(az account show --query user.name -o tsv)"
    log_info "Subscription: $(az account show --query name -o tsv)"
}

# ---- CREATE all resources ----
create() {
    check_az
    log_info "Creating all Azure resources..."

    # Resource group
    log_info "Creating resource group: $RESOURCE_GROUP"
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION" -o none

    # Language service (for CLU)
    log_info "Creating Language service: $LANGUAGE_NAME"
    az cognitiveservices account create \
        --name "$LANGUAGE_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --kind "TextAnalytics" \
        --sku "$SKU" \
        --location "$LOCATION" \
        --yes -o none

    CLU_KEY=$(az cognitiveservices account keys list \
        --name "$LANGUAGE_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "key1" -o tsv)
    CLU_ENDPOINT=$(az cognitiveservices account show \
        --name "$LANGUAGE_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.endpoint" -o tsv)
    log_info "CLU Endpoint: $CLU_ENDPOINT"

    # Application Insights
    log_info "Creating Application Insights: $APPINSIGHTS_NAME"
    az monitor app-insights component create \
        --app "$APPINSIGHTS_NAME" \
        --location "$LOCATION" \
        --resource-group "$RESOURCE_GROUP" \
        --kind web \
        --application-type web -o none

    APPINSIGHTS_KEY=$(az monitor app-insights component show \
        --app "$APPINSIGHTS_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "instrumentationKey" -o tsv)
    APPINSIGHTS_CONN=$(az monitor app-insights component show \
        --app "$APPINSIGHTS_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "connectionString" -o tsv)

    # Web App (App Service)
    log_info "Creating App Service Plan + Web App: $APP_NAME"
    az appservice plan create \
        --name "${APP_NAME}-plan" \
        --resource-group "$RESOURCE_GROUP" \
        --sku B1 \
        --is-linux -o none 2>/dev/null || {
        log_warn "B1 Linux plan failed (quota limit). Trying F1 Free tier..."
        az appservice plan create \
            --name "${APP_NAME}-plan" \
            --resource-group "$RESOURCE_GROUP" \
            --sku F1 -o none
    }

    az webapp create \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --plan "${APP_NAME}-plan" \
        --runtime "$PYTHON_RUNTIME" -o none

    # Set environment variables on the web app
    log_info "Configuring app settings..."
    az webapp config appsettings set \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --settings \
            CluProjectName="$CLU_PROJECT" \
            CluDeploymentName="$CLU_DEPLOYMENT" \
            CluAPIKey="$CLU_KEY" \
            CluEndpoint="$CLU_ENDPOINT" \
            AppInsightsInstrumentationKey="$APPINSIGHTS_KEY" \
            AppInsightsConnectionString="$APPINSIGHTS_CONN" \
            SCM_DO_BUILD_DURING_DEPLOYMENT=true \
            PORT=8000 \
        -o none

    # Set startup command
    az webapp config set \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --startup-file "P10_01_chatbot/startup.sh" -o none

    # Write .env file locally
    log_info "Writing local .env file..."
    cat > P10_01_chatbot/.env <<EOF
MicrosoftAppId=
MicrosoftAppPassword=

CluProjectName=$CLU_PROJECT
CluDeploymentName=$CLU_DEPLOYMENT
CluAPIKey=$CLU_KEY
CluEndpoint=$CLU_ENDPOINT

AppInsightsInstrumentationKey=$APPINSIGHTS_KEY
AppInsightsConnectionString=$APPINSIGHTS_CONN

PORT=3978
EOF

    echo ""
    log_info "All resources created!"
    echo ""
    echo "  Resource Group:    $RESOURCE_GROUP"
    echo "  Language Service:  $LANGUAGE_NAME"
    echo "  CLU Endpoint:      $CLU_ENDPOINT"
    echo "  App Insights:      $APPINSIGHTS_NAME"
    echo "  Web App:           https://${APP_NAME}.azurewebsites.net"
    echo ""
    echo "  .env updated with real credentials."
    echo ""
    echo "  Next steps:"
    echo "    ./azure_manage.sh train    # train the CLU model"
    echo "    ./azure_manage.sh deploy   # deploy the chatbot"
}

# ---- TRAIN the CLU model ----
train() {
    check_az
    log_info "Training CLU model..."

    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    VENV="$SCRIPT_DIR/.venv/bin/python"

    if [ ! -f "$VENV" ]; then
        log_error "Virtual environment not found at $SCRIPT_DIR/.venv"
        log_info "Create it: python3 -m venv .venv && pip install -r P10_01_chatbot/requirements.txt"
        exit 1
    fi

    # Prepare training data from Frames
    log_info "Preparing training data from Frames dataset..."
    $VENV "$SCRIPT_DIR/P10_04_scripts/training/prepare_training_data.py"

    # Train and deploy CLU model
    log_info "Training and deploying CLU model..."
    $VENV "$SCRIPT_DIR/P10_04_scripts/training/train_clu_model.py"

    # Evaluate
    log_info "Evaluating model..."
    $VENV "$SCRIPT_DIR/P10_04_scripts/training/evaluate_model.py"

    log_info "Training complete!"
}

# ---- DEPLOY the app ----
deploy() {
    check_az
    log_info "Deploying to Azure Web App: $APP_NAME"

    # Deploy from the project root
    cd "$(dirname "$0")"

    az webapp up \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --runtime "$PYTHON_RUNTIME"

    log_info "Deployed! App URL: https://${APP_NAME}.azurewebsites.net"
}

# ---- START the web app ----
start() {
    check_az
    log_info "Starting web app: $APP_NAME"
    az webapp start --name "$APP_NAME" --resource-group "$RESOURCE_GROUP"
    log_info "Started. URL: https://${APP_NAME}.azurewebsites.net"
}

# ---- STOP the web app ----
stop() {
    check_az
    log_info "Stopping web app: $APP_NAME"
    az webapp stop --name "$APP_NAME" --resource-group "$RESOURCE_GROUP"
    log_info "Stopped."
}

# ---- STATUS of all resources ----
status() {
    check_az
    echo ""
    log_info "Resource Group: $RESOURCE_GROUP"
    echo ""

    # Web app status
    echo "--- Web App ---"
    az webapp show \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "{name:name, state:state, url:defaultHostName}" \
        -o table 2>/dev/null || echo "  Not found"

    echo ""
    echo "--- Language Service ---"
    az cognitiveservices account show \
        --name "$LANGUAGE_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "{name:name, endpoint:properties.endpoint, sku:sku.name}" \
        -o table 2>/dev/null || echo "  Not found"

    echo ""
    echo "--- Application Insights ---"
    az monitor app-insights component show \
        --app "$APPINSIGHTS_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "{name:name, instrumentationKey:instrumentationKey}" \
        -o table 2>/dev/null || echo "  Not found"

    echo ""

    # Show logs if app is running
    log_info "Recent logs:"
    az webapp log tail \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --lines 10 2>/dev/null || echo "  No logs available"
}

# ---- DELETE everything ----
delete() {
    check_az
    log_warn "This will delete ALL resources in resource group: $RESOURCE_GROUP"
    read -p "Are you sure? (y/N): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        log_info "Cancelled."
        exit 0
    fi

    log_info "Deleting resource group: $RESOURCE_GROUP (this takes a few minutes)..."
    az group delete --name "$RESOURCE_GROUP" --yes --no-wait
    log_info "Deletion started. Resources will be removed in the background."
}

# ---- LOGS ----
logs() {
    check_az
    log_info "Streaming logs from $APP_NAME..."
    az webapp log tail \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP"
}

# ---- Main ----
case "${1:-}" in
    create)  create ;;
    train)   train ;;
    deploy)  deploy ;;
    start)   start ;;
    stop)    stop ;;
    status)  status ;;
    delete)  delete ;;
    logs)    logs ;;
    *)
        echo "FlyMe Chatbot - Azure Management"
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  create   Create all Azure resources (Language, App Insights, Web App)"
        echo "  train    Prepare data + train + evaluate the CLU model"
        echo "  deploy   Deploy the chatbot to Azure Web App"
        echo "  start    Start the web app"
        echo "  stop     Stop the web app"
        echo "  status   Show status of all resources"
        echo "  logs     Stream live logs from the web app"
        echo "  delete   Delete all resources (asks for confirmation)"
        ;;
esac
