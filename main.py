from subprocess import check_output, call

import yaml


def fetch_from_git():
    synced = False
    head_sha = check_output(["git", "rev-parse", "HEAD"])
    current_sha = check_output(["git", "rev-parse", "@{u}"])
    print(f"HEAD SHA: {head_sha}, current SHA: {current_sha}")

    if head_sha != current_sha:
        branch = check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        call(["git", "pull", "origin", f"{branch}"])
        synced = True
    return synced


def sync_docker_stacks():
    # For loop to search for yaml file in servers.
    # Then find any file with server.name = hostname.
    # If found, get through all stacks and do cd workdir and docker-compose up commands.
    yaml.load("")


def main():
    if fetch_from_git():
        sync_docker_stacks()


if __name__ == "__main__":
    main()
