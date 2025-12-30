# Cloudflare Tunnel Verification Guide

This guide helps you verify that your Cloudflare Tunnel is working correctly and that friends can connect to your Satisfactory server.

## Quick Verification

Run the verification script:
```bash
./scripts/verify-tunnel.sh
```

This script checks:
- Container status
- Tunnel connection
- WARP routing status
- Server health
- Port connectivity

## Manual Verification Steps

### 1. Check Container Status

```bash
docker compose ps
```

**Expected output:**
- `satisfactory-server`: Status should be `Up` and `healthy`
- `satisfactory-cloudflared`: Status should be `Up`

### 2. Check Tunnel Logs

```bash
docker compose logs cloudflared --tail 50
```

**Look for:**
- ✅ `Registered tunnel connection` - Tunnel is connected
- ✅ `"warp-routing":{"enabled":true}` - WARP routing is enabled
- ✅ Multiple connection registrations (normal for redundancy)

**Example of healthy tunnel:**
```
INF Registered tunnel connection connIndex=0 connection=...
INF Updated to new configuration config="{\"ingress\":[{\"hostname\":\"satisfactory.luk-homeserver.com.br\",\"originRequest\":{},\"service\":\"tcp://satisfactory:7777\"}...}"
```

### 3. Check Cloudflare Dashboard

