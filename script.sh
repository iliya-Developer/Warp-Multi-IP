cd ~

if [ ! -f warp.py ]; then
    echo "warp.py not found — downloading..."
    sudo wget -O warp.py https://raw.githubusercontent.com/iliya-Developer/Warp-Multi-IP/refs/heads/main/warp.py
else
    echo "warp.py already exists."
fi

if [ ! -s warp.py ]; then
    echo "warp.py is empty or corrupted — re-downloading..."
    sudo wget -O warp.py https://raw.githubusercontent.com/iliya-Developer/Warp-Multi-IP/refs/heads/main/warp.py
fi

chmod +x warp.py
sudo python3 warp.py
