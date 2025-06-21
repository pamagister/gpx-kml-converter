import os
import socket
import subprocess
import sys
import traceback
import urllib.error
import urllib.request
from pathlib import Path


class FirewallHandler:
    """Handles firewall detection and configuration for network access."""

    def __init__(self, logger=None):
        self.logger = logger
        self.test_urls = [
            "http://httpbin.org/get",
            "http://www.google.com",
            "https://httpbin.org/get",
            "https://www.google.com",
        ]
        self.srtm_urls = [
            "https://cloud.sdsc.edu/v1/AUTH_opentopography/Raster/SRTM_GL1/",
            "http://cloud.sdsc.edu/v1/AUTH_opentopography/Raster/SRTM_GL1/",
        ]

    def check_network_access(self, timeout: int = 5) -> bool:
        """Check if network access is available."""
        self.logger.info("Checking network connectivity...")

        # First check basic connectivity
        if not self._check_basic_connectivity():
            self.logger.warning("Basic network connectivity failed")
            return False

        # Then check HTTP access
        if not self._check_http_access(timeout):
            self.logger.warning("HTTP access failed")
            return False

        # Finally check SRTM-specific URLs
        if not self._check_srtm_access(timeout):
            self.logger.warning("SRTM service access failed")
            return False

        self.logger.info("Network access verified successfully")
        return True

    def _check_basic_connectivity(self) -> bool:
        """Check basic network connectivity using socket."""
        try:
            # Try to connect to DNS servers
            for host, port in [("8.8.8.8", 53), ("1.1.1.1", 53)]:
                try:
                    with socket.create_connection((host, port), timeout=3):
                        return True
                except (TimeoutError, OSError):
                    continue
            return False
        except Exception as e:
            self.logger.debug(f"Basic connectivity check failed: {e}")
            return False

    def _check_http_access(self, timeout: int) -> bool:
        """Check HTTP access to common websites."""
        for url in self.test_urls:
            try:
                with urllib.request.urlopen(url, timeout=timeout) as response:
                    if response.status == 200:
                        self.logger.debug(f"HTTP access confirmed via {url}")
                        return True
            except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError) as e:
                self.logger.debug(f"HTTP access failed for {url}: {e}")
                continue
        return False

    def _check_srtm_access(self, timeout: int) -> bool:
        """Check access to SRTM-specific URLs."""
        for url in self.srtm_urls:
            try:
                with urllib.request.urlopen(url, timeout=timeout) as response:
                    if response.status in [200, 403]:  # 403 is expected for directory listing
                        self.logger.debug(f"SRTM access confirmed via {url}")
                        return True
            except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError) as e:
                self.logger.debug(f"SRTM access failed for {url}: {e}")
                continue
        return False

    def handle_firewall_issue(self):
        """Handle firewall issues by attempting to create rules and inform user."""
        self.logger.info("Attempting to resolve firewall issues...")

        # Get current executable path
        exe_path = self._get_executable_path()
        if not exe_path:
            self.logger.error("Could not determine executable path")
            self._show_manual_instructions()
            return

        # Try to create firewall rules
        if self._is_windows():
            self._handle_windows_firewall(exe_path)
        else:
            self._handle_linux_firewall(exe_path)

    def _get_executable_path(self) -> str | None:
        """Get the path of the current executable."""
        try:
            if getattr(sys, "frozen", False):
                # PyInstaller executable
                return sys.executable
            else:
                # Python script
                return sys.executable
        except Exception as e:
            self.logger.error(f"Error getting executable path: {e}")
            return None

    def _is_windows(self) -> bool:
        """Check if running on Windows."""
        return os.name == "nt"

    def _handle_windows_firewall(self, exe_path: str):
        """Handle Windows firewall configuration."""
        self.logger.info("Attempting to configure Windows Firewall...")

        app_name = Path(exe_path).stem

        # Commands to add firewall rules
        commands = [
            # Inbound rule
            [
                "netsh",
                "advfirewall",
                "firewall",
                "add",
                "rule",
                f"name={app_name}_Inbound",
                "dir=in",
                "action=allow",
                f"program={exe_path}",
                "enable=yes",
            ],
            # Outbound rule
            [
                "netsh",
                "advfirewall",
                "firewall",
                "add",
                "rule",
                f"name={app_name}_Outbound",
                "dir=out",
                "action=allow",
                f"program={exe_path}",
                "enable=yes",
            ],
        ]

        success = False
        for cmd in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                self.logger.info(
                    f"Firewall rule added successfully: {' '.join(cmd)} result: {result}"
                )
                success = True
            except subprocess.CalledProcessError as e:
                self.logger.warning(f"Failed to add firewall rule: {e}")
                self.logger.debug(f"Command: {' '.join(cmd)}")
                self.logger.debug(f"Error output: {e.stderr}")
            except Exception as e:
                self.logger.error(f"Unexpected error adding firewall rule: {e}")
                self.logger.debug(f"Full traceback:\n{traceback.format_exc()}")

        if success:
            self.logger.info(
                "Windows Firewall rules added successfully. Please restart the application."
            )
        else:
            self.logger.warning("Failed to automatically configure Windows Firewall.")
            self._show_manual_instructions()

    def _handle_linux_firewall(self, exe_path: str):
        """Handle Linux firewall configuration."""
        self.logger.info("Detected Linux system. Firewall configuration may be needed.")
        self._show_manual_instructions()

    def _show_manual_instructions(self):
        """Show general manual instructions"""
        self.logger.info(
            "Please check your firewall settings and ensure the application has network access.\n"
            "Refer to the documentation for manual configuration steps."
            "quick solution:"
            "Start your EXE as administrator:"
            "Right-click on EXE → Run as administrator"
            "Or temporarily deactivate the firewall:"
        )
