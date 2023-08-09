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
import mido
import dotenv

##########################
# UTILS FUNCTIONS ########
##########################


def write_to_env(key, value):
    with open(".env", "r+") as file:
        # Write the key-value pair to the .env file
        dotenv.set_key(file, key, value)


def read_json(file_path):
    with open(file_path, "r") as file:
        dict = file.read()
        return json.loads(dict)


def fetch_env_vars():
    # Load the environment variables from .env file
    dotenv.load_dotenv()
    server = os.getenv("SERVER", "irc.chat.twitch.tv")
    port = int(os.getenv("PORT", 6667))
    token = os.getenv("TOKEN", "oauth:8avli6uj6lllpblk0akdomwahbts45")
    channel = os.getenv("CHANNEL", "#dastou")
    nickname = os.getenv("NICKNAME", "dastou")

    return server, port, token, channel, nickname


##########################
# CHAT CLIENT CLASS ######
##########################
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

        # GUI variables
        self.midi_port = tk.StringVar()
        self.max_beats = tk.IntVar()
        self.chords_allowed = tk.BooleanVar()
        self.scale = tk.StringVar()
        self.base_note = tk.StringVar()
        self.midi_ports_list = mido.get_output_names()
        if self.midi_ports_list:
            self.midi_port.set(self.midi_ports_list[-1])
        else:
            self.midi_port.set("No MIDI Ports Available")

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
        self.ports_allowed = list(self.notes_and_ports.values())

        self.note_list = self.full_note_list
        self.base_note.set(self.note_list[0])

        self.chords_allowed.set(True)

        ############
        # GUI ######
        ############

        master.title("Twitch Plays Music")

        # Create frames to organize the layout
        chat_frame = tk.Frame(master)
        chat_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        controls_frame = tk.Frame(master)
        controls_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        queue_frame = tk.Frame(master)
        queue_frame.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")

        # Text Area ; Chat frame
        self.text_area = tk.Text(chat_frame, wrap=tk.WORD)
        self.text_area.pack(expand=True, fill=tk.BOTH)

        # Label and Entry for Max Beats ; Controls frame
        max_beats_frame = tk.Frame(controls_frame)
        max_beats_frame.pack(pady=5)
        self.max_beats_label = tk.Label(max_beats_frame, text="Max number of beats:")
        self.max_beats_label.pack(side=tk.LEFT)
        self.max_beats_entry = tk.Entry(max_beats_frame, textvariable=self.max_beats)
        self.max_beats_entry.pack(side=tk.LEFT)

        # Checkbox for Chords Allowed ; Controls frame
        self.chords_allowed_check = tk.Checkbutton(
            controls_frame, text="Allow chords", variable=self.chords_allowed
        )
        self.chords_allowed_check.pack(pady=5)

        # Scale selection ; Controls frame
        scale_frame = tk.Frame(controls_frame)
        scale_frame.pack(pady=5)
        scale_label = tk.Label(scale_frame, text="Scale:")
        scale_label.pack(side=tk.LEFT)
        self.scale_menu = tk.OptionMenu(scale_frame, self.scale, *self.scales_list)
        self.scale_menu.pack(side=tk.LEFT)

        # Base note selection ; Controls frame
        base_note_frame = tk.Frame(controls_frame)
        base_note_frame.pack(pady=5)
        base_note_label = tk.Label(base_note_frame, text="Base note:")
        base_note_label.pack(side=tk.LEFT)
        self.base_note_menu = tk.OptionMenu(
            base_note_frame, self.base_note, *self.full_note_list
        )
        self.base_note_menu.pack(side=tk.LEFT)

        # Note list ; Controls frame
        self.note_listbox_label = tk.Label(controls_frame, text="Available Notes:")
        self.note_listbox_label.pack()
        self.note_listbox = tk.Listbox(controls_frame)
        self.note_listbox.pack(expand=True, fill=tk.BOTH)
        for note in self.note_list:
            self.note_listbox.insert(tk.END, note)

        # MIDI port selection ; Controls frame
        midi_port_frame = tk.Frame(controls_frame)
        midi_port_frame.pack(pady=5)
        self.midi_port_label = tk.Label(midi_port_frame, text="MIDI Port:")
        self.midi_port_label.pack(side=tk.LEFT)
        self.midi_port_menu = tk.OptionMenu(
            midi_port_frame, self.midi_port, *self.midi_ports_list
        )
        self.midi_port_menu.pack(side=tk.LEFT)

        # Config button ; Controls frame
        config_button = tk.Button(
            controls_frame, text="Config", command=self.show_config_modal
        )
        config_button.pack(pady=5)

        # Queue list ; current notes frameX

        ##############
        # end of GUI #
        ##############

        self.scale.trace("w", self.option_changed)
        self.base_note.trace("w", self.option_changed)

        try:
            self.init_socket()
            threading.Thread(target=self.receive_message, daemon=True).start()

        except Exception as e:
            self.text_area.insert(tk.END, f"Failed to connect to the server: {str(e)}")

        master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def note_received(self, note):
        self.waiting_notes.append(note)

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
            if len(note) == 1 or note[1] == "#":
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

    def parse_message_parts(self, message_parts):
        note_or_ports = message_parts[0]
        note_or_port_list = note_or_ports.split(",")
        velocity = int(message_parts[1]) if len(message_parts) > 1 else None
        length = float(message_parts[2]) if len(message_parts) > 2 else None

        return note_or_port_list, velocity, length

    def filter_ports(self, note_or_port_list):
        ports = [
            self.get_port_for_note_or_none(note_or_port)
            for note_or_port in note_or_port_list
        ]
        print("Ports:", ports)
        return [port for port in ports if port in self.ports_allowed]

    def send_midi_with_timeout(self, ports, velocity, length):
        def send_midi_wrapper():
            print("Sending MIDI...", ports)
            send_midi_notes(
                ports,
                velocity,
                length,
                self.chords_allowed.get(),
                self.midi_port.get(),
            )

        event = threading.Event()
        t = threading.Thread(target=lambda: (send_midi_wrapper(), event.set()))
        t.start()

        if not event.wait(timeout=5):
            print("Warning: MIDI sending timed out!")

    def parse_and_play_midi(self, message: str):
        try:
            message_list = message.split(" ")

            for message in message_list:
                message_parts = message.split(":")
                note_or_port_list, velocity, length = self.parse_message_parts(
                    message_parts
                )
                ports = self.filter_ports(note_or_port_list)

                if ports == [None] or not ports:
                    continue
                print(f"Playing {ports} with velocity {velocity} and length {length}")
                self.send_midi_with_timeout(ports, velocity, length)

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

            matching_ports = []
            for note in self.note_list:
                if "#" in note:
                    matching_ports += [
                        self.notes_and_ports[key]
                        for key in self.notes_and_ports.keys()
                        if note in key[:2]
                    ]
                else:
                    matching_ports += [
                        self.notes_and_ports[key]
                        for key in self.notes_and_ports.keys()
                        if note == key[0] and "#" not in key
                    ]
            self.ports_allowed = sorted(matching_ports)

        else:
            self.note_list = self.full_note_list
            self.ports_allowed = self.notes_and_ports.values()

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
        if not re.match(pattern, message):
            print("Invalid message format")
        return bool(re.match(pattern, message))

    def open_settings_modal(self):
        self.settings_window = tk.Toplevel(self.master)
        self.settings_window.title("Settings")

        server_label = tk.Label(self.settings_window, text="Server:")
        server_label.grid(row=0, column=0)
        self.server_entry = tk.Entry(self.settings_window)
        self.server_entry.insert(0, self.server)
        self.server_entry.grid(row=0, column=1)

        port_label = tk.Label(self.settings_window, text="Port:")
        port_label.grid(row=1, column=0)
        self.port_entry = tk.Entry(self.settings_window)
        self.port_entry.insert(0, self.port)
        self.port_entry.grid(row=1, column=1)

        token_label = tk.Label(self.settings_window, text="Token:")
        token_label.grid(row=2, column=0)
        self.token_entry = tk.Entry(self.settings_window)
        self.token_entry.insert(0, self.token)
        self.token_entry.grid(row=2, column=1)

        channel_label = tk.Label(self.settings_window, text="Channel:")
        channel_label.grid(row=3, column=0)
        self.channel_entry = tk.Entry(self.settings_window)
        self.channel_entry.insert(0, self.channel)
        self.channel_entry.grid(row=3, column=1)

        nickname_label = tk.Label(self.settings_window, text="Nickname:")
        nickname_label.grid(row=4, column=0)
        self.nickname_entry = tk.Entry(self.settings_window)
        self.nickname_entry.insert(0, self.nickname)
        self.nickname_entry.grid(row=4, column=1)

        save_button = tk.Button(
            self.settings_window, text="Save", command=self.save_settings
        )
        save_button.grid(row=6, column=0, columnspan=2)

    def save_settings(self):
        self.server = self.server_entry.get()
        write_to_env("SERVER", self.server)
        write_to_env("PORT", self.port)
        write_to_env("TOKEN", self.token)
        write_to_env("CHANNEL", self.channel)
        write_to_env("NICKNAME", self.nickname)

        self.settings_window.destroy()

    def show_config_modal(self):
        modal = ConfigModal(self.master, self)
        self.master.wait_window(modal.top)


