import os
import tkinter as tk
from chat_client import ChatClient
import logging_config
import dotenv
from dotenv import load_dotenv, set_key

dotenv.load_dotenv()


def write_to_env(key, value):
    with open(".env", "r+") as file:
        # Write the key-value pair to the .env file
        set_key(file, key, value)


def fetch_env_vars():
    # Load the environment variables from .env file
    load_dotenv()
    server = os.getenv("SERVER")
    port = int(os.getenv("PORT"))
    token = os.getenv("TOKEN")
    channel = os.getenv("CHANNEL")
    nickname = os.getenv("NICKNAME")

    return server, port, token, channel, nickname


def main():
    logging_config.setup_logging()

    server, port, token, channel, nickname = fetch_env_vars()

    # If any variable is not found in .env, open the settings modal
    if not all([server, port, token, channel, nickname]):
        client.open_settings_modal()

    root = tk.Tk()
    client = ChatClient(root, server, port, nickname, token, channel)
    root.mainloop()


if __name__ == "__main__":
    main()
