import argparse
import os
import shutil
import socket
from subprocess import check_output, CalledProcessError

import yaml
import logging


def fetch_from_git():
    synced = False
    result = check_output(["git", "fetch", "origin"])
    logging.info(f"Running git-sync, fetch result: {result.decode('utf-8')}")
    head_sha = check_output(["git", "rev-parse", "HEAD"])
    current_sha = check_output(["git", "rev-parse", "@{u}"])
    logging.info(f"HEAD SHA: {head_sha}, current SHA: {current_sha}")

    if head_sha != current_sha:
        branch = check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode("utf-8").replace("\n", "")
        result = check_output(["git", "pull", "--rebase", "origin", f"{branch}"])
        logging.info(result.decode("utf-8"))
        synced = True
    return synced


def update_docker_stacks(yaml_content, command):
    if command is None or command == "":
        command = "docker compose"
    for stack_name in yaml_content.get("stacks"):
        stack = yaml_content.get("stacks").get(stack_name)
        workdir = stack.get("workdir")
        compose_file = stack.get("compose")
        if compose_file is None:
            compose_file = "docker-compose.yaml"
        if workdir is not None:
            try:
                env = stack.get("values")
                program = command.split(" ") + ["-f", compose_file, "up", "-d"]
                logging.info(f"Executing {program} with env: {env}")
                result = check_output(program, cwd=workdir, env=env).decode("utf-8").strip()
                if result != "":
                    logging.info(result)
            except (RuntimeError, CalledProcessError) as error:
                logging.error(f"Runtime Error occurred while executing:\n {error}")


def link_nginx_configs(content):
    if content.get("nginx") is not None:
        if content.get("nginx").get("config") is not None:
            nginx_config = content.get("nginx").get("config")
            source = nginx_config.get("provisioning")
            target = nginx_config.get("target")
            sites_enabled = nginx_config.get("sites-enabled")

            if not sites_enabled.endswith("/"):
                sites_enabled += "/"
            if target is not None and source is not None:
                # Backup old file because in next step it would be overwritten.
                if os.path.isfile(target):
                    shutil.move(target, target + ".bak")
                    logging.info(f"Moved {target} to {target}.bak (backup file).")

                # Overwrite nginx config file.
                shutil.copy(source, target)
                logging.info(f"Copied {source} to {target}.")

            if content.get("nginx").get("sites") is not None:
                nginx_sites = content.get("nginx").get("sites")
                for site_name in nginx_sites:
                    site = nginx_sites.get(site_name)
                    link = sites_enabled + site.get("name")
                    source = os.path.abspath(site.get("file"))
                    if os.path.realpath(link) != source:
                        if os.path.islink(link) or os.path.isfile(link):
                            os.remove(link)
                            logging.info(f"Deleted file/link: {link}")
                        os.symlink(source, link)
                        logging.info(f"Created link from {link} -> {source}.")


def execute_post_commands(post_commands):
    for command in post_commands:
        logging.info(f"Executing {command}")
        result = check_output(command.split(" ")).decode("utf-8").strip()
        if result != "":
            logging.info(result)


def find_yaml_config(args):
    # For loop to search for yaml file in servers.
    for file in walk_through_files(path=args.server_directory):
        content = yaml.safe_load(open(file))
        # Then find any file with server.name = hostname.
        if content is not None and content.get("server") is not None and content.get("server").get("name") is not None:
            name = content.get("server").get("name")
            command = content.get("server").get("compose-command")
            post_commands = content.get("server").get("post-check-commands")
            # If found, get through all stacks and do cd workdir and docker-compose up commands.
            if name == socket.gethostname():
                if not args.disable_docker:
                    update_docker_stacks(content, command)
                if args.enable_nginx_config:
                    link_nginx_configs(content)
                if post_commands is not None and len(post_commands) > 0:
                    execute_post_commands(post_commands)


def walk_through_files(path, file_extensions='.yaml,.yml'):
    for (dir_path, dir_names, filenames) in os.walk(path):
        for filename in filenames:
            for extension in file_extensions.split(","):
                if filename.endswith(extension):
                    yield os.path.join(dir_path, filename)


def main():
    logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
    parser = argparse.ArgumentParser(
        prog='docker-git-sync.py',
        description='Sync docker stacks with git repository.')
    parser.add_argument('-nc', '--enable-nginx-config', action='store_true', default=False,
                        help="enables nginx config linking/overwriting")
    parser.add_argument('-dd', '--disable-docker', action='store_true', default=False,
                        help="disable docker-compose to startup docker stacks")
    parser.add_argument('-up', '--start-up', action='store_true', default=False,
                        help="start the docker-compose anyways (without git change; useful for initial start)")
    parser.add_argument('-sd', '--server-directory', default="./servers", help="set path for server configurations.")
    args = parser.parse_args()
    if fetch_from_git() and (not args.disable_docker or args.enable_nginx_config) or args.start_up:
        find_yaml_config(args)


if __name__ == "__main__":
    main()
