import argparse
import logging
import shutil
import socket
from pathlib import Path
from subprocess import CalledProcessError, check_output
from typing import Any

import yaml


def fetch_from_git() -> bool:
    result = check_output(["git", "fetch", "origin"])
    logging.info(f"Running git-sync, fetch result: {result.decode('utf-8')}")
    head_sha = check_output(["git", "rev-parse", "HEAD"])
    current_sha = check_output(["git", "rev-parse", "@{u}"])
    logging.info(f"HEAD SHA: {head_sha}, current SHA: {current_sha}")

    if head_sha != current_sha:
        branch = (
            check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            .decode("utf-8")
            .replace("\n", "")
        )
        result = check_output(["git", "pull", "--rebase", "origin", f"{branch}"])
        logging.info(result.decode("utf-8"))
        return True
    return False


def update_docker_stacks(
    yaml_content: dict[str, Any], command: str = "docker compose"
) -> None:
    for stack_name in yaml_content.get("stacks"):
        stack = yaml_content.get("stacks").get(stack_name)
        workdir = stack.get("workdir")
        compose_file = stack.get("compose") or "docker-compose.yaml"
        if not workdir:
            continue
        env = stack.get("values")
        program = command.split(" ") + ["-f", compose_file, "up", "-d"]
        logging.info(f"Executing {program} with env: {env}")
        try:
            result = check_output(program, cwd=workdir, env=env).decode("utf-8").strip()
        except (RuntimeError, CalledProcessError) as error:
            logging.error(f"Runtime Error occurred while executing:\n {error}")
            return
        if result != "":
            logging.info(result)


def link_nginx_configs(content: dict[str, Any]) -> None:
    if not content.get("nginx"):
        return
    if not content["nginx"].get("config"):
        return

    nginx_config = content["nginx"]["config"]
    source = nginx_config.get("provisioning")
    target = nginx_config.get("target")
    sites_enabled = nginx_config.get("sites-enabled")

    if not sites_enabled.endswith("/"):
        sites_enabled += "/"
    if target and source:
        # Backup old file because in next step it would be overwritten.
        if Path(target).is_file():
            shutil.move(target, target + ".bak")
            logging.info(f"Moved {target} to {target}.bak (backup file).")

        # Overwrite nginx config file.
        shutil.copy(source, target)
        logging.info(f"Copied {source} to {target}.")

    nginx_sites = content["nginx"].get("sites")
    if not nginx_sites:
        return
    for site_name in nginx_sites:
        site = nginx_sites.get(site_name)
        link = Path(sites_enabled) / site.get("name")
        source = Path(site.get("file")).resolve()
        if link.resolve() == source:
            continue
        if link.is_symlink() or link.is_file():
            link.unlink()
            logging.info(f"Deleted file/link: {link}")
        link.symlink_to(source)
        logging.info(f"Created link from {link} -> {source}.")


def execute_post_commands(post_commands: list[str]) -> None:
    for command in post_commands:
        logging.info(f"Executing {command}")
        result = check_output(command.split(" ")).decode("utf-8").strip()
        if result:
            logging.info(result)


def find_yaml_config(args) -> None:
    # For loop to search for yaml file in servers.
    server_directory = Path(args.server_directory)
    for file in server_directory.rglob("*.y*ml"):
        content = yaml.safe_load(file.open())
        # Then find any file with server.name = hostname.
        if (
            content is None
            or content.get("server") is None
            or content.get("server").get("name") is None
        ):
            continue
        name = content.get("server").get("name")
        command = content.get("server").get("compose-command")
        post_commands = content.get("server").get("post-check-commands")
        # If found, get through all stacks and do cd workdir and docker-compose up commands.
        if name != socket.gethostname():
            continue
        if not args.disable_docker:
            update_docker_stacks(content, command)
        if args.enable_nginx_config:
            link_nginx_configs(content)
        if post_commands is not None and len(post_commands) > 0:
            execute_post_commands(post_commands)


def main():
    logging.basicConfig(
        format="%(asctime)s - %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
        level=logging.INFO,
    )
    parser = argparse.ArgumentParser(
        prog="docker-git-sync.py", description="Sync docker stacks with git repository."
    )
    parser.add_argument(
        "-nc",
        "--enable-nginx-config",
        action="store_true",
        default=False,
        help="enables nginx config linking/overwriting",
    )
    parser.add_argument(
        "-dd",
        "--disable-docker",
        action="store_true",
        default=False,
        help="disable docker-compose to startup docker stacks",
    )
    parser.add_argument(
        "-up",
        "--start-up",
        action="store_true",
        default=False,
        help="start the docker-compose anyways (without git change; useful for initial start)",
    )
    parser.add_argument(
        "-sd",
        "--server-directory",
        default="./servers",
        help="set path for server configurations.",
    )
    args = parser.parse_args()
    if (
        fetch_from_git()
        and (not args.disable_docker or args.enable_nginx_config)
        or args.start_up
    ):
        find_yaml_config(args)


if __name__ == "__main__":
    main()
