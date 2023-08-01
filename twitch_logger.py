import os
import socket
import threading
import logging
import tkinter as tk
from emoji import demojize
import dotenv
import sys
import signal

dotenv.load_dotenv()

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s — %(message)s',
                    datefmt='%Y-%m-%d_%H:%M:%S',
                    handlers=[logging.FileHandler('chat.log', encoding='utf-8')])


class ChatClient:

    def __init__(self, master, server, port, nickname, token, channel):
        self.master = master
        self.server = server
        self.port = port
        self.nickname = nickname
        self.token = token
        self.channel = channel
        self.sock = None
        self.running = True

        master.title("Chat client")

        # Configure the grid
        master.columnconfigure(0, minsize=50, weight=1)
        master.rowconfigure(0, minsize=50, weight=1)

        self.text_area = tk.Text(master)
        self.text_area.grid(row=0, column=0, sticky="nsew")

        try:
            self.init_socket()
            threading.Thread(target=self.receive_message, daemon=True).start()

        except Exception as e:
            self.text_area.insert(tk.END, f"Failed to connect to the server: {str(e)}")

        master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def init_socket(self):
        self.sock = socket.socket()
        self.sock.connect((self.server, self.port))
        self.sock.send(f"PASS {self.token}\r\n".encode('utf-8'))
        self.sock.send(f"NICK {self.nickname}\r\n".encode('utf-8'))
        self.sock.send(f"JOIN {self.channel}\r\n".encode('utf-8'))

    def receive_message(self):
        while self.running:
            try:
                if not self.running:
                    break
                resp = self.sock.recv(2048).decode('utf-8')

                if resp.startswith('PING'):
                    self.sock.send("PONG :tmi.twitch.tv\n".encode('utf-8'))
                    self.sock.send("PONG\n".encode('utf-8'))
                elif len(resp) > 0:
                    
                    self.text_area.config(state=tk.NORMAL)  # Set state to normal before inserting text
                    self.text_area.insert(tk.END, demojize(resp))
                    self.text_area.config(state=tk.DISABLED)  # Set state to disabled after inserting text
                


            except Exception as e:
                self.text_area.insert(tk.END, f"Error: {str(e)}")
                break          
            
        print("post while", self.running)
                
        

    def send_message(self, msg):
        self.sock.send(f"PRIVMSG {self.channel} :{msg}\r\n".encode('utf-8'))

    def on_closing(self):
        self.running = False
        self.sock.close()  # It's a good practice to close the socket before exiting
        self.master.destroy()
        print("Closing", self.running)
        sys.exit(0)  # exit the program
        


def main():
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
