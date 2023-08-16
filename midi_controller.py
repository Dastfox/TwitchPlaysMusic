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
    velocity: int,
    note_length: float,
    chords_allowed=True,
    midi_port=None,
    max_beats=4,
):
    """
    Send a MIDI note or chord to the specified MIDI port.
    :note_list: A list of MIDI notes to play.
    :param velocity: The velocity of the note(s) to play.
    :param note_length: The length of the note(s) to play.
    :param chords_allowed: Whether or not to play chords.
    :param midi_port: The MIDI port to play the note(s) on.

    """

    if type(note_list) == int:
        note_list = [note_list]
    if velocity is None or type(velocity) != int:
        velocity = VELOCITY
    if note_length is None:
        note_length = NOTE_LENGTH
    elif type(note_length) != float and type(note_length) != int:
        print("DEF note_length", note_length, type(note_length))
        try:
            note_length = float(note_length)
        except ValueError:
            note_length = NOTE_LENGTH

    final_notes = []

    for note in note_list:
        if note == "X":
            continue
        if note is None or note > 127 or note < 12 or type(note) != int:
            # remove the note
            note_list.remove(note)
    # print(
    #     "note_list",
    #     note_list,
    #     velocity,
    #     note_length,
    #     chords_allowed,
    #     midi_port,
    #     final_notes,
    # )
    print("Play", note_list, note_length)
    with mido.open_output(midi_port) as port:
        # Start all notes
        if not note_list == ["X"]:
            for note in note_list if chords_allowed else [note_list[0]]:
                note_on = mido.Message("note_on", note=note, velocity=velocity)
                port.send(note_on)
        else:
            print("No notes to play", note_list, note_length)
        # Wait for the specified note length (in seconds)
        time.sleep(note_length)
        # Stop all notes
        if not note_list == ["X"]:
            for note in note_list:
                note_off = mido.Message("note_off", note=note, velocity=velocity)
                port.send(note_off)
