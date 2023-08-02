import os
import tkinter as tk
from chat_client import ChatClient
import logging_config
import dotenv

dotenv.load_dotenv()


def main():
    logging_config.setup_logging()
    server = os.getenv("server")
    port = int(os.getenv("port"))
    nickname = os.getenv("nickname")
    token = os.getenv("token")
    channel = os.getenv("channel")

    root = tk.Tk()
    client = ChatClient(root, server, port, nickname, token, channel)
    root.mainloop()


if __name__ == "__main__":
    main()
