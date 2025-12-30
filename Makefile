# Satisfactory Server Management
# Usage: make <target>
# Run `make help` for available commands

.PHONY: help start stop restart logs status backup update mods-install mods-manual \
        setup validate-env shell clean network-verify

# Default target
.DEFAULT_GOAL := help

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
CYAN := \033[0;36m
NC := \033[0m

# Variables
COMPOSE := docker compose
SCRIPTS := ./scripts/main.sh

#==============================================================================
# Help
#==============================================================================

help: ## Show this help message
	@echo ""
	@echo "$(BLUE)Satisfactory Server Management$(NC)"
	@echo ""
	@echo "$(GREEN)Usage:$(NC) make <target>"
	@echo ""
	@echo "$(YELLOW)Server Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quick Reference:$(NC)"
	@echo "  $(GREEN)make start$(NC)       Start all services"
	@echo "  $(GREEN)make stop$(NC)        Stop all services"
	@echo "  $(GREEN)make logs$(NC)        View server logs"
	@echo "  $(GREEN)make status$(NC)      Check server status"
	@echo "  $(GREEN)make backup$(NC)      Create backup"
	@echo ""

#==============================================================================
# Server Lifecycle
#==============================================================================

start: validate-env ## Start all services
	@echo "$(BLUE)Starting services...$(NC)"
	$(COMPOSE) up -d
	@echo "$(GREEN)✓ Services started$(NC)"

stop: ## Stop all services
	@echo "$(BLUE)Stopping services...$(NC)"
	$(COMPOSE) stop
	@echo "$(GREEN)✓ Services stopped$(NC)"

down: ## Stop and remove containers
	@echo "$(BLUE)Stopping and removing containers...$(NC)"
	$(COMPOSE) down
	@echo "$(GREEN)✓ Containers removed$(NC)"

restart: ## Restart all services
	@echo "$(BLUE)Restarting services...$(NC)"
	$(COMPOSE) restart
	@echo "$(GREEN)✓ Services restarted$(NC)"

restart-server: ## Restart only Satisfactory server
	@echo "$(BLUE)Restarting Satisfactory server...$(NC)"
	$(COMPOSE) restart satisfactory
	@echo "$(GREEN)✓ Server restarted$(NC)"

#==============================================================================
# Monitoring
#==============================================================================

logs: ## View all service logs (follow mode)
	$(COMPOSE) logs -f

logs-server: ## View Satisfactory server logs
	$(COMPOSE) logs -f satisfactory

logs-tunnel: ## View Cloudflare tunnel logs
	$(COMPOSE) logs -f cloudflared

status: ## Check server status
	@$(SCRIPTS) status

ps: ## Show container status
	$(COMPOSE) ps

health: ## Run health monitoring
	@$(SCRIPTS) server monitor

#==============================================================================
# Backup & Update
#==============================================================================

backup: ## Create a backup
	@$(SCRIPTS) server backup

update: ## Update server to latest version
	@$(SCRIPTS) server update

import-save: ## Import a save file (use: make import-save FILE=path/to/save.sav)
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)Error: FILE not specified$(NC)"; \
		echo "Usage: make import-save FILE=path/to/save.sav"; \
		exit 1; \
	fi
	@$(SCRIPTS) server import "$(FILE)"

#==============================================================================
# Mods
#==============================================================================

mods-install: ## Install mods automatically
	@$(SCRIPTS) mods install

mods-manual: ## Install mods manually (use: make mods-manual FILES="*.pak")
	@if [ -z "$(FILES)" ]; then \
		echo "$(RED)Error: FILES not specified$(NC)"; \
		echo "Usage: make mods-manual FILES=\"~/Downloads/*.pak\""; \
		exit 1; \
	fi
	@$(SCRIPTS) mods manual $(FILES)

mods-list: ## Generate mod download list
	@$(SCRIPTS) mods list

mods-client-info: ## Show client mod installation instructions
	@echo "$(CYAN)======================================$(NC)"
	@echo "$(CYAN)  Client Mod Installation$(NC)"
	@echo "$(CYAN)======================================$(NC)"
	@echo ""
	@echo "$(GREEN)Windows (PowerShell):$(NC)"
	@echo "  Run: scripts/mods/client/install-client-mods.ps1"
	@echo ""
	@echo "$(GREEN)Linux/macOS (Bash):$(NC)"
	@echo "  Run: scripts/mods/client/install-client-mods.sh"
	@echo ""
	@echo "$(GREEN)Options:$(NC)"
	@echo "  --game-path PATH    Manually specify game path"
	@echo "  --category CAT      Install specific category"
	@echo "  --dry-run           Show what would be installed"
	@echo "  --list              List all available mods"
	@echo ""
	@echo "$(YELLOW)Full documentation:$(NC)"
	@echo "  scripts/mods/client/README.md"

#==============================================================================
# Network
#==============================================================================

network-verify: ## Verify Cloudflare tunnel connectivity
	@$(SCRIPTS) network verify

network-configure: ## Configure Cloudflare Zero Trust
	@$(SCRIPTS) network cloudflare

#==============================================================================
# Setup
#==============================================================================

setup: ## Run initial setup
	@./setup.sh

setup-cron: ## Install cron jobs for backup/monitoring
	@$(SCRIPTS) setup cron

validate-env: ## Validate environment configuration
	@./scripts/setup/validate-env.sh

#==============================================================================
# Utilities
#==============================================================================

shell: ## Open shell in Satisfactory container
	$(COMPOSE) exec satisfactory bash

shell-root: ## Open root shell in Satisfactory container
	$(COMPOSE) exec -u root satisfactory bash

pull: ## Pull latest Docker images
	@echo "$(BLUE)Pulling latest images...$(NC)"
	$(COMPOSE) pull
	@echo "$(GREEN)✓ Images updated$(NC)"

clean-logs: ## Clean old log files
	@echo "$(BLUE)Cleaning log files...$(NC)"
	@find data/logs -name "*.log" -mtime +7 -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Old logs cleaned$(NC)"

clean-backups: ## Clean old backup files (keeps recent)
	@echo "$(BLUE)Cleaning old backups...$(NC)"
	@find data/backups -name "*.tar.gz" -mtime +30 -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Old backups cleaned$(NC)"

#==============================================================================
# Development
#==============================================================================

lint: ## Run shell script linting
	@echo "$(BLUE)Linting shell scripts...$(NC)"
	@shellcheck scripts/**/*.sh 2>/dev/null || echo "$(YELLOW)shellcheck not installed$(NC)"

test-scripts: ## Test scripts without executing
	@echo "$(BLUE)Testing scripts...$(NC)"
	@bash -n scripts/main.sh && echo "$(GREEN)✓ main.sh OK$(NC)"
	@bash -n scripts/lib/common.sh && echo "$(GREEN)✓ common.sh OK$(NC)"
	@bash -n scripts/server/backup.sh && echo "$(GREEN)✓ backup.sh OK$(NC)"
