#!/bin/bash
# Satisfactory Server Backup Script
# Creates compressed backups with retention policy

set -e

# Source common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/common.sh"

# Initialize
init_common
set_log_file "${LOGS_DIR}/backup.log"

# Default values from env
BACKUP_RETENTION_DAILY=$(get_env "BACKUP_RETENTION_DAILY" "7")
BACKUP_RETENTION_WEEKLY=$(get_env "BACKUP_RETENTION_WEEKLY" "4")

# Create backup
create_backup() {
    local backup_type=$1
    local timestamp=$(date '+%Y%m%d-%H%M%S')
    local date_only=$(date '+%Y%m%d')

    local backup_name
    if [[ "$backup_type" == "weekly" ]]; then
        backup_name="satisfactory-weekly-${date_only}.tar.gz"
    else
        backup_name="satisfactory-${timestamp}.tar.gz"
    fi

    local backup_path="${BACKUP_DIR}/${backup_name}"

    log "Starting backup: $backup_name"

    if tar -czf "$backup_path" -C "$PROJECT_DIR" data/saved 2>/dev/null; then
        local size=$(du -h "$backup_path" | cut -f1)
        log_success "Backup completed: $backup_name (Size: $size)"
        echo "$backup_path"
    else
        log_error "Backup failed: $backup_name"
        return 1
    fi
}

# Cleanup old backups
cleanup_backups() {
    log "Cleaning up old backups..."

    # Remove daily backups older than 3 days
    local deleted
    deleted=$(find "$BACKUP_DIR" -name "satisfactory-*.tar.gz" ! -name "satisfactory-weekly-*.tar.gz" -type f -mtime +3 -print -delete | wc -l)
    if [[ "$deleted" -gt 0 ]]; then
        log "Removed $deleted daily backup(s) older than 3 days"
    fi

    # Keep weekly backups for configured weeks
    local weekly_count
    weekly_count=$(find "$BACKUP_DIR" -name "satisfactory-weekly-*.tar.gz" | wc -l)
    if [[ "$weekly_count" -gt "$BACKUP_RETENTION_WEEKLY" ]]; then
        local to_remove=$((weekly_count - BACKUP_RETENTION_WEEKLY))
        find "$BACKUP_DIR" -name "satisfactory-weekly-*.tar.gz" -type f -printf '%T@ %p\n' | \
            sort -n | head -n "$to_remove" | cut -d' ' -f2- | xargs rm -f
        log "Removed $to_remove old weekly backup(s)"
    fi
}

# Main execution
main() {
    log "=== Backup Script Started ==="

    # Check if save directory exists
    if [[ ! -d "$SAVE_DIR" ]]; then
        log_error "Save directory not found: $SAVE_DIR"
        exit 1
    fi

    # Determine backup type (weekly on Sunday, daily otherwise)
    local day_of_week=$(date '+%u')
    local backup_type="daily"

    if [[ "$day_of_week" == "7" ]]; then
        backup_type="weekly"
        log "Creating weekly backup (Sunday)"
    else
        log "Creating daily backup"
    fi

    # Create backup
    if backup_path=$(create_backup "$backup_type"); then
        cleanup_backups

        # Send Discord notification
        local backup_filename
        backup_filename=$(basename "$backup_path")
        if [[ "$backup_type" == "weekly" ]]; then
            send_discord_notification "📦 Weekly Backup" \
                "Weekly backup completed successfully: $backup_filename" \
                "$DISCORD_GREEN"
        else
            send_discord_notification "📦 Daily Backup" \
                "Daily backup completed successfully: $backup_filename" \
                "$DISCORD_GREEN"
        fi

        log "=== Backup Script Completed Successfully ==="
    else
        log_error "Backup script failed"
        send_discord_notification "❌ Backup Failed" \
            "Backup failed! Please check logs." \
            "$DISCORD_RED"
        exit 1
    fi
}

main "$@"
