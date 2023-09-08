import json


def read_json(file_path):
    with open(file_path, "r") as file:
        dict = file.read()
        return json.loads(dict)


class MusicTheory:
    def __init__(self) -> None:
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
        self.notes_and_ports: dict = read_json(
            "./Music_informations/notes_and_ports.json"
        )
        self.scales: dict = read_json("./Music_informations/scales_intervals.json")
        self.scales_list = list(self.scales.keys())

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

    def handle_ports_changes(self, scale, base_note, note_list):
        """
        This function is used to update the ports allowed to be played
        based on the scale and base note.

        If the scale and base note are not specified, all ports are allowed.

        """

        if len(scale) > 0 and len(base_note) > 0:
            matching_ports = self.get_matching_ports_for_notes(note_list)
            return sorted(matching_ports)
        else:
            return self.notes_and_ports.values()

    def get_matching_ports_for_notes(self, notes):
        matching_ports = []
        for note in notes:
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
        return matching_ports
