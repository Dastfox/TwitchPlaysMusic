import datetime
import os
import re
import socket
import threading
import tkinter as tk
from emoji import demojize
import sys
import json
from midi_controller import send_midi_notes


def read_json(file_path):
    with open(file_path, "r") as file:
        dict = file.read()
        return json.loads(dict)


class ChatClient:
    def __init__(self, master, server, port, nickname, token, channel):
        self.current_notes = []  # Notes that are currently being played
        self.waiting_notes = []  # Notes that are waiting to be played
        self.master = master
        self.server = server
        self.port = port
        self.nickname = nickname
        self.token = token
        self.channel = channel
        self.sock = None
        self.running = True
        self.notes_and_ports = read_json("./Music_informations/notes_and_ports.json")
        self.scales: dict = read_json("./Music_informations/scales_intervals.json")
        # GUI
        self.max_beats = tk.IntVar()
        self.chords_allowed = tk.BooleanVar()
        self.scale = tk.StringVar()
        self.base_note = tk.StringVar()

        self.scales_list = list(self.scales.keys())
        self.full_note_list = [
            "C",
            "C#",
            "D",
            "D#",
            "E",
            "F",
            "F#",
            "G",
            "G#",
            "A",
            "A#",
            "B",
        ]

        self.note_list = self.full_note_list
        self.base_note.set(self.note_list[0])

        master.title("Twitch plays music")

        # Configure the grid
        master.columnconfigure(0, minsize=50, weight=1)
        master.rowconfigure(0, minsize=50, weight=1)

        self.text_area = tk.Text(master)
        self.text_area.grid(row=0, column=0, sticky="nsew")

        self.max_beats_label = tk.Label(master, text="Max number of beats")
        self.max_beats_label.grid(row=1, column=0, sticky="w")

        self.max_beats_entry = tk.Entry(master, textvariable=self.max_beats)
        self.max_beats_entry.grid(row=2, column=0, sticky="w")

        self.chords_allowed_check = tk.Checkbutton(
            master, text="Allow chords", variable=self.chords_allowed
        )
        self.chords_allowed_check.grid(row=3, column=0, sticky="w")

        self.max_beats_label = tk.Label(master, text="Scale")
        self.max_beats_label.grid(row=4, column=0, sticky="w")

        self.scale_menu = tk.OptionMenu(master, self.scale, *self.scales_list)
        self.scale_menu.grid(row=5, column=0, sticky="w")

        self.max_beats_label = tk.Label(master, text="Base note")
        self.max_beats_label.grid(row=6, column=0, sticky="w")

        self.base_note_menu = tk.OptionMenu(
            master, self.base_note, *self.full_note_list
        )
        self.base_note_menu.grid(row=7, column=0, sticky="w")

        self.scale.trace("w", self.option_changed)
        self.base_note.trace("w", self.option_changed)

        # New Listbox for displaying note list
        self.note_listbox = tk.Listbox(master)
        self.note_listbox.grid(row=8, column=0, sticky="w")
        for note in self.note_list:
            self.note_listbox.insert(tk.END, note)

        try:
            self.init_socket()
            threading.Thread(target=self.receive_message, daemon=True).start()

        except Exception as e:
            self.text_area.insert(tk.END, f"Failed to connect to the server: {str(e)}")

        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        def __init__(self):
            self.current_notes = []  # Notes that are currently being played
            self.waiting_notes = []  # Notes that are waiting to be played

        def note_started(self, note):
            self.waiting_notes.remove(note)
            self.current_notes.append(note)

    def note_stopped(self, note):
        self.current_notes.remove(note)

    def init_socket(self):
        self.sock = socket.socket()
        self.sock.connect((self.server, self.port))
        self.sock.send(f"PASS {self.token}\r\n".encode("utf-8"))
        self.sock.send(f"NICK {self.nickname}\r\n".encode("utf-8"))
        self.sock.send(f"JOIN {self.channel}\r\n".encode("utf-8"))

    def get_port_for_note_or_none(self, note):
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
            if self.is_message_valid(message):
                # Insert the message into the text area
                self.text_area.config(state=tk.NORMAL)
                # only print what is after the first # which is the channel name
                self.text_area.insert(
                    tk.END,
                    demojize(
                        f'[{datetime.datetime.now().strftime("%H:%M:%S")}]'
                        + resp.split("#", 1)[1]
                    ),
                )
                self.text_area.config(state=tk.DISABLED)

                self.text_area.config(state=tk.DISABLED)

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

                if ports == [None]:
                    continue

                send_midi_notes(
                    ports, velocity, length, self.chords_allowed_check.get()
                )

        except ValueError as e:
            print(f"Error parsing MIDI message: {e}")

    def send_message(self, msg):
        self.sock.send(f"PRIVMSG {self.channel} :{msg}\r\n".encode("utf-8"))

    def on_closing(self):
        self.running = False
        self.sock.close()
        self.master.destroy()
        sys.exit(0)

    def option_changed(self, *args):
        if len(self.scale.get()) > 0 and len(self.base_note.get()) > 0:
            self.note_list = self.get_notes_in_scale(
                self.scale.get(), self.base_note.get()
            )
            self.note_listbox.delete(0, tk.END)
            for note in self.note_list:
                self.note_listbox.insert(tk.END, note)
        else:
            self.note_list = self.full_note_list

    def get_notes_in_scale(self, scale, base_note):
        base_index = self.full_note_list.index(base_note)
        scale_intervals = self.scales[scale]

        notes_in_scale = []
        for interval in scale_intervals:
            base_index = (base_index + interval) % len(self.full_note_list)
            notes_in_scale.append(self.full_note_list[base_index])

        # Move the last element to the beginning
        last_note = notes_in_scale.pop()
        notes_in_scale.insert(0, last_note)

        return notes_in_scale

    def is_message_valid(self, message: str) -> bool:
        pattern = r"^([A-Ga-g0-9#]+(,[A-Ga-g0-9#]+)*(:[0-9]+(:[0-9]+(\.[0-9]+)?)?)?( [A-Ga-g0-9#]+(,[A-Ga-g0-9#]+)*(:[0-9]+(:[0-9]+(\.[0-9]+)?)?)?)*$)"

        return bool(re.match(pattern, message))
