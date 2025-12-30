# Cloudflare Tunnel Configuration

This directory contains the Cloudflare Tunnel configuration for the Satisfactory server.

## Setup Instructions

### Method 1: Token-Based (Recommended)

1. Go to [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
2. Navigate to **Networks** > **Tunnels**
3. Click **Create a tunnel**
4. Choose **Cloudflared** as the connector
5. Give it a name (e.g., `satisfactory-server`)
6. Copy the **Tunnel Token**
7. Paste it into your `.env` file as `CLOUDFLARE_TUNNEL_TOKEN`

When using a token, cloudflared automatically configures the tunnel. The `config.yml` file in this directory is optional but can be used for additional settings.

### Method 2: Config File-Based

If you prefer to use a config file instead of a token:

1. Create a tunnel in the Cloudflare dashboard
2. Download the credentials file and save it as `credentials.json` in this directory
3. Update `config.yml` with your tunnel ID
4. Uncomment the config file command in `docker-compose.yml`:
   ```yaml
   command: tunnel --config /etc/cloudflared/config.yml run
   ```

## Private Network Setup (For UDP Support)

Satisfactory requires UDP on port 7777. To enable this through Cloudflare Tunnel:

1. **Enable WARP Routing:**
   - In Cloudflare Zero Trust dashboard, go to **Networks** > **Tunnels**
   - Select your tunnel
   - Enable **Private Network** routing
   - Add your server's private IP (e.g., `172.18.0.0/16` for Docker network)

2. **Configure Clients:**
   - Friends need to install [Cloudflare WARP client](https://developers.cloudflare.com/cloudflare-one/connections/connect-devices/warp/)
   - Connect to your organization's WARP
   - They can then connect to the server using the tunnel IP or hostname

## Files

- `config.yml` - Optional configuration file for advanced settings
- `credentials.json` - Tunnel credentials (only needed for config-based setup, should be in .gitignore)

## Troubleshooting

### Tunnel Not Connecting

1. Verify the token is correct in `.env`
2. Check tunnel status: `docker compose logs cloudflared`
3. Verify tunnel appears in Cloudflare dashboard

### UDP Not Working

1. Ensure WARP routing is enabled in Cloudflare dashboard
2. Verify clients have WARP installed and connected
3. Check private network routes are configured correctly

### Connection Issues

1. Check tunnel health: `docker compose exec cloudflared cloudflared tunnel info`
2. Review logs: `docker compose logs -f cloudflared`
3. Verify network connectivity between containers

