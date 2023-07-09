import os
import json

APP_NAME = "rpcserv"


def locate_config() -> str:
    """Locate the config file."""

    if os.name == "nt":  # Windows
        appdata_dir = os.getenv("APPDATA")
        config_dir = os.path.join(appdata_dir, APP_NAME)
    else:  # Unix (Linux, macOS)
        home_dir = os.path.expanduser("~")
        xdg_config_home = os.getenv(
            "XDG_CONFIG_HOME", os.path.join(home_dir, ".config")
        )
        config_dir = os.path.join(xdg_config_home, APP_NAME)

    # Create the directory if it doesn't exist
    os.makedirs(config_dir, exist_ok=True)

    return config_dir


def get_config() -> dict:
    """Get the config."""

    config_dir = locate_config()
    config_file = os.path.join(config_dir, "config.json")

    # Create the config file if it doesn't exist
    if not os.path.isfile(config_file):
        with open(config_file, "w") as f:
            f.write("{}")

    # Read the config file
    with open(config_file, "r") as f:
        config = json.load(f)

    return config


def save_config(config: dict) -> None:
    """Save the config."""

    config_dir = locate_config()
    config_file = os.path.join(config_dir, "config.json")

    # Write the config file
    with open(config_file, "w") as f:
        json.dump(config, f, indent=4)
