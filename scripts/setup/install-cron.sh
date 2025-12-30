#!/bin/bash
# Cron Installation Script for Satisfactory Server
# Installs cron jobs for backup and monitoring

set -e

# Source common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/common.sh"

# Initialize
init_common

BACKUP_SCRIPT="${SCRIPTS_DIR}/server/backup.sh"
MONITOR_SCRIPT="${SCRIPTS_DIR}/server/monitor.sh"

print_header "Satisfactory Server Cron Installation"

# Check if running as root or with sudo
if [[ "$EUID" -eq 0 ]]; then
    print_warn "Running as root. Cron jobs will be installed for root user."
    print_warn "Consider running as your user account instead."
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 1
    fi
fi

# Check if scripts exist
if [[ ! -f "$BACKUP_SCRIPT" ]]; then
    print_error "Backup script not found: $BACKUP_SCRIPT"
    exit 1
fi

if [[ ! -f "$MONITOR_SCRIPT" ]]; then
    print_error "Monitor script not found: $MONITOR_SCRIPT"
    exit 1
fi

# Make scripts executable
chmod +x "$BACKUP_SCRIPT"
chmod +x "$MONITOR_SCRIPT"
print_success "Scripts are executable"

# Get current user
CURRENT_USER=${SUDO_USER:-$USER}
CRON_FILE="/tmp/satisfactory-cron-$$"

# Backup existing crontab
print_info "Backing up existing crontab..."
crontab -l > "$CRON_FILE" 2>/dev/null || touch "$CRON_FILE"

# Check if jobs already exist
if grep -q "satisfactory.*backup.sh" "$CRON_FILE" 2>/dev/null; then
    print_warn "Backup cron job already exists"
    read -p "Replace existing backup job? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        grep -v "satisfactory.*backup.sh" "$CRON_FILE" > "${CRON_FILE}.tmp"
        mv "${CRON_FILE}.tmp" "$CRON_FILE"
    fi
fi

if grep -q "satisfactory.*monitor.sh" "$CRON_FILE" 2>/dev/null; then
    print_warn "Monitor cron job already exists"
    read -p "Replace existing monitor job? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        grep -v "satisfactory.*monitor.sh" "$CRON_FILE" > "${CRON_FILE}.tmp"
        mv "${CRON_FILE}.tmp" "$CRON_FILE"
    fi
fi

# Add new cron jobs
echo ""
print_info "Adding cron jobs..."

# Backup job: Daily at 4 AM
echo "# Satisfactory Server - Daily backup at 4 AM" >> "$CRON_FILE"
echo "0 4 * * * cd $PROJECT_DIR && $BACKUP_SCRIPT >> $LOGS_DIR/backup-cron.log 2>&1" >> "$CRON_FILE"

# Monitor job: Every 5 minutes
echo "# Satisfactory Server - Health check every 5 minutes" >> "$CRON_FILE"
echo "*/5 * * * * cd $PROJECT_DIR && $MONITOR_SCRIPT >> $LOGS_DIR/monitor-cron.log 2>&1" >> "$CRON_FILE"

# Install crontab
print_info "Installing crontab..."
crontab "$CRON_FILE"

# Cleanup
rm -f "$CRON_FILE"

print_header "Installation Complete"
print_success "Cron jobs installed successfully!"
echo ""
echo "Installed jobs:"
echo "  - Daily backup: 0 4 * * * (4:00 AM)"
echo "  - Health monitoring: */5 * * * * (every 5 minutes)"
echo ""
echo "To view your crontab:"
echo "  crontab -l"
echo ""
echo "To remove all Satisfactory cron jobs:"
echo "  crontab -l | grep -v 'satisfactory' | crontab -"
echo ""
echo "Log files:"
echo "  - Backup: $LOGS_DIR/backup-cron.log"
echo "  - Monitor: $LOGS_DIR/monitor-cron.log"
