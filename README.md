# docker-git-sync
This simple python script allows to sync your docker stacks using a git repository (gitops repo).

Simply run the script using:
```sh
# Execute script with default parameters.
python3 docker-git-sync.py

# Display help.
python3 docker-git-sync.py -h
```

The script also allows to sync the nginx config and nginx site config files (disabled by default).

To run the script to sync nginx config files simply enter:
```sh
# Execute with nginx-config sync enabled and docker-compose disabled.
sudo python3 docker-git-sync.py -nc -dd
```
You have to have root/sudo privileges because the nginx config is stored in ``/etc/nginx``.
It is recommended to not start the containers as root, therefore disable the docker-compose command execution using parameter ``-dd``.

### Initial startup
You can also start your stacks without any git change (for example on initial server setup or on testing purposes).
To do this just enter the following command:

```sh
# Execute script with default parameters + initial startup.
python3 docker-git-sync.py -up

# Execute with nginx-config sync enabled and docker-compose disabled + initial startup.
sudo python3 docker-git-sync.py -up -nc -dd
```
The ``-up`` parameter will simply skip the git check and execute the commands to sync the docker containers and the nginx config.

## Server configuration
For each server (hostname) you have to specify a configuration yaml file.

Example configuration:
```yaml
server:
  name: "your-server-hostname"
  description: "Your server Hostname description"
  compose-command: "docker compose"
  post-check-commands: []
stacks:
  example-hello-world:
    workdir: "./example/hello-world/"
    compose: "docker-compose.yaml"
    values: {}
  example-ubuntu:
    workdir: "./example/ubuntu"
    compose: "docker-compose.yaml"
    values:
      IMAGE_TAG: "22.04"
nginx:
  config:
    provisioning: "./nginx/nginx.conf"
    target: "/etc/nginx/nginx.conf"
    sites-enabled: "/etc/nginx/sites-enabled/"
  sites:
    test:
      name: "example.com"
      file: "./nginx/sites/example.com.conf"
```
It is important to set the hostname of your server in the "name" argument.
All servers which use the docker-git-sync script and have this specific hostname will start the specified docker stacks and sync the nginx config.

You can also set env variables for the process the docker compose command gets executed.
Just add them as key-value pairs in the "values" parameter of your stack.
The env variable can then be accessed in the docker-compose.yaml using ``${YOUR_VARIABLE_NAME}``.
## Cron jobs
You can also set up cron jobs to automatically start the sync script.

To run every minute (and store output in sync.log): 
```cron
* * * * * cd /home/user/repo/ && python3 docker-git-sync.py >> /home/user/git-sync.log 2>&1
```

You can also sync nginx config (+sites) with a different user (root privileges):
```cron
* * * * * cd /home/user/repo/ && python3 docker-git-sync.py -nc -dd >> /home/user/git-sync.log 2>&1
```
**Keep in mind that this will be run as root user and may be insecure and dangerous to use. Use this at your own risk**.