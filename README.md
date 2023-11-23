# BLOGGER.

A simple blog written with Flask. It currently features,

- Authentication
- Flash messages
- Tagging for posts
- File attachments
- CKEditor for a WYSIWYG blogging experience with image upload support. 
    - Video and other file types can be embedded by clicking the source button - just upload file attachments, and reference them.

Features still missing,

- Cascade deletions for tags and files
- Decoupled configs
- Commenting on posts


## Preview

See a collection of screenshots [here](resources/README.md).

## Set up

This site was developed against Python 3.10.12, so you should first have that version of Python installed. Other versions (3.11) probably work too.

### Windows
```
git clone https://github.com/skwzrd/blogger.git
cd blogger
py -m venv venv
venv\Scripts\activate.bat
py -m pip install -r requirements.txt
py app.py
```

### Linux
```
git clone https://github.com/skwzrd/blogger.git
cd blogger
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
python3 app.py
```


## Site Configurations

If you want to go beyond just demoing this code,

- Configure the variables at the top of the file `app.py`.
- Delete the current database
- Create a new user with solid credentials (see `app.build_db` for how to do this)


## Formatting

- `djhtml .`
- `isort .`


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
ExecStart=/home/user1/venv/bin/gunicorn -w 2 -b 127.0.0.1:8080 'app:app'

Type=simple
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```