# Domain Setup Guide - Using luk-homeserver.com.br

This guide explains how to configure your domain `luk-homeserver.com.br` (or subdomain) so friends can connect using the domain name instead of the IP address.

## Current Configuration

Your tunnel is already configured with:
- **Tunnel Hostname**: `satisfactory.luk-homeserver.com.br`
- **Service**: `tcp://satisfactory:7777`
- **WARP Routing**: Enabled

## DNS Configuration

To use the domain, you need to configure DNS in Cloudflare:

### Option 1: Using Cloudflare DNS (Recommended)

1. **Go to Cloudflare Dashboard**:
   - Navigate to: https://dash.cloudflare.com/
   - Select your domain: `luk-homeserver.com.br`

2. **Add DNS Record** (if not already exists):
   - Go to **DNS** > **Records**
   - Click **Add record**
   - **Type**: `CNAME`
   - **Name**: `satisfactory` (or `@` for root domain)
   - **Target**: `satisfactory.luk-homeserver.com.br` (or your tunnel's CNAME target)
   - **Proxy status**: ⚠️ **DNS only** (gray cloud) - Important for TCP connections!
   - Click **Save**

3. **Verify DNS Propagation**:
   ```bash
   # Check DNS resolution
   dig satisfactory.luk-homeserver.com.br
   # or
   nslookup satisfactory.luk-homeserver.com.br
   ```

### Option 2: Using Tunnel's Automatic DNS

If your tunnel is configured with automatic DNS:

1. **Check Tunnel Configuration**:
   - Go to: https://one.dash.cloudflare.com/
   - Navigate to: **Networks** > **Tunnels**
   - Click on your tunnel
   - Check **Public Hostnames** section
   - Verify `satisfactory.luk-homeserver.com.br` is listed

2. **DNS should be automatically configured** by Cloudflare Tunnel

## Important Notes

### DNS Proxy Status

⚠️ **Critical**: For TCP/UDP game connections, the DNS record should be **DNS only** (gray cloud), NOT proxied (orange cloud).

**Why?**
- Proxied DNS (orange cloud) only works for HTTP/HTTPS
- Satisfactory needs direct TCP/UDP connections
- DNS only allows direct connection through the tunnel

### WARP Still Required

Even with the domain configured, friends still need:
- ✅ Cloudflare WARP client installed and connected
- ✅ Enrolled in Zero Trust (team: `luk-homelab`)
- ✅ WARP routing enabled

The domain just makes it easier to remember - it still routes through WARP to the private network.

## Testing the Domain

### From Your Server

```bash
# Test DNS resolution
nslookup satisfactory.luk-homeserver.com.br

# Test connection (should work locally)
nc -zv satisfactory.luk-homeserver.com.br 7777
```

### From Friend's Computer (with WARP)

```bash
# Test DNS resolution
nslookup satisfactory.luk-homeserver.com.br

# Test connection
nc -zv satisfactory.luk-homeserver.com.br 7777
```

**Expected**: Connection successful

## Using the Domain in Satisfactory

Once DNS is configured, friends can connect using:

**Server Address**: `satisfactory.luk-homeserver.com.br`
**Port**: `7777`

Instead of: `172.19.0.2:7777`

## Alternative: Root Domain

If you want to use the root domain `luk-homeserver.com.br` instead of a subdomain:

1. **Update Tunnel Configuration**:
   - In Cloudflare Zero Trust dashboard
   - Edit your tunnel's public hostname
   - Change from `satisfactory.luk-homeserver.com.br` to `luk-homeserver.com.br`
   - Or add both

2. **Update DNS**:
   - Add CNAME record for root domain pointing to tunnel

3. **Friends connect using**: `luk-homeserver.com.br:7777`

## Troubleshooting

### Domain Not Resolving

1. **Check DNS Configuration**:
   ```bash
   dig satisfactory.luk-homeserver.com.br
   ```

2. **Verify DNS is not proxied**:
   - In Cloudflare DNS settings
   - Ensure record shows gray cloud (DNS only)

3. **Check Tunnel Hostname**:
   - Verify in Cloudflare Zero Trust dashboard
   - Tunnel should list the hostname

### Connection Timeout with Domain

1. **WARP must be connected**:
   - Friend must have WARP running
   - WARP must show "Connected"

2. **Try IP address as fallback**:
   - If domain doesn't work, use: `172.19.0.2:7777`

3. **Check DNS propagation**:
   - DNS changes can take a few minutes
   - Wait 5-10 minutes after changes

### Domain Resolves but Can't Connect

1. **Verify tunnel is healthy**:
   ```bash
   docker compose logs cloudflared | grep -i "registered"
   ```

2. **Check tunnel configuration**:
   - Ensure service is `tcp://satisfactory:7777`
   - Verify WARP routing is enabled

3. **Test with IP first**:
   - If IP works but domain doesn't, it's a DNS/tunnel routing issue

## Verification Checklist

- [ ] DNS record exists in Cloudflare
- [ ] DNS record is set to "DNS only" (gray cloud)
- [ ] Tunnel hostname matches DNS record
- [ ] Tunnel is healthy in Cloudflare dashboard
- [ ] WARP routing is enabled
- [ ] Domain resolves correctly (`nslookup` or `dig`)
- [ ] Connection works from friend's computer (with WARP)

## Next Steps

1. **Configure DNS** (if not already done)
2. **Update Friend Guide** to use domain instead of IP
3. **Test connection** from a friend's computer
4. **Share updated connection details** with friends

## Related Documentation

- **Friend Connection Guide**: See `FRIEND_GUIDE.md`
- **Tunnel Verification**: See `TUNNEL_VERIFICATION.md`
- **Zero Trust Setup**: See `CLOUDFLARE_ZERO_TRUST_SETUP.md`

