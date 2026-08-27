# Age of Empires Match Notifier

A Discord bot to notify the match results of your [Age of Empires 2: Definitive Edition](https://www.ageofempires.com/) community.

### Introduction

The goal of this project is to keep your community informed about your successes (and defeats) in Age of Empires 2 Definitive Edition by sending the results of your matches through Discord notifications.

Example:

<img width="421" height="239" alt="aoe2-notif" src="https://github.com/user-attachments/assets/6ce1e747-a632-4878-b150-1c2570accc9c" />

> The bot collects game data from World's Edge public API.

### Requirements

Software:
- [python](https://www.python.org/downloads/release/python-370/) 3.7 or higher.

### Install on Ubuntu Focal

1. Update the package lists:
```
$ apt update
```

2. Install pip:
```
$ apt install -y python3-pip
```

3. Install the project dependencies:
```
$ pip3 install requests pyyaml discord.py
```

4. Create the installation directory:
```
$ mkdir /etc/aoe
```

5. Put the sources inside:
```
$ ls -1 /etc/aoe/
aoe.py
config.py
engine.py
link_resolver.py
main.py
match_classifier.py
message_formatter.py
models.py
```

### Usage

1. Edit the configuration file by filling your friends's Steam IDs and your Discord webhook:
```
$ cat /etc/aoe/config.yml
worldsedge_url: "https://aoe-api.worldsedgelink.com/community"
discord_hook: "https://discord.com/api/webhooks/your/token"
players:
- name: "TheViper"
  steamId: "76561197984749679"
  profileId: 196240
- name: "Hera"
  steamId: "76561198449406083"
  profileId: 199325
```

2. Start the service:
```
$ python3.8 /etc/aoe/main.py --config-file="/etc/aoe/config.yml" --translations-file="/etc/aoe/en.yml"
```

### As daemon

1. Set un unit systemd daemon:
```
$ cat /etc/systemd/system/aoe.service
[Unit]
Description=aoe-notifier
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
ExecStart=python3 /etc/aoe/main.py --config-file="/etc/aoe/config.yml" --translations-file="/etc/aoe/en.yml"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Enable the service
```
$ systemctl daemon-reload
$ systemctl start aoe.service
```

3. Check the logs
```
$ journalctl -u aoe.service -f
```

### Development

Install the dev dependencies and run the test suite:
```
$ pip3 install -r requirements-dev.txt
$ python3 -m pytest
```

The test suite covers `match_classifier.py` and `message_formatter.py`, the two modules with no
network or Discord I/O. There are no tests for the World's Edge client or the Discord webhook
send path, since those need live credentials to exercise meaningfully.
