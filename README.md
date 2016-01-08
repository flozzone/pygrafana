# python grafana backend

This project aims to build a python backend for grafana. Grafana depends on go and other software
components, which are not easy to cross compile for embedded hardware. Due to its beautiful frontend which
relies on a quite simple API, I decided to write an API in python.

## installation

The current installation process is long and error prone. It will be improved in future releases.

### Preparing static files


Install a grafana release and copy the 'public' folder into /var/www/grafana:

Prepare a index.html at /var/www/grafana/public/index.html. You can retrieve a index.html
from a installed grafana:

    curl http://localhost:3000 -O index.html

Change it to your needs.

### Install pygrafana

    python setup.py sdist
    pip install dist/pygrafana-LATEST.tar.gz

After installing pygrafana, you can (and you'll need to) run the development webserver by simply calling the script

    pygrafana

This will do the database initialization, otherwise starting uwsgi without initializing the database will fail.
The development webserver will only provide the grafana API, not the static files it needs to run the frontend. These
are provided by the nginx webserver.

### Start uwsgi application server

    uwsgi --module pygrafana.app --callable app --master --socket 0.0.0.0:8889

### Configure nginx

    server {
        # serve index.html
        location /grafana {
            alias /var/www/grafana/public;
            index index.html;
        }
        # serve static files
        location /grafana/public {
            alias /var/www/grafana/public;
        }
        # serve api
        location /grafana/api {
            # used to remove trailing slash from grafana frontend
            rewrite ^/grafana/api/(.*)/$ /grafana/api/$1 break;
            include uwsgi_params;
            uwsgi_pass localhost:8889;

            uwsgi_param SCRIPT_NAME /grafana;
            uwsgi_modifier1 30;
        }
    }
    
And reload nginx.