<h1>UAC</h1>
<h2>OpenWin's User Account Control Module.</h2>

<b>Description:</b> Securely uses a front-end when user prompts for `sudo`, simulating the Win 10 experience of UAC.

<b>How it works:</b> It is used with `SUDO_ASKPASS` and creates an alias for `sudo -A` on `~/.bashrc`.

<b>How to use:</b> Use `./install.sh` and reboot your system to install, or `./uninstall.sh` and reboot your system to uninstall.

##### Tested Platforms
| OS | Display Server | Shell | Works? |
| :--- | --- | --- | ---: |
| Linux Mint | xorg | bash | YES |
| Kubuntu | wayland | bash | YES |

<h3>Screenshots</h3>
<img src="screenshot-english.png" width="50%">
<img src="screenshot-portuguese.png" width="50%">
