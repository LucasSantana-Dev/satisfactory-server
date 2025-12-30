# Satisfactory Dedicated Server

A containerized Satisfactory dedicated server with Cloudflare Tunnel for secure, semi-public access.

## Features

- 🐳 Docker Compose orchestration for easy management
- 🔒 Cloudflare Tunnel integration for secure access without port forwarding
- 💾 Automatic backups with configurable retention
- 📊 Health monitoring with Discord notifications
- 🎮 Mod support with installation scripts
- ⚙️ Environment-based configuration (no hardcoded secrets)

## Quick Start

```bash
# 1. Run setup
./setup.sh

# 2. Configure .env (edit required secrets)
nano .env

# 3. Start server
make start

# 4. Check status
make status
```

## Prerequisites

- Docker and Docker Compose installed
- At least 8GB RAM available
- ~10GB free disk space
- Cloudflare account with Zero Trust (for tunnel setup)

## Project Structure

```
satisfactory-server/
├── README.md                 # This file
├── CHANGELOG.md              # Version history
├── Makefile                  # Task automation
├── setup.sh                  # Initial setup script
├── docker-compose.yml        # Container orchestration
├── .env.example              # Configuration template
│
├── config/                   # Configuration files
│   └── cloudflared/          # Cloudflare tunnel config
│
├── docs/                     # Documentation
│   ├── CLOUDFLARE_ZERO_TRUST_SETUP.md
│   ├── FRIEND_GUIDE.md
│   ├── MODS_GUIDE.md
│   └── ...
│
├── scripts/                  # Management scripts
│   ├── main.sh               # Unified CLI
│   ├── lib/                  # Shared libraries
│   ├── server/               # Server operations
│   ├── mods/                 # Mod management
│   ├── network/              # Network operations
│   └── setup/                # Setup utilities
│
└── data/                     # Runtime data (gitignored)
    ├── backups/              # Automatic backups
    ├── gamefiles/            # Game installation
    ├── logs/                 # Application logs
    └── saved/                # Game saves
```

## Configuration

### Required Secrets

Edit `.env` and configure these required values:

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `CLOUDFLARE_TUNNEL_TOKEN` | Tunnel authentication | [Cloudflare Dashboard](https://one.dash.cloudflare.com/) > Networks > Tunnels |
| `SFTP_PASSWORD` | SFTP access password | Generate: `openssl rand -base64 32` |

### Optional Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MAXPLAYERS` | 4 | Maximum players |
| `MEMORY_LIMIT` | 8G | Docker memory limit |
| `DISCORD_WEBHOOK_URL` | - | Discord notifications |
| `AUTOSAVEINTERVAL` | 300 | Seconds between saves |

See `.env.example` for all available options.

## Usage

### Using Make (Recommended)

```bash
make help           # Show all commands

# Server lifecycle
make start          # Start all services
make stop           # Stop all services
make restart        # Restart all services
make logs           # View logs

# Operations
make status         # Check server status
make backup         # Create backup
make update         # Update server

# Mods
make mods-install   # Auto-install mods
make mods-manual FILES="~/Downloads/*.pak"

# Network
make network-verify # Verify tunnel

# Setup
make validate-env   # Validate configuration
make setup-cron     # Install automation
```

### Using Scripts Directly

```bash
./scripts/main.sh help              # Show commands
./scripts/main.sh server backup     # Create backup
./scripts/main.sh mods install      # Install mods
./scripts/main.sh network verify    # Verify tunnel
```

### Using Docker Compose

```bash
docker compose up -d                # Start
docker compose stop                 # Stop
docker compose logs -f              # Logs
docker compose restart              # Restart
```

## Connecting to Server

### For Server Owner

1. Complete setup above
2. Configure Cloudflare Zero Trust (see `docs/CLOUDFLARE_ZERO_TRUST_SETUP.md`)
3. Set up WARP enrollment for friends (see `docs/WARP_ENROLLMENT_SETUP.md`)

### For Friends

See `docs/FRIEND_GUIDE.md` for complete instructions:

1. Install [Cloudflare WARP client](https://developers.cloudflare.com/cloudflare-one/connections/connect-devices/warp/)
2. Enroll device using team domain
3. Connect with WARP enabled to: `172.19.0.2:7777`

## Backup & Restore

### Automatic Backups

After running `make setup-cron`:
- **Daily backups**: 4:00 AM
- **Weekly backups**: Sundays
- **Retention**: 7 daily + 4 weekly backups

### Manual Backup

```bash
make backup
# or
./scripts/main.sh server backup
```

### Restore from Backup

```bash
# Stop server
make stop

# Extract backup
cd data/backups
tar -xzf satisfactory-YYYYMMDD-HHMMSS.tar.gz -C ..

# Start server
make start
```

## Mod Support

```bash
# Automatic installation (tries GitHub releases)
make mods-install

# Manual installation
make mods-manual FILES="~/Downloads/*.pak"

# Generate download list
make mods-list
```

See `docs/MODS_GUIDE.md` for detailed instructions.

## Monitoring

### Discord Notifications

Configure `DISCORD_WEBHOOK_URL` in `.env` to receive:
- 📦 Backup completed
- 🔴 Server down alerts
- ⚠️ Server degraded warnings
- ✅ Server recovered
- 🔄 Update completed

### Health Checks

```bash
make health         # Run health check
make status         # Quick status
```

## Security

- ✅ No hardcoded secrets in configuration files
- ✅ Required secrets fail fast if not configured
- ✅ `.env` excluded from version control
- ✅ SFTP disabled by default (opt-in with profile)
- ✅ Cloudflare Tunnel for secure access

### Enabling SFTP (Optional)

SFTP is disabled by default. To enable:

```bash
# 1. Set strong password in .env
SFTP_PASSWORD=$(openssl rand -base64 32)

# 2. Start with SFTP profile
docker compose --profile sftp up -d
```

## Troubleshooting

### Server Won't Start

```bash
# Check logs
make logs-server

# Verify configuration
make validate-env

# Check resources
free -h && df -h
```

### Friends Can't Connect

1. Verify tunnel: `make network-verify`
2. Check WARP client is connected
3. Confirm friend enrolled in Zero Trust
4. Use correct IP: `172.19.0.2:7777`

See `docs/FRIEND_GUIDE.md` for more troubleshooting.

### Performance Issues

```bash
# Increase memory in .env
MEMORY_LIMIT=12G
MEMORY_RESERVATION=6G

# Restart
make restart
```

## Documentation

| Document | Description |
|----------|-------------|
| [CLOUDFLARE_ZERO_TRUST_SETUP.md](docs/CLOUDFLARE_ZERO_TRUST_SETUP.md) | Cloudflare configuration guide |
| [FRIEND_GUIDE.md](docs/FRIEND_GUIDE.md) | Connection guide for friends |
| [MODS_GUIDE.md](docs/MODS_GUIDE.md) | Mod installation guide |
| [WARP_ENROLLMENT_SETUP.md](docs/WARP_ENROLLMENT_SETUP.md) | WARP enrollment setup |
| [scripts/README.md](scripts/README.md) | Scripts documentation |

## Resources

- [Satisfactory Server Wiki](https://satisfactory.fandom.com/wiki/Dedicated_servers)
- [wolveix/satisfactory-server](https://github.com/wolveix/satisfactory-server)
- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
- [Cloudflare WARP Client](https://developers.cloudflare.com/cloudflare-one/connections/connect-devices/warp/)

## License

This setup uses the [wolveix/satisfactory-server](https://github.com/wolveix/satisfactory-server) Docker image (MIT License).
