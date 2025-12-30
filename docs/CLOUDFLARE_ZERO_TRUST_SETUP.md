# Cloudflare Zero Trust Setup Guide

This guide walks you through setting up Cloudflare Zero Trust with WARP routing to enable UDP support for your Satisfactory server.

## Prerequisites

- Cloudflare account (free tier works)
- Access to [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
- Your Satisfactory server tunnel already created

## Step 1: Create/Verify Zero Trust Organization

1. Go to [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
2. If you don't have a Zero Trust organization yet:
   - Click **Get Started** or **Sign Up**
   - Choose a team name (e.g., `luk-homeserver`)
   - Complete the setup wizard
3. Note your **Team Domain**: `luk-homelab.cloudflareaccess.com`
   - This will be used by friends to enroll their devices
   - Team name: `luk-homelab`

## Step 2: Configure Private Network Routing

**Important**: Private networks for Cloudflare Tunnels are configured through the tunnel's routing settings, not as separate CIDR routes.

1. Navigate to **Networks** > **Tunnels** in the Zero Trust dashboard
2. Find and click on your Satisfactory tunnel (the one with your tunnel token)
3. Click on the tunnel name to view its details
4. Look for **Private Network** section or **Routes** tab
5. Click **Add a route** or **Configure routes**
6. Select **Private Network** as the route type
7. Enter the following:
   - **Network**: `172.19.0.0/16`
   - **Description**: `Satisfactory Docker Network`
   - **Type**: Private Network (not Public Hostname)
8. Click **Save route**

**Alternative Method (if above doesn't work):**

If you see a "CIDR invalid" error, try these alternatives:

1. **Use the tunnel's configuration file approach:**
   - The private network might need to be configured via the tunnel's config
   - Go to **Networks** > **Tunnels** > Your tunnel > **Configure**
   - Look for **Private Network** or **WARP Routing** settings
   - Enable **Private Network routing**
   - Add the network there

2. **Verify the CIDR format:**
   - Ensure you're entering exactly: `172.19.0.0/16` (no spaces)
   - The format should be: `IP_ADDRESS/SUBNET_MASK`
   - Verify your Docker network: `docker network inspect satisfactory-server_satisfactory-network`

3. **Check if WARP routing needs to be enabled first:**
   - Go to **Settings** > **WARP Client** > **Device Settings**
   - Ensure **Private Network routing** is enabled for your organization
   - Then return to tunnel configuration

This allows WARP clients to route traffic to your Docker network where Satisfactory runs.

## Step 3: Configure WARP Client Settings

1. Navigate to **Settings** > **WARP Client** in the Zero Trust dashboard
2. Under **Device enrollment permissions**, click **Add a rule**
3. Configure the enrollment rule:
   - **Rule name**: `Satisfactory Players`
   - **Selector**: Choose one:
     - **Emails**: Add specific email addresses (friends' emails)
     - **One-time PIN**: Allows anyone with a PIN to enroll (easier for friends)
   - **Value**:
     - If using emails: Enter comma-separated email addresses
     - If using PIN: Leave empty (PIN will be generated)
4. Click **Save**

### Using One-time PIN (Recommended for Friends)

1. After creating the PIN enrollment rule, go to **Settings** > **WARP Client**
2. Find your enrollment rule and click **Generate PIN**
3. Share this PIN with your friends (it expires after use or time limit)
4. Friends will use this PIN during WARP enrollment

## Step 4: Verify Tunnel Configuration

1. Go back to **Networks** > **Tunnels** > Your tunnel
2. Verify the **Private Network** tab shows `172.19.0.0/16`
3. Check the tunnel status shows as **Healthy** and **Connected**

## Step 5: Test WARP Routing

After friends enroll their devices, they should be able to:

1. Connect to your server using the Docker network IP: `172.19.0.2:7777`
2. UDP traffic should work properly for Satisfactory gameplay

## Troubleshooting

### "CIDR Invalid" Error

If you see "CIDR invalid" when trying to add `172.19.0.0/16`:

1. **Verify you're in the correct section:**
   - You should be in **Networks** > **Tunnels** > Your tunnel > **Routes** or **Private Network**
   - NOT in **Networks** > **Routes** (that's for different routing)

2. **Check the CIDR format:**
   - Must be exactly: `172.19.0.0/16` (no spaces, no quotes)
   - Verify with: `docker network inspect satisfactory-server_satisfactory-network`

3. **Try alternative approach:**
   - Some Cloudflare accounts require enabling Private Network routing at the organization level first
   - Go to **Settings** > **WARP Client** > Enable **Private Network routing**
   - Then return to tunnel configuration

4. **Use API method:**
   - If UI continues to fail, use the Cloudflare API
   - See `configure_cloudflare_api.py` script for API-based configuration

### Tunnel Not Showing Private Network

- Ensure you've added the private network in the tunnel configuration (not as a separate route)
- Check that the CIDR matches your Docker network: `172.19.0.0/16`
- Verify tunnel is running: `docker compose ps` in your server directory
- Check tunnel logs: `docker compose logs cloudflared`

### Friends Can't Enroll

- Verify enrollment rule is active in **Settings** > **WARP Client**
- Check that emails match exactly (case-sensitive)
- If using PIN, ensure it hasn't expired
- Friends should use your team domain: `your-team-name.cloudflareaccess.com`

### UDP Still Not Working

- Verify WARP client is connected on friend's device
- Check that private network routing is enabled in tunnel config
- Ensure friend's device shows as enrolled in **My Team** > **Devices**

## Next Steps

After completing this setup:

1. Share the friend connection guide (`FRIEND_GUIDE.md`) with your friends
2. Provide them with:
   - Your team domain name
   - Enrollment PIN (if using PIN method)
   - Server connection details (IP: `172.19.0.2`, Port: `7777`)

## Reference Links

- [Cloudflare Private Networks Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/private-net/)
- [WARP Client Setup](https://developers.cloudflare.com/cloudflare-one/connections/connect-devices/warp/)
- [Zero Trust Dashboard](https://one.dash.cloudflare.com/)
