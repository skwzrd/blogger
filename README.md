# BLOGGER

A simple blog written with Flask. It currently features,

- WYSIWYG post editor
- Admin account access for CRUD actions
- Tags
- Comments
- File attachments
- Contact form
- Documentation for set-up
- Endpoint rate limiting
- Flash messages
- Mobile support
- Easily customizable CSS


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

- Create a long, random string in a file called `secret.txt`.
    - Note: The following does the job, `tr -dc A-Za-z0-9 </dev/urandom | head -c 64 > secret.txt`
- Rename `configs_COPY.py` to `configs.py` and configure its variables.
    - Note: Class variables in `CONSTS` that are all-caps are available in Flask `app.configs['NAME']`.
- Initialize a new database by running `init_database.py`, or drop-in an existing SQLite database.
    - Note: When `CONSTS.TESTING = True`, on each request, BLOGGER will check if a new database has to be created.
- Flush redis records `redis-cli flushall`.
- Customize your site's styling by modifying the global CSS variables in `/static/css/index.css`


### Formatting & Linting

These libraries are not including in the production venv, so install them with `pip install djhtml isort black pylint`.

- `djhtml ./templates`
- `isort ./`
- `black --line-length=140 --target-version=py310 .`
- `pylint -d C <module_name>`


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
RestartSec=20

[Install]
WantedBy=multi-user.target
```