##########################
# Config Modal           #
##########################
class ConfigModal:
    def __init__(self, parent, chat_client):
        self.top = tk.Toplevel(parent)
        self.chat_client = chat_client

        self.server = tk.StringVar(value=os.getenv("server"))
        self.port = tk.StringVar(value=os.getenv("port"))
        self.nickname = tk.StringVar(value=os.getenv("nickname"))
        self.token = tk.StringVar(value=os.getenv("token"))
        self.channel = tk.StringVar(value=os.getenv("channel"))

        tk.Label(self.top, text="Server:").pack()
        tk.Entry(self.top, textvariable=self.server).pack()

        tk.Label(self.top, text="Port:").pack()
        tk.Entry(self.top, textvariable=self.port).pack()

        tk.Label(self.top, text="Nickname:").pack()
        tk.Entry(self.top, textvariable=self.nickname).pack()

        tk.Label(self.top, text="Token:").pack()
        tk.Entry(self.top, textvariable=self.token).pack()

        tk.Label(self.top, text="Channel:").pack()
        tk.Entry(self.top, textvariable=self.channel).pack()

        tk.Button(self.top, text="OK", command=self.validate).pack()

    def validate(self):
        dotenv.set_key(".env", "server", self.server.get())
        dotenv.set_key(".env", "port", self.port.get())
        dotenv.set_key(".env", "nickname", self.nickname.get())
        dotenv.set_key(".env", "token", self.token.get())
        dotenv.set_key(".env", "channel", self.channel.get())
        self.top.destroy()
