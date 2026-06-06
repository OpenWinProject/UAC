#!/usr/bin/env bash
sudo apt install -y python3 python3-pip python3-dev libgirepository-1.0-dev libgirepository-2.0-dev libcairo2-dev pkg-config
sudo mkdir /etc/OpenWin-UAC
sudo cp -r main.py index.html assets/ /etc/OpenWin-UAC/
sudo python3 -m venv /etc/OpenWin-UAC/venv
sudo /etc/OpenWin-UAC/venv/bin/pip install --upgrade pip setuptools wheel pywebview pywebview[qt] pygobject
sudo touch /usr/bin/openwin-uac
sudo tee /usr/bin/openwin-uac << 'EOF' > /dev/null
#!/usr/bin/env bash
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="$XAUTHORITY"
exec /etc/OpenWin-UAC/venv/bin/python3 /etc/OpenWin-UAC/main.py
EOF
sudo chmod +x /usr/bin/openwin-uac
echo 'SUDO_ASKPASS="/usr/bin/openwin-uac"' | sudo tee -a /etc/environment > /dev/null
echo 'if [ -t 1 ]; then alias sudo="sudo -A"; fi' >> ~/.bashrc
echo "OpenWin-UAC Installation Script finished. Please, reboot your system to apply the changes!"
