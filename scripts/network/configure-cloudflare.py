#!/usr/bin/env python3
"""
Cloudflare Zero Trust Configuration Script
Automates configuration of Private Network routing and WARP enrollment

Requirements:
    pip install requests

Usage:
    export CLOUDFLARE_API_TOKEN="your-api-token"
    export CLOUDFLARE_ACCOUNT_ID="your-account-id"
    python3 configure-cloudflare.py
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from common import (
    init_script, load_env, get_env,
    print_header, print_info, print_success, print_error, print_warn
)

try:
    import requests
except ImportError:
    print_error("'requests' library not found")
    print("Install with: pip3 install requests")
    sys.exit(1)

# Configuration
DOCKER_NETWORK_CIDR = "172.19.0.0/16"
TUNNEL_NAME = "satisfactory-server"
ZERO_TRUST_API_BASE = "https://api.cloudflare.com/client/v4"


class CloudflareZeroTrustConfig:
    """Helper class for configuring Cloudflare Zero Trust"""

    def __init__(self, api_token: str, account_id: str):
        self.api_token = api_token
        self.account_id = account_id
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

    def get_tunnels(self) -> Optional[list]:
        """Get list of tunnels"""
        url = f"{ZERO_TRUST_API_BASE}/accounts/{self.account_id}/cfd_tunnel"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json().get("result", [])
        except requests.exceptions.RequestException as e:
            print_error(f"Error fetching tunnels: {e}")
            return None

    def find_tunnel(self, tunnel_name: str) -> Optional[Dict[str, Any]]:
        """Find tunnel by name"""
        tunnels = self.get_tunnels()
        if not tunnels:
            return None

        for tunnel in tunnels:
            if tunnel.get("name") == tunnel_name:
                return tunnel
        return None

    def get_tunnel_config(self, tunnel_id: str) -> Optional[Dict[str, Any]]:
        """Get tunnel configuration"""
        url = f"{ZERO_TRUST_API_BASE}/accounts/{self.account_id}/cfd_tunnel/{tunnel_id}/configurations"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json().get("result", {})
        except requests.exceptions.RequestException as e:
            print_error(f"Error fetching tunnel config: {e}")
            return None

    def add_private_network(self, tunnel_id: str, cidr: str, description: str = "") -> bool:
        """Add private network to tunnel configuration"""
        config = self.get_tunnel_config(tunnel_id)
        if not config:
            print_error("Could not fetch tunnel configuration")
            return False

        config_obj = config.get("config", {})
        warp_routing = config_obj.get("warp-routing", {})
        private_networks = warp_routing.get("enabled", False)

        if private_networks:
            print_info(f"WARP routing already enabled for tunnel {tunnel_id}")

        print_info(f"To add private network {cidr}, use Cloudflare dashboard:")
        print(f"  Networks > Tunnels > {tunnel_id} > Private Network")
        print(f"  Add CIDR: {cidr}")
        print(f"  Description: {description}")

        return True

    def create_warp_enrollment_rule(self, rule_name: str, emails: Optional[list] = None) -> bool:
        """Create WARP enrollment rule"""
        print_info("To create WARP enrollment rule, use Cloudflare dashboard:")
        print(f"  Settings > WARP Client > Device enrollment permissions")
        print(f"  Add rule: {rule_name}")
        if emails:
            print(f"  Emails: {', '.join(emails)}")
        else:
            print("  Use One-time PIN method")

        return True


def main():
    print_header("Cloudflare Zero Trust Configuration Script")

    # Initialize paths
    paths, _ = init_script("cloudflare-config")

    # Load configuration
    api_token = get_env("CLOUDFLARE_API_TOKEN")
    account_id = get_env("CLOUDFLARE_ACCOUNT_ID")

    if not api_token:
        print_error("CLOUDFLARE_API_TOKEN not found")
        print("Set it as environment variable or in .env file")
        print()
        print("To get your API token:")
        print("1. Go to https://dash.cloudflare.com/profile/api-tokens")
        print("2. Create token with Zero Trust permissions")
        print("3. Export: export CLOUDFLARE_API_TOKEN='your-token'")
        return 1

    if not account_id:
        print_error("CLOUDFLARE_ACCOUNT_ID not found")
        print("Set it as environment variable or in .env file")
        print()
        print("To get your Account ID:")
        print("1. Go to https://dash.cloudflare.com/")
        print("2. Select your account")
        print("3. Copy Account ID from right sidebar")
        print("4. Export: export CLOUDFLARE_ACCOUNT_ID='your-account-id'")
        return 1

    # Initialize configurator
    config = CloudflareZeroTrustConfig(api_token, account_id)

    # Find tunnel
    print_info(f"Searching for tunnel: {TUNNEL_NAME}")
    tunnel = config.find_tunnel(TUNNEL_NAME)

    if not tunnel:
        print_error(f"Tunnel '{TUNNEL_NAME}' not found")
        print("Available tunnels:")
        tunnels = config.get_tunnels()
        if tunnels:
            for t in tunnels:
                print(f"  - {t.get('name', 'Unknown')} (ID: {t.get('id', 'Unknown')})")
        return 1

    tunnel_id = tunnel.get("id")
    print_success(f"Found tunnel: {tunnel.get('name')} (ID: {tunnel_id})")
    print()

    # Add private network
    print_info(f"Configuring private network: {DOCKER_NETWORK_CIDR}")
    config.add_private_network(tunnel_id, DOCKER_NETWORK_CIDR, "Satisfactory Docker Network")
    print()

    # Create enrollment rule
    print_info("WARP Enrollment Configuration:")
    config.create_warp_enrollment_rule("Satisfactory Players")
    print()

    print("=" * 60)
    print_success("Configuration guide generated!")
    print("=" * 60)
    print()
    print_warn("NOTE: Some operations require manual configuration in the dashboard.")
    print("See CLOUDFLARE_ZERO_TRUST_SETUP.md for detailed instructions.")
    print()
    print_info("Dashboard: https://one.dash.cloudflare.com/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
