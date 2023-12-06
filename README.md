# BLOGGER.

A simple blog written with Flask. It currently features,

- Authentication
- Flash messages
- Tagging for posts
- File attachments
- CKEditor for a WYSIWYG blogging experience with image upload support. 
    - Video and other file types can be embedded by clicking the source button - just upload file attachments, and reference them.
- Cascade deletions for tags and files
- Decoupled configs

Features still missing,

- Commenting on posts
- File attachment deletions


## Preview

See a collection of screenshots [here](resources/README.md).


## Set up

This site was developed against Python 3.10.12, so you should first have that version of Python installed. Other versions (3.11) probably work too.


### Linux Environment
```
git clone https://github.com/skwzrd/blogger.git
cd blogger
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt

sudo apt update
sudo apt install redis-server
sudo nano /etc/redis/redis.conf # set line `supervised no` to `supervised systemd`
sudo systemctl restart redis
sudo systemctl status redis


python3 main.py
```


### Site Configurations

- Create a long, random string (`import secrets` `secrets.token_urlsafe(64)`) in a file called `secret.txt`.
- Rename `configs_COPY.py` to `configs.py` and configure its variables.
- Initialize a new database by running `init_database.py`, or drop-in an existing SQLite database.
- Flush redis records `redis-cli flushall`.


### Formatting

Formatting libraries are not including in the production venv, so install them with `pip install djhtml isort black`.

- `djhtml ./templates`
- `isort ./`
- `black --line-length=140 --target-version=py310 .`


## Hosting on Ubuntu

`python3 -m pip install gunicorn`

`sudo nano /etc/systemd/system/blogger.service`

```service
[Unit]
Description=Blogger - Gunicorn Service
After=network.target

[Service]
User=user1
Group=www-data

WorkingDirectory=/home/user1/blogger
Environment="PATH=/home/user1/venv/bin"
ExecStart=/home/user1/venv/bin/gunicorn -w 2 -b 127.0.0.1:8080 'main:app'

Type=simple
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```