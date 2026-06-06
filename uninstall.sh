#!/usr/bin/env bash
sudo rm -rf /etc/OpenWin-UAC
sudo rm -rf /usr/bin/openwin-uac
sudo sed -i '/^SUDO_ASKPASS="\/usr\/bin\/openwin-uac"/d' /etc/environment
sed -i '/if \[ -t 1 \]; then alias sudo="sudo -A"; fi/d' ~/.bashrc
echo "OpenWin-UAC Uninstallation Script finished. Please, reboot your system to apply the changes!"