# Install Airflow with Postgresql on custome paths in linux
_Consider rebooting the server after completing a step if it doesn't work_
I installed in the following paths:
* Installing airflow on /data/airflow
* Installing PostgreSQL on /data/postgres
## Create user
```sh
useradd airflow
```
## On /root/.bashrc
```sh
export AIRFLOW_HOME=/data/airflow
```
## PostgreSQL
follow the steps [here](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/selinux_users_and_administrators_guide/sect-managing_confined_services-postgresql-configuration_examples) to install Postgres on linux with different db paths.
Once installed, connect to postgres using psql (su - postgres first) and create Airflow DB and user.
```sql
CREATE DATABASE airflow_db;
CREATE USER airflow_user WITH PASSWORD 'some_password';
GRANT ALL PRIVILEGES ON DATABASE airflow_db TO airflow_user;
```
## Airflow
Switch to airflow user  (su - airflow)
And edit /home/airflow/.bash_profile file as following:
``` bash
# .bash_profile
# Get the aliases and functions
if [ -f ~/.bashrc ]; then
        . ~/.bashrc
fi
# User specific environment and startup programs
PATH=$PATH:$HOME/.local/bin
export PATH
export AIRFLOW_HOME=/data/airflow
export AIRFLOW_CONFIG=/data/airflow
```
Install airflow using pip install.
Use the connectors you need.
```py
pip install 'apache-airflow[cncf.kubernetes, docker, elasticsearch, ldap, mongo, microsoft.mssql, jdbc, postgres, crypto]'
```
> `crypto`  is used to encrypt passwords in connections
#### airflow.cfg
simply run the command airflow to create airflow.cfg
```sh
airflow
```
Next, edit cfg file with the following properties:
```
executor = LocalExecutor
sql_alchemy_conn = postgresql+psycopg2://airflow_user:some_password@localhost:5432/airflow_db
dags_folder = /data/airflow/dags
```
Run the following command to get the encryption key:
```py
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```	
Paste the result in the cfg file under:
```
fernet_key = Uasdflkj2340987435lkj-asdg=
```
### Init airflow
```sh
airflow db init
```
### Airflow Services
For airflow to start automatically after restart we need to create services.
#### airflow-scheduler.service
```sh
[Unit]
Description=Airflow scheduler daemon
After=network.target postgresql.service
Wants=postgresql.service
[Service]
PIDFile=/data/airflow/scheduler.pid
User=airflow
Group=airflow
Type=simple
ExecStart=/bin/bash -c 'export AIRFLOW_HOME=/data/airflow ; airflow scheduler --pid /data/airflow/scheduler.pid'
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID
Restart=on-failure
RestartSec=42s
PrivateTmp=true
[Install]
WantedBy=multi-user.target
```
#### airflow-webserver.service
```sh
[Unit]
Description=Airflow webserver daemon
After=network.target postgresql.service
Wants=postgresql.service
[Service]
PIDFile=/data/airflow/webserver.pid
User=airflow
Group=airflow
Type=simple
ExecStart=/bin/bash -c 'export AIRFLOW_HOME=/data/airflow ; airflow webserver --pid /data/airflow/webserver.pid'
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID
Restart=on-failure
RestartSec=42s
PrivateTmp=true
[Install]
WantedBy=multi-user.target
```
## Create a user to connect to airflow for the first time
su - airflow first:
```sh
airflow users create \
    --username admin \
    --firstname Eran \
    --lastname Hadad \
    --role Admin \
    --email eranh@harel-ins.co.il
```
## Configure TLS\SSL for secure connection
Fitst you need to generate a certificate (without a password).
Then in airflow.cfg check the following:
```sh
[webserver]
# The base url of your website as airflow cannot guess what domain or
# cname you are using. This is used in automated emails that
# airflow sends to point links to the right web server
base_url = https://servername:8080
# The ip specified when starting the web server
web_server_host = 0.0.0.0
# The port on which to run the web server
web_server_port = 8080
# Paths to the SSL certificate and key for the web server. When both are
# provided SSL will be enabled. This does not change the web server port.
web_server_ssl_cert = /data/airflow/servername.domainname.com.crt
# Paths to the SSL certificate and key for the web server. When both are
# provided SSL will be enabled. This does not change the web server port.
web_server_ssl_key = /data/airflow/servername.domainname.com.key
```
## Configure LDAP authentication
Then in airflow-webserver.cfg check the following:
```sh
"""Default configuration for the Airflow webserver"""
import os
from flask_appbuilder.security.manager import AUTH_LDAP
basedir = os.path.abspath(os.path.dirname(__file__))
WTF_CSRF_ENABLED = True
AUTH_TYPE = AUTH_LDAP
AUTH_LDAP_SERVER = "ldap://servername:3268"
AUTH_LDAP_BIND_USER = "CN=some_user,OU=Services,DC=company_name,DC=com"
AUTH_LDAP_BIND_PASSWORD = "some_password"
AUTH_LDAP_SEARCH = "DC=company_name,DC=com"
AUTH_LDAP_UID_FIELD = "sAMAccountName"
AUTH_LDAP_FIRSTNAME_FIELD = "givenName"
AUTH_LDAP_LASTTNAME_FIELD = "sn"
# Will allow user self registration
AUTH_USER_REGISTRATION = True
# The default user self registration role
AUTH_USER_REGISTRATION_ROLE = "Public"
# Config for Flask-Mail necessary for user self registration
MAIL_SERVER = 'servername.company_name.com'
# MAIL_USE_TLS = True
# MAIL_USERNAME = 'yourappemail@gmail.com'
# MAIL_PASSWORD = 'passwordformail'
MAIL_DEFAULT_SENDER = 'airflow@company_name.com'
```
