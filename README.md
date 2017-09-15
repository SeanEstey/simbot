# Setup Instructions

#### Clone repository
```
git clone https://github.com/SeanEstey/flask_celery_skeleton --branch <b_name>
cd flask_celery_skeleton
```

#### Ubuntu/Python Packages

Follow instructions in requirements/pkg_list.txt and requirements/requirements.txt

#### Run setup

`python setup.py`

This will copy nginx virtual host file and setup logrotate.d

#### MongoDB

Create "db_auth.py" in Bravo root directory:  

```
user = "db_user"
password = "db_pw"
```

# Run Instructions

Start RabbitMQ daemon:

`$ rabbitmqctl start_app`

Run app:

`python run.py`

Arguments

-Start with celerybeat:

`-c, --celerybeat` 

-Start in debug mode:

`-d, --debug`

# Shutdown Instructions

If running in foreground, kill with CTRL+C. This will kill Celery workers.

If running in background, get pid:

`$ps aux | grep -m 1 'python main.py' | awk '{print $2}'`

Now kill it using that PID:

`$kill -9 <PID>`

(May need to run twice)

# Monitoring

Monitor Celery worker(s) with Flower:

pip install flower

To run it:

flower --url_prefix=flower --basic_auth=user1:password1

To access it remotely through the browser, add the following to the nginx virtual_host file:

    server {
        listen 80;
        server_name ip_or_hostname.ca;
 
        location /flower/ {
            rewrite ^/flower/(.*)$ /$1 break;
            proxy_pass http://127.0.0.1:5555;
            proxy_set_header Host $host;
        }

Restart nginx:

service nginx restart

It should now be accessible and secured via http://ip_or_hostname.ca/flower

# Notes

To free memory not released by abberant python/celery processes:

$ sync && echo 3 | sudo tee /proc/sys/vm/drop_caches
