import datetime
import os
import socket
import threading
import tkinter as tk
from emoji import demojize
import sys
import json
from midi_controller import send_midi_notes


def read_notes_and_ports_from_file(file_path):
    with open(file_path, "r") as file:
        notes_and_ports_json = file.read()
        return json.loads(notes_and_ports_json)


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
        self.notes_and_ports = read_notes_and_ports_from_file(
            "./Music_informations/notes_and_ports.json"
        )

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
        self.sock.send(f"PASS {self.token}\r\n".encode("utf-8"))
        self.sock.send(f"NICK {self.nickname}\r\n".encode("utf-8"))
        self.sock.send(f"JOIN {self.channel}\r\n".encode("utf-8"))

    def get_port_for_note_or_none(self, note):
        print("get_port_for_note_or_none", note, type(note))
        if note is None:
            return None
        try:
            if note.isdigit() and int(note) in self.notes_and_ports.values():
                return int(note)
            note: str = note.upper()
            if len(note) == 1:
                note = f"{note}5"
            return self.notes_and_ports.get(str(note), None)

        except ValueError:
            return None

    def receive_message(self):
        while self.running:
            try:
                resp = self.sock.recv(2048).decode("utf-8")

                if resp.startswith("PING"):
                    self.respond_to_ping()
                elif len(resp) > 0:
                    self.handle_response(resp)

            except Exception as e:
                self.text_area.insert(tk.END, f"Error: {str(e)}")
                break

    def respond_to_ping(self):
        self.sock.send("PONG :tmi.twitch.tv\n".encode("utf-8"))
        self.sock.send("PONG\n".encode("utf-8"))

    def handle_response(self, resp: str):
        # Extract the message part from the response
        parts = resp.split(":", 2)
        if len(parts) >= 3 and "PRIVMSG" in resp:
            message = parts[2].strip()

            # Insert the message into the text area
            self.text_area.config(state=tk.NORMAL)
            # only print what is after the first # which is the channel name
            self.text_area.insert(
                tk.END,
                demojize(
                    f'[{datetime.datetime.now().strftime("%H:%M:%S")}]'
                    + resp.split("#", 1)[1]
                )
                + "\n",
            )
            self.text_area.config(state=tk.DISABLED)

            self.text_area.config(state=tk.DISABLED)
            if "PRIVMSG" in resp:
                self.parse_and_play_midi(message)

    def parse_and_play_midi(self, message: str):
        try:
            # Split the message into multiple parts based on commas
            message_list = message.split(" ")

            for message in message_list:
                message_parts = message.split(":")
                message_parts_count = len(message_parts)

                note_or_ports = message_parts[0]
                note_or_port_list = note_or_ports.split(",")

                velocity = int(message_parts[1]) if message_parts_count > 1 else None
                length = float(message_parts[2]) if message_parts_count > 2 else None

                ports = [
                    self.get_port_for_note_or_none(note_or_port)
                    for note_or_port in note_or_port_list
                ]

                if not ports:
                    return

                send_midi_notes(ports, velocity, length)

        except ValueError as e:
            print(f"Error parsing MIDI message: {e}")

    def send_message(self, msg):
        self.sock.send(f"PRIVMSG {self.channel} :{msg}\r\n".encode("utf-8"))

    def on_closing(self):
        self.running = False
        self.sock.close()
        self.master.destroy()
        sys.exit(0)
