# docker-git-sync
This simple python script allows to sync your docker stacks using a git repository (gitops repo).

Simply run the script using:
```sh
python3 docker-git-sync.py
```

The script also allows to sync the nginx config and nginx site config files (disabled by default).

To run the script to sync nginx config files simply enter:
```sh
sudo python3 docker-git-sync.py -nc -dd
```
You have to have root/sudo privileges because the nginx config is stored in ``/etc/nginx``.
It is recommended to not start the containers as root, therefore disable the docker-compose command execution using parameter ``-dd``.

## server configuration
For each configuration you have to specify a configuration yaml file.

Example configuration:
```yaml
server:
  name: "<your-server-hostname>"
  description: "Your server Hostname description"
  compose-command: "docker-compose"
stacks:
  example-hello-world:
    workdir: "./example/"
    compose: "docker-compose.yaml"
    values: {}
nginx:
  config:
    provisioning: "./nginx/nginx.conf"
    target: "/etc/nginx/nginx.conf"
    sites-enabled: "/etc/nginx/sites-enabled/"
  sites:
    test:
      name: "example.com"
      file: "./nginx/sites/example.com.conf"
      values: {}
```
It is important to set the hostname of your server in the "name" argument.
All servers which use the docker-git-sync script and have this specific hostname will start the specified docker stacks and sync the nginx config.

## cron jobs
You can also set up cron jobs to automatically start the sync script.

To run every minute: 
```cron
* * * * * python3 /home/user/repo/docker-git-sync.py >> /home/user/sync.log
```

Keep in mind to also sync nginx config (+sites) with a different user (root privileges):
```cron
* * * * * python3 /home/user/repo/docker-git-sync.py -nc -dd >> /home/user/sync-nginx.log
```