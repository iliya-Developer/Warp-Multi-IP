cd ~

[ -f warp.py ] && rm -f warp.py

echo "Downloading latest warp.py..."
sudo wget -O warp.py https://raw.githubusercontent.com/iliya-Developer/Warp-Multi-IP/refs/heads/main/warp.py

if [ ! -s warp.py ]; then
    echo "Download failed or file is empty — retrying..."
    sudo wget -O warp.py https://raw.githubusercontent.com/iliya-Developer/Warp-Multi-IP/refs/heads/main/warp.py
fi

chmod +x warp.py
sudo python3 warp.py
