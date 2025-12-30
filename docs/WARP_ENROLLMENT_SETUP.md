# WARP Enrollment Setup for Friends

This guide shows you exactly how to configure WARP enrollment so your friends can connect to your Satisfactory server.

## Quick Setup (5 minutes)

### Step 1: Access Device Enrollment Settings

**Try these locations in order:**

1. **Team & Resources (Most Common Location)**:
   - Go to [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
   - In the **left sidebar**, click **Team & Resources**
   - Click **Devices** (or look for **Device enrollment**)
   - You should see **Device enrollment permissions** section

2. **Settings Tab (Alternative)**:
   - Go to [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
   - Click **Settings** in the left sidebar
   - Look through the tabs for **WARP Client** or **Device enrollment**
   - If not visible, use **Team & Resources** > **Devices** instead

3. **Direct Search**:
   - Press **⌘+K** (Mac) or **Ctrl+K** (Windows/Linux) to open search
   - Type: `device enrollment` or `warp enrollment`
   - Click on the result

4. **Direct URL** (if you know your account ID):
   - Go to: `https://one.dash.cloudflare.com/[your-account-id]/team-and-resources/devices`

### Step 2: Create Enrollment Rule

Once you're in the **Device enrollment permissions** section:

1. Click **Add a rule** button (usually at the top right)
2. If you don't see "Add a rule", look for:
   - **Create enrollment rule**
   - **New enrollment rule**
   - **Add enrollment method**

### Step 3: Choose Enrollment Method

You have two options:

#### Option A: One-time PIN (Recommended - Easiest for Friends)

1. **Rule name**: Enter `Satisfactory Players` (or any name you prefer)
2. **Selector** or **Method**: Select **One-time PIN** (may also be called "PIN" or "One-time code")
3. **Value**: Leave empty (PIN will be generated automatically)
4. Click **Save** or **Create**

5. **Generate PIN**:
   - After saving, you'll see your rule in the list
   - Find your rule (`Satisfactory Players`)
   - Click on it or look for a **Generate PIN** / **View PIN** / **Show PIN** button
   - Copy the PIN (it will look like: `1234-5678-9012` or similar format)
   - **Share this PIN with your friends**

**PIN Details:**
- PINs typically expire after 24 hours or after first use
- You can generate a new PIN anytime
- Each PIN can be used by multiple friends (until it expires)

#### Option B: Email-based Enrollment (More Secure)

1. **Rule name**: Enter `Satisfactory Players`
2. **Selector** or **Method**: Select **Emails** (may also be called "Email" or "Email addresses")
3. **Value**: Enter your friends' email addresses (comma-separated)
   - Example: `friend1@example.com, friend2@example.com`
4. Click **Save** or **Create**

**Email Details:**
- Friends will receive an email invitation
- They must use the exact email address you added
- Case-sensitive (Friend@Example.com ≠ friend@example.com)

### Step 4: Share Information with Friends

Share the following with your friends:

**Required Information:**
- **Team Domain**: `luk-homelab.cloudflareaccess.com`
- **Team Name**: `luk-homelab`
- **Enrollment PIN**: (if using PIN method) - The PIN you generated
- **Server Address**: `satisfactory.luk-homeserver.com.br:7777` (or `172.19.0.2:7777`)

**Also share:**
- `FRIEND_GUIDE.md` - Complete connection instructions for friends

## Visual Navigation Guide

### Finding Device Enrollment Settings

**Path 1 (Most Common):**
```
Cloudflare Zero Trust Dashboard
└── Team & Resources (left sidebar)
    └── Devices
        └── Device enrollment permissions
            └── [Add a rule] button
```

**Path 2 (Alternative):**
```
Cloudflare Zero Trust Dashboard
└── Settings (left sidebar)
    └── [Look for WARP Client or Device enrollment tab]
        └── Device enrollment permissions
```

**If you can't find it:**
- Use the search bar (⌘+K or Ctrl+K) and search for "device enrollment"
- Or go directly to: `https://one.dash.cloudflare.com/[your-account-id]/team-and-resources/devices`

### Enrollment Rule Configuration

```
Add Enrollment Rule Dialog
├── Rule name: "Satisfactory Players"
├── Selector/Method: [Dropdown]
│   ├── One-time PIN ← Recommended
│   └── Emails
└── Value: [Leave empty for PIN] or [Enter emails]
```

## Verification

After creating the enrollment rule:

1. **Verify rule is active**:
   - Go back to **Team & Resources** > **Devices** (or wherever you found it)
   - You should see your rule listed under **Device enrollment permissions**
   - Status should show as **Active** or **Enabled**

2. **Test enrollment** (optional):
   - Install WARP on a test device
   - Try enrolling using the PIN or email
   - Verify it works before sharing with friends

## Troubleshooting: Can't Find Device Enrollment

If you can't find the Device enrollment section:

1. **Check your plan**:
   - Device enrollment requires a Cloudflare Zero Trust plan
   - Free tier should work, but verify your account has Zero Trust enabled

2. **Try different navigation**:
   - Look in **Team & Resources** > **Devices**
   - Check **Settings** tabs for WARP-related options
   - Use the search function (⌘+K / Ctrl+K)

3. **Check permissions**:
   - Ensure you have admin/owner access to the Zero Trust account
   - Some features may require specific roles

4. **Alternative: Use Cloudflare API**:
   - If the UI is not accessible, you can use the API
   - See `scripts/configure_cloudflare_api.py` for API-based setup

## Managing Enrollment

### Generate New PIN

1. Go to **Team & Resources** > **Devices** (or **Settings** > **WARP Client** if available)
2. Find your enrollment rule in the **Device enrollment permissions** section
3. Click on the rule or look for **Generate PIN** / **View PIN** button
4. Copy and share new PIN with friends

### Add More Friends (Email Method)

1. Go to **Team & Resources** > **Devices** (or **Settings** > **WARP Client**)
2. Find your enrollment rule in the list
3. Click on the rule to edit it
4. Edit the **Value** field (email addresses)
5. Add more email addresses (comma-separated)
6. Click **Save**

### Revoke Access

1. Go to **Team & Resources** > **Devices** (or **Settings** > **WARP Client**)
2. Find your enrollment rule in the **Device enrollment permissions** section
3. Click **Delete** or **Disable** on the rule
4. Or edit the rule to remove specific emails from the list

## Troubleshooting

### Friends Can't Enroll

**Check:**
1. ✅ Enrollment rule is **Active** (not disabled)
2. ✅ PIN hasn't expired (if using PIN method)
3. ✅ Email matches exactly (if using email method - case-sensitive)
4. ✅ Friends are using correct team domain: `luk-homelab.cloudflareaccess.com`

**Solution:**
- Generate a new PIN
- Or verify email addresses are correct

### PIN Not Working

**Possible causes:**
- PIN expired (generate a new one)
- PIN already used (if single-use)
- Wrong team domain entered

**Solution:**
- Generate a fresh PIN
- Verify friends are using: `luk-homelab` as team name

### Email Not Received

**Check:**
- Email address is correct (case-sensitive)
- Check spam/junk folder
- Verify email is added to the enrollment rule

**Solution:**
- Re-add email address
- Or switch to PIN method (easier)

## Best Practices

1. **Use PIN for casual gaming**:
   - Easier to share
   - No email verification needed
   - Quick setup for friends

2. **Use Email for security**:
   - Better access control
   - Audit trail of who enrolled
   - Can revoke individual access

3. **Keep PINs fresh**:
   - Generate new PINs periodically
   - Don't share expired PINs
   - One PIN can be used by multiple friends

4. **Document your setup**:
   - Note which method you're using
   - Keep track of active PINs
   - Update friend list as needed

## Next Steps

After configuring enrollment:

1. ✅ **Share with friends**:
   - Send `FRIEND_GUIDE.md`
   - Provide team domain: `luk-homelab`
   - Share PIN (if using PIN method)

2. ✅ **Friends install WARP**:
   - Download from: https://1.1.1.1/
   - Install on their system

3. ✅ **Friends enroll**:
   - Open WARP app
   - Connect to organization: `luk-homelab`
   - Enter PIN or use email

4. ✅ **Friends connect**:
   - Open Satisfactory
   - Connect to: `satisfactory.luk-homeserver.com.br:7777`

## Quick Reference

**Dashboard URL**: https://one.dash.cloudflare.com/
**Path**: Team & Resources > Devices > Device enrollment permissions
**Alternative Path**: Settings > (look for WARP Client or Device enrollment tab)
**Team Domain**: `luk-homelab.cloudflareaccess.com`
**Team Name**: `luk-homelab`

**Recommended Method**: One-time PIN
**PIN Location**: Team & Resources > Devices > [Your Rule] > Generate PIN

## Related Documentation

- **Friend Connection Guide**: `FRIEND_GUIDE.md` - Share this with friends
- **Zero Trust Setup**: `CLOUDFLARE_ZERO_TRUST_SETUP.md` - Complete setup guide
- **Tunnel Verification**: `TUNNEL_VERIFICATION.md` - Verify everything works
