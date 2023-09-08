import os
import mido
import time
import dotenv

dotenv.load_dotenv()

# Default MIDI values
NOTE = 60
VELOCITY = 64
NOTE_LENGTH = 1


def send_midi_notes(
    note_list: list,
    velocities: list = None,
    note_lengths: list = None,
    chords_allowed=True,
    midi_port=None,
    max_beats=4,
):
    print(locals())

    if velocities is None:
        velocities = [VELOCITY] * len(note_list)

    if note_lengths is None:
        note_lengths = [NOTE_LENGTH] * len(note_list)

    # Make sure lists are of the same length
    if len(velocities) != len(note_list) or len(note_lengths) != len(note_list):
        print(
            "Error: note_list, velocities, and note_lengths must be of the same length."
        )
        return

    with mido.open_output(midi_port) as port:
        for i, note in enumerate(note_list):
            velocity = velocities[i]
            note_length = note_lengths[i]

            # Skip 'X' and invalid notes
            if (
                note == "X"
                or note is None
                or note > 127
                or note < 12
                or type(note) != int
            ):
                continue

            # Play the note
            note_on = mido.Message("note_on", note=note, velocity=velocity)
            port.send(note_on)

            # Wait for the specified note length (in seconds)
            time.sleep(note_length)

            # Stop the note
            note_off = mido.Message("note_off", note=note, velocity=velocity)
            port.send(note_off)
