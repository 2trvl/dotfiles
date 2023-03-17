#!/bin/zsh

chckusr=$(id -u)

if [ "$chckusr" -eq 0 ]; then
    echo "Cleaning RAM and SWAP, please, just wait.."
    sync
    echo 3 > /proc/sys/vm/drop_caches
    swapoff -a
    swapon -a
    echo "Cleaned!"
else
    echo "Starting as root.."
    sudo "$0"
fi
