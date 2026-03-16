"""
RDP Guard - Firewall Manager
"""

import subprocess
import logging

log = logging.getLogger(__name__)
RULE_PREFIX = "RDPGuard_Block_"


class FirewallManager:
    def block_ip(self, ip: str, permanent: bool = False):
        rule_name = f"{RULE_PREFIX}{ip}"
        label = "PERMANENT" if permanent else "TEMPORARY"
        try:
            self._delete_rule(rule_name)
            subprocess.run([
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={rule_name}", "dir=in", "action=block",
                f"remoteip={ip}", "protocol=any", "enable=yes",
                f"description=RDPGuard {label} block",
            ], check=True, capture_output=True, text=True)
            log.info(f"Firewall rule added ({label}): block {ip}")
            return True
        except subprocess.CalledProcessError as exc:
            log.error(f"Failed to add firewall rule for {ip}: {exc.stderr.strip()}")
            return False

    def unblock_ip(self, ip: str):
        rule_name = f"{RULE_PREFIX}{ip}"
        self._delete_rule(rule_name)
        log.info(f"Firewall rule removed: unblock {ip}")

    def is_blocked(self, ip: str) -> bool:
        rule_name = f"{RULE_PREFIX}{ip}"
        try:
            result = subprocess.run([
                "netsh", "advfirewall", "firewall", "show", "rule",
                f"name={rule_name}",
            ], capture_output=True, text=True)
            return "No rules match" not in result.stdout
        except Exception:
            return False

    def _delete_rule(self, rule_name: str):
        try:
            subprocess.run([
                "netsh", "advfirewall", "firewall", "delete", "rule",
                f"name={rule_name}",
            ], capture_output=True, text=True)
        except Exception:
            pass
