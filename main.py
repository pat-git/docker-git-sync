import os
import socket
from subprocess import check_output

import yaml


def fetch_from_git():
    synced = False
    head_sha = check_output(["git", "rev-parse", "HEAD"])
    current_sha = check_output(["git", "rev-parse", "@{u}"])
    print(f"HEAD SHA: {head_sha}, current SHA: {current_sha}")

    if head_sha != current_sha:
        branch = check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        result = check_output(["git", "pull", "origin", f"{branch}"])
        print(result.decode("utf-8"))
        synced = True
    return synced


def update_docker_stacks(yaml_content, command):
    if command is None or command == "":
        command = "docker-compose"
    for stack_name in yaml_content.get("stacks"):
        stack = yaml_content.get("stacks").get(stack_name)
        workdir = stack.get("workdir")
        compose_file = stack.get("compose")
        if compose_file is None:
            compose_file = "docker-compose.yaml"
        if workdir is not None:
            try:
                result = check_output([command, "-f", compose_file, "up", "-d"], cwd=workdir)
                print(result.decode("utf-8"))
            except RuntimeError:
                print(f"Runtime Error occurred while executing {command} -f {compose_file} up -d")


def link_nginx_configs(content):
    pass


def find_yaml_config():
    # For loop to search for yaml file in servers.
    for file in walk_through_files(path="./servers"):
        content = yaml.safe_load(open(file))
        # Then find any file with server.name = hostname.
        if content is not None and content.get("server") is not None and content.get("server").get("name") is not None:
            name = content.get("server").get("name")
            command = content.get("server").get("compose-command")
            # If found, get through all stacks and do cd workdir and docker-compose up commands.
            if name == socket.gethostname():
                update_docker_stacks(content, command)
                link_nginx_configs(content)


def walk_through_files(path, file_extensions='.yaml,.yml'):
    for (dir_path, dir_names, filenames) in os.walk(path):
        for filename in filenames:
            for extension in file_extensions.split(","):
                if filename.endswith(extension):
                    yield os.path.join(dir_path, filename)


def main():
    if fetch_from_git() or True:
        find_yaml_config()


if __name__ == "__main__":
    main()