1. Go to [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
2. Navigate to **Networks** > **Tunnels**
3. Find your tunnel (should show as **HEALTHY**)
4. Verify:
   - ✅ Tunnel status is **HEALTHY** (green)
   - ✅ Private network route `172.19.0.0/16` is configured
   - ✅ WARP routing is enabled

### 4. Test Port Connectivity

```bash
# Test game port
nc -zv localhost 7777

# Test messaging port
nc -zv localhost 8888
```

**Expected:** Connection successful

### 5. Verify Server Health

```bash
docker inspect --format='{{.State.Health.Status}}' satisfactory-server
```

**Expected:** `healthy` or empty (if health check not configured)

## Testing Friend Connection

### Prerequisites for Friends

Before friends can connect, they must:

1. **Install Cloudflare WARP Client**
   - Download from: https://1.1.1.1/
   - Install on their system

2. **Enroll in Zero Trust**
   - Open WARP application
   - Connect to organization: `luk-homelab`
   - Complete enrollment (email or PIN)

3. **Verify WARP is Connected**
   - WARP icon should show as connected/green
   - Status should say "Connected"

### Connection Test

**From a friend's computer (with WARP connected):**

1. **Test network connectivity:**
   ```bash
   # Windows PowerShell
   Test-NetConnection -ComputerName 172.19.0.2 -Port 7777

   # Linux/Mac
   nc -zv 172.19.0.2 7777
   ```

2. **In Satisfactory:**
   - Open **Server Manager**
   - Click **Add Server**
   - Enter: `172.19.0.2:7777`
   - Click **Connect**

## Troubleshooting

### Tunnel Not Connecting

**Symptoms:**
- No "Registered tunnel connection" in logs
- Tunnel shows as unhealthy in dashboard

**Solutions:**
1. Check tunnel token in `.env`:
   ```bash
   grep CLOUDFLARE_TUNNEL_TOKEN .env
   ```

2. Verify token is valid in Cloudflare dashboard

3. Restart tunnel:
   ```bash
   docker compose restart cloudflared
   ```

4. Check logs for errors:
   ```bash
   docker compose logs cloudflared | grep -i error
   ```

### Friends Can't Connect

**Checklist:**

1. ✅ **WARP is installed and connected**
   - Friend must have WARP running
   - WARP must show "Connected" status

2. ✅ **Friend is enrolled in Zero Trust**
   - Must use team domain: `luk-homelab`
   - Enrollment must be complete

3. ✅ **Private network route is configured**
   - Check Cloudflare dashboard
   - Route `172.19.0.0/16` must exist

4. ✅ **Server is running**
   ```bash
   docker compose ps
   ```

5. ✅ **Using correct IP and port**
   - IP: `172.19.0.2` (NOT the public domain)
   - Port: `7777`

### Server Not Appearing in Browser

**Note:** The server may not appear in Satisfactory's server browser even when working correctly. This is normal with Cloudflare Tunnel.

**Solution:** Use direct IP connection:
- IP: `172.19.0.2`
- Port: `7777`

### Connection Timeout

**Possible causes:**

1. **WARP not connected** - Most common issue
   - Friend must have WARP running and connected
   - Check WARP status icon

2. **Wrong IP address**
   - Must use: `172.19.0.2:7777`
   - NOT the public domain name

3. **Server not running**
   ```bash
   docker compose ps satisfactory-server
   ```

4. **Firewall blocking**
   - Check friend's firewall settings
   - WARP should handle this, but verify

## Verification Checklist

Use this checklist to verify everything is working:

- [ ] Both containers are running (`docker compose ps`)
- [ ] Tunnel logs show "Registered tunnel connection"
- [ ] Cloudflare dashboard shows tunnel as HEALTHY
- [ ] Private network route `172.19.0.0/16` is configured
- [ ] WARP routing is enabled in dashboard
- [ ] Server health check passes
- [ ] Ports 7777 and 8888 are responding locally
- [ ] Friend has WARP installed and connected
- [ ] Friend is enrolled in Zero Trust
- [ ] Friend can connect using `172.19.0.2:7777`

## Getting Help

If issues persist:

1. **Collect information:**
   ```bash
   # Run verification script
   ./scripts/verify-tunnel.sh

   # Get tunnel logs
   docker compose logs cloudflared --tail 100 > tunnel-logs.txt

   # Get server logs
   docker compose logs satisfactory --tail 100 > server-logs.txt
   ```

2. **Check Cloudflare dashboard:**
   - Tunnel status
   - Connection metrics
   - Error logs

3. **Verify friend's setup:**
   - WARP connection status
   - Zero Trust enrollment
   - Network connectivity

## CIDR Invalid Error Troubleshooting

If you're seeing "CIDR invalid" when trying to add `172.19.0.0/16` in the Cloudflare dashboard:

### Quick Fix Steps

**1. Verify You're in the Correct Location**

**Wrong Location** (will show CIDR invalid):
- Networks > Routes > Create CIDR route

**Correct Location** (for Tunnel Private Networks):
- Networks > Tunnels > [Your Tunnel Name] > Routes tab
- OR Networks > Tunnels > [Your Tunnel Name] > Configure > Private Network

**2. Check CIDR Format**

The CIDR must be entered exactly as:
```
172.19.0.0/16
```

**Common mistakes:**
- ❌ `172.19.0.0 / 16` (spaces)
- ❌ `172.19.0.0/16 ` (trailing space)
- ❌ `"172.19.0.0/16"` (quotes)
- ✅ `172.19.0.0/16` (correct)

**3. Verify Docker Network**

Check your Docker network CIDR:
```bash
docker network inspect satisfactory-server_satisfactory-network | grep Subnet
```

Should show: `"Subnet": "172.19.0.0/16"`

**4. Alternative: Use Tunnel Configuration**

Instead of adding via Routes, configure directly in tunnel:
1. Go to Networks > Tunnels > [Your Tunnel]
2. Click **Configure** > **Private Network**
3. Add: `172.19.0.0/16`
4. Save

## Tunnel Setup Guide

### Initial Tunnel Configuration

1. **Go to Cloudflare Zero Trust Dashboard**:
   - Navigate to: https://one.dash.cloudflare.com/
   - Go to **Networks** > **Tunnels**

2. **Configure Public Hostname** (For TCP Access):
   - Click on your tunnel
   - Go to **Public Hostname** section
   - Edit existing or add new hostname:
     - **Subdomain**: `satisfactory`
     - **Domain**: `luk-homeserver.com.br`
     - **Service Type**: `TCP` (not HTTPS!)
     - **URL**: `satisfactory:7777` (Docker service name and port)
   - Click **Save**

3. **Add Messaging Port** (Optional):
   - Add another public hostname:
     - **Subdomain**: `satisfactory-msg`
     - **Domain**: `luk-homeserver.com.br`
     - **Service Type**: `TCP`
     - **URL**: `satisfactory:8888`
   - Click **Save**

4. **Configure Private Network** (For UDP Support):
   - In tunnel configuration, go to **Private Network**
   - Click **Add a private network**
   - Set **IP/CIDR**: `172.19.0.0/16`
   - Click **Save**

5. **Enable WARP Routing**:
   - Go to **Settings** > **WARP Client**
   - Enable **Private Network** routing
   - Friends will need Cloudflare WARP client installed

### Verify Docker Network

Your Docker network information:
- **Network**: `satisfactory-server_satisfactory-network`
- **Subnet**: `172.19.0.0/16` ✅
- **Satisfactory Container IP**: `172.19.0.2` ✅

Use `172.19.0.0/16` in the Private Network configuration.

## Additional Resources

- **Friend Connection Guide**: See `FRIEND_GUIDE.md`
- **Zero Trust Setup**: See `CLOUDFLARE_ZERO_TRUST_SETUP.md`
- **Domain Setup**: See `DOMAIN_SETUP.md`
