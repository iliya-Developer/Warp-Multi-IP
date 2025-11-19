import os
import subprocess
import time
from pathlib import Path

os.system('clear')
print("=" * 42)
print("Created by Parsa in OPIran club https://t.me/OPIranClub")
print("Love Iran :)")
print("=" * 42)

BASE_DIR = "/root/warp-confs"
os.makedirs(BASE_DIR, exist_ok=True)

# Ask user if they want to clean everything first
cleanup = input("Do you want to remove all existing configs and proxies? (y/n): ").strip().lower()
if cleanup == 'y':
    print("Cleaning up previous configurations...")
    for i in range(1, 13):
        os.system(f"systemctl stop danted-warp{i} 2>/dev/null")
        os.system(f"systemctl disable danted-warp{i} 2>/dev/null")
        os.system(f"rm -f /etc/systemd/system/danted-warp{i}.service")
        os.system(f"rm -f /etc/danted-multi/danted-warp{i}.conf")
        os.system(f"wg-quick down wgcf{i} 2>/dev/null || ip link delete wgcf{i} 2>/dev/null")
        os.system(f"rm -f /etc/wireguard/wgcf{i}.conf")
        os.system(f"rm -rf {BASE_DIR}/warp{i}")

    os.system("systemctl daemon-reload")
    print("Cleanup completed. Continuing with fresh setup...\n")

print("Installing WireGuard and required packages...")
os.system("apt update")
os.system("apt install -y wireguard resolvconf curl jq dante-server unzip")

if not Path("/usr/local/bin/wgcf").exists():
    print("Installing wgcf...")
    os.system("curl -fsSL git.io/wgcf.sh | bash")
    os.system("mv wgcf /usr/local/bin/")

os.chdir(BASE_DIR)

print("Generating 5 WARP configs...")
for i in range(1, 6):
    conf_path = f"/etc/wireguard/wgcf{i}.conf"
    if Path(conf_path).exists():
        print(f"  Config wgcf{i}.conf already exists, skipping.")
        continue

    folder = f"{BASE_DIR}/warp{i}"
    os.makedirs(folder, exist_ok=True)
    os.chdir(folder)

    if Path("wgcf-account.toml").exists():
        os.remove("wgcf-account.toml")

    os.system("wgcf register --accept-tos > /dev/null")
    os.system("wgcf generate")
    os.system(f"cp wgcf-profile.conf {conf_path}")

    ip_addr = f"172.16.0.{i+1}"
    table_id = 51820 + i

    os.system(f"sed -i 's|Address = .*|Address = {ip_addr}/32|' {conf_path}")
    os.system(
        f"sed -i '/\\[Interface\\]/a Table = {table_id}\\n"
        f"PostUp = ip rule add from {ip_addr}/32 table {table_id}\\n"
        f"PostDown = ip rule del from {ip_addr}/32 table {table_id}' {conf_path}"
    )

print("Reloading WireGuard interfaces...")
os.system("systemctl daemon-reload")
os.system("modprobe wireguard")

print("Bringing up interfaces...")
for i in range(1, 6):
    os.system(f"systemctl enable --now wg-quick@wgcf{i}")

print("Setting up Dante SOCKS proxies...")
os.makedirs("/etc/danted-multi", exist_ok=True)

for i in range(1, 6):
    port = 1080 + i
    ip = f"172.16.0.{i+1}"
    conf_file = f"/etc/danted-multi/danted-warp{i}.conf"

    with open(conf_file, "w") as f:
        f.write(
            f"""logoutput: /var/log/danted-warp{i}.log
internal: 127.0.0.1 port = {port}
external: {ip}
user.privileged: root
user.unprivileged: nobody
clientmethod: none
socksmethod: none
client pass {{ from: 0.0.0.0/0 to: 0.0.0.0/0 }}
socks pass {{ from: 0.0.0.0/0 to: 0.0.0.0/0 }}
"""
        )

    service_file = f"/etc/systemd/system/danted-warp{i}.service"
    with open(service_file, "w") as f:
        f.write(
            f"""[Unit]
Description=Dante SOCKS proxy warp{i}
After=network-online.target wg-quick@wgcf{i}.service
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/sbin/danted -f {conf_file}
Restart=always

[Install]
WantedBy=multi-user.target
"""
        )

print("Reloading systemd services...")
os.system("systemctl daemon-reload")

for i in range(1, 6):
    os.system(f"systemctl enable --now danted-warp{i}")

print("Done. All 5 WARP proxies are running and persistent after reboot!")
print("\nSOCKS5 proxies:")
for i in range(1, 6):
    print(f"  wgcf{i} → 127.0.0.1:{1080+i}")
