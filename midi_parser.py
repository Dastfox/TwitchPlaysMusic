class MIDI_Parser:
    def __init__(self):
        print("MIDI Parser initialized")
        self.max_beats = lambda: -1  # Placeholder for max_beats

    def print(self, _print: str):
        print(_print)

    def parse_message(
        self,
        message: str,
        notes_and_ports: dict = {},
        ports_allowed: list = [],
    ):
        print("Parsing message: ")
        message_list = message.split(" ")
        print(message_list)
        midi_data = []
        total_beats_played = 0

        for message in message_list:
            message_parts = message.split(":")
            note_or_port_list, velocities, lengths = self.parse_message_parts(
                message_parts
            )
            print(note_or_port_list, velocities, lengths)

            # Update total beats
            total_beats_played += sum(lengths) if lengths else 1

            # Check max beats
            if self.max_beats() != -1 and total_beats_played > self.max_beats():
                break

            ports = self.filter_ports(note_or_port_list, ports_allowed, notes_and_ports)

            # Collect MIDI data for later processing
            midi_data.append((ports, velocities, lengths))

        print("Parsed MIDI data: " + str(midi_data, total_beats_played))
        return midi_data, total_beats_played

    def parse_message_parts(self, message_parts):
        note_or_ports = message_parts[0]
        note_or_port_list = note_or_ports.split(",")

        # Convert velocities and lengths to lists
        lengths = (
            [float(length) for length in message_parts[1].split(",")]
            if len(message_parts) > 1
            else [None] * len(note_or_port_list)
        )
        velocities = (
            [int(velocity) for velocity in message_parts[2].split(",")]
            if len(message_parts) > 2
            else [None] * len(note_or_port_list)
        )

        # Adjust lengths and velocities to match note_or_port_list size if needed
        if len(lengths) < len(note_or_port_list):
            lengths += [lengths[-1]] * (len(note_or_port_list) - len(lengths))

        if len(velocities) < len(note_or_port_list):
            velocities += [velocities[-1]] * (len(note_or_port_list) - len(velocities))

        return note_or_port_list, velocities, lengths

    def filter_ports(self, note_or_port_list, ports_allowed=None, notes_and_ports=None):
        ports = [
            self.get_port_for_note_or_none(note_or_port, notes_and_ports)
            if note_or_port != "X"
            else "X"
            for note_or_port in note_or_port_list
        ]
        return [port for port in ports if port in ports_allowed or port == "X"]

    def get_port_for_note_or_none(self, note_or_port, notes_and_ports: dict):
        if note_or_port is None:
            return None
        try:
            if note_or_port.isdigit() and int(note_or_port) in notes_and_ports.values():
                return int(note_or_port)
            note_or_port: str = note_or_port.upper()
            if len(note_or_port) == 1 or note_or_port[1] == "#":
                note_or_port = f"{note_or_port}5"
            return notes_and_ports.get(str(note_or_port), None)

        except ValueError:
            return None

    def get_note_for_port_or_none(self, port, notes_and_ports: dict):
        # note is a letter with possiblly a # and is a key or notes_and_ports
        for note, port_value in notes_and_ports.items():
            if port_value == port:
                return note
