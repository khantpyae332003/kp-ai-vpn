#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# Called in the installed guest chroot; never on Android/host.
set -eu
profile=$1
# Restore hardware discovery disabled by the upstream container image.
for unit in systemd-udevd.service systemd-udevd-control.socket systemd-udevd-kernel.socket systemd-udev-trigger.service systemd-modules-load.service; do
 if [ "$(readlink /etc/systemd/system/"$unit" 2>/dev/null || true)" = /dev/null ]; then rm /etc/systemd/system/"$unit"; fi
done
[ "$(id -u)" = 0 ]
[ -x /usr/bin/startxfce4 ] && [ -x /usr/sbin/lightdm ]
mkdir -p /etc/lightdm/lightdm.conf.d /etc/sudoers.d /usr/local/sbin /etc/systemd/system /home/kasm-user/Desktop
cp -a /home/kasm-default-profile/. /home/kasm-user/
chown -R 1000:1000 /home/kasm-user
chmod 750 /home/kasm-user
usermod -s /bin/bash kasm-user
# Lock password authentication. Local VM console uses explicit autologin and sudo.
passwd -l root
passwd -l kasm-user
printf 'kasm-user ALL=(ALL:ALL) NOPASSWD: ALL\n' > /etc/sudoers.d/kp-local-guest
chmod 440 /etc/sudoers.d/kp-local-guest
visudo -cf /etc/sudoers.d/kp-local-guest
cat > /etc/lightdm/lightdm.conf.d/90-kp.conf <<'CONF'
[Seat:*]
autologin-user=kasm-user
autologin-user-timeout=0
user-session=xfce
autologin-session=xfce
xserver-command=X -nolisten tcp
CONF
cat > /home/kasm-user/Desktop/root-terminal.desktop <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=Root Terminal
Comment=Administrator terminal inside this Kali virtual machine
Exec=qterminal -e sudo -i
Icon=utilities-terminal
Terminal=false
DESKTOP
chmod 755 /home/kasm-user/Desktop/root-terminal.desktop
chown 1000:1000 /home/kasm-user/Desktop/root-terminal.desktop
printf 'kp-kali\n' > /etc/hostname
printf '127.0.0.1 localhost\n127.0.1.1 kp-kali\n::1 localhost ip6-localhost\n' > /etc/hosts
printf 'nameserver 10.0.2.3\n' > /etc/resolv.conf
printf 'UUID=%s / ext4 defaults 0 1\n' "$(blkid -s UUID -o value /dev/vda 2>/dev/null || true)" > /etc/fstab
ln -sf /dev/null /etc/systemd/system/serial-getty@ttyS0.service
# Container daemons are inappropriate in the local VM session.
for unit in kasm.service kasm-setup.service regenerate-ssh-host-keys.service nfs-client.target remote-fs.target cups.service cups.path cups.socket ModemManager.service smartmontools.service ssh.service ssh.socket redis-server.service postgresql.service mosquitto.service; do
 rm -f /etc/systemd/system/multi-user.target.wants/"$unit"
 ln -sf /dev/null /etc/systemd/system/"$unit"
done
ln -sf /lib/systemd/system/graphical.target /etc/systemd/system/default.target
ln -sf /lib/systemd/system/lightdm.service /etc/systemd/system/display-manager.service
mkdir -p /etc/systemd/system/graphical.target.wants
ln -sf /etc/systemd/system/kp-ready.service /etc/systemd/system/graphical.target.wants/kp-ready.service
cat > /usr/local/sbin/kp-ready <<READY
#!/bin/sh
printf '\\nKP:ROOT_UID:%s\\n' "\$(id -u)" > /dev/ttyS0
for n in \$(seq 1 600); do
 if pgrep -u 1000 -x xfce4-panel >/dev/null && pgrep -u 1000 -x xfce4-session >/dev/null; then
  uid=\$(sudo -u kasm-user sudo -n id -u) || exit 1
  printf '\\nKP:SUDO_UID:%s\\n' "\$uid" > /dev/ttyS0
  [ "\$uid" = 0 ] || exit 1
  printf '\\nKP:DESKTOP_READY:sha256:$profile\\n' > /dev/ttyS0
  exit 0
 fi
 sleep 2
done
printf '\\nKP:ERROR:Desktop session did not become ready; inspect guest journal\\n' > /dev/ttyS0
exit 1
READY
chmod 755 /usr/local/sbin/kp-ready
cat > /etc/systemd/system/kp-ready.service <<'SERVICE'
[Unit]
Description=Verify local Kali desktop and guest administrator
After=display-manager.service
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/kp-ready
TimeoutStartSec=1250
[Install]
WantedBy=graphical.target
SERVICE
# DHCP on emulated Ethernet, using systemd's installed network client.
mkdir -p /etc/systemd/network /etc/systemd/system/multi-user.target.wants
cat > /etc/systemd/network/20-kp.network <<'NET'
[Match]
Name=en* eth*
[Network]
DHCP=ipv4
NET
ln -sf /lib/systemd/system/systemd-networkd.service /etc/systemd/system/multi-user.target.wants/systemd-networkd.service
# Reset container identity and transient records before first VM boot.
: > /etc/machine-id
rm -f /var/lib/dbus/machine-id
ln -sf /etc/machine-id /var/lib/dbus/machine-id
printf '%s\n' "$profile" > /etc/kp-kali-profile
