import os
import subprocess
import time
from pathlib import Path
import signal
import sys


def run(cmd):
    """Run shell command safely with error handling."""
    result = os.system(cmd)
    if result != 0:
        print(f"❌ ERROR: Command failed → {cmd}")
    return result


def check_cmd(cmd):
    """Run command and return output or None if fails."""
    try:
        return subprocess.check_output(cmd, shell=True).decode().strip()
    except:
        return None


def fix_dns():
    print("\n🔧 Checking DNS...")
    
    print("Checking internet connection...")
    if os.system("ping -c 1 8.8.8.8 > /dev/null 2>&1") != 0:
        print("❌ No internet connection. Fix your network first.")
        sys.exit(1)

    print("Checking DNS resolution...")
    if os.system("ping -c 1 google.com > /dev/null 2>&1") != 0:
        print("⚠ DNS is broken → Fixing automatically...")

        run('bash -c \'echo "nameserver 4.2.2.4" > /etc/resolv.conf\'')
        run('bash -c \'echo "nameserver 8.8.8.8" >> /etc/resolv.conf\'')

        print("🔄 Retesting DNS...")
        if os.system("ping -c 1 google.com > /dev/null 2>&1") != 0:
            print("❌ DNS failed even after fixing. Stop and fix manually.")
            sys.exit(1)

        print("✅ DNS has been fixed.")
    else:
        print("✅ DNS is OK!")

def handle_exit(sig, frame):
    print("\n\n🛑 CTRL+C detected — exiting safely.\n")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)


# -----------------------------
# START SCRIPT
# -----------------------------

os.system('clear')
print("=" * 42)
print("Created by Parsa in OPIran club")
print("Love Iran ❤️")
print("=" * 42)

# Fix DNS at start
fix_dns()

BASE_DIR = "/root/warp-confs"
run(f"mkdir -p {BASE_DIR}")

# Cleanup prompt
cleanup = input("Do you want to remove all existing configs and proxies? (y/n): ").strip().lower()
if cleanup == 'y':
    print("🧹 Cleaning old configs...")
    for i in range(1, 13):
        run(f"systemctl stop danted-warp{i}")
        run(f"systemctl disable danted-warp{i}")
        run(f"rm -f /etc/systemd/system/danted-warp{i}.service")
        run(f"rm -f /etc/danted-multi/danted-warp{i}.conf")
        run(f"wg-quick down wgcf{i} || ip link delete wgcf{i}")
        run(f"rm -f /etc/wireguard/wgcf{i}.conf")
        run(f"rm -rf {BASE_DIR}/warp{i}")

    run("systemctl daemon-reload")
    print("✅ Cleanup done.\n")


print("📦 Installing dependencies...")
run("apt update -y")
run("apt install -y wireguard resolvconf curl jq dante-server unzip wget")

# Install wgcf if missing
if not Path("/usr/local/bin/wgcf").exists():
    print("⬇ Installing wgcf...")
    run("wget https://github.com/ViRb3/wgcf/releases/latest/download/wgcf_2.2.20_linux_amd64 -O /usr/local/bin/wgcf")
    run("chmod +x /usr/local/bin/wgcf")

if not Path("/usr/local/bin/wgcf").exists():
    print("❌ wgcf installation FAILED. Stop.")
    sys.exit(1)

os.chdir(BASE_DIR)

print("⚙ Generating WARP configs...")
for i in range(1, 6):
    conf_path = f"/etc/wireguard/wgcf{i}.conf"

    folder = f"{BASE_DIR}/warp{i}"
    run(f"mkdir -p {folder}")
    os.chdir(folder)

    if Path("wgcf-account.toml").exists():
        os.remove("wgcf-account.toml")

    print(f"➡ Registering WARP{i}...")
    if run("wgcf register --accept-tos > /dev/null") != 0:
        print("❌ wgcf register failed. Skipping.")
        continue

    run("wgcf generate")

    if not Path("wgcf-profile.conf").exists():
        print("❌ wgcf-profile.conf missing! Aborting.")
        sys.exit(1)

    run(f"cp wgcf-profile.conf {conf_path}")

    ip = f"172.16.0.{i+1}"
    table = 51820 + i

    run(f"sed -i 's|Address = .*|Address = {ip}/32|' {conf_path}")
    run(
        f"sed -i '/\\[Interface\\]/a Table = {table}\\n"
        f"PostUp = ip rule add from {ip}/32 table {table}\\n"
        f"PostDown = ip rule del from {ip}/32 table {table}' {conf_path}"
    )

print("🔄 Reloading systemd & WireGuard...")
run("systemctl daemon-reload")
run("modprobe wireguard")

print("🚀 Starting WireGuard tunnels...")
for i in range(1, 6):
    run(f"systemctl enable --now wg-quick@wgcf{i}")

print("🧱 Creating Dante configs...")
run("mkdir -p /etc/danted-multi")

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

    with open(f"/etc/systemd/system/danted-warp{i}.service", "w") as f:
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

run("systemctl daemon-reload")

print("\n🚀 Starting Dante proxies...")
for i in range(1, 6):
    run(f"systemctl enable --now danted-warp{i}")

print("\n🎉 ALL DONE! SOCKS5 proxies are ready:")

for i in range(1, 6):
    print(f"  wgcf{i} → 127.0.0.1:{1080+i}")
