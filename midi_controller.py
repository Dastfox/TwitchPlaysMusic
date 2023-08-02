import mido
import time

NOTE = 60
VELOCITY = 64
NOTE_LENGTH = 0.5


def send_midi_notes(note_list, velocity, note_length):
    print("send_midi_notes", note_list, velocity, note_length)
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
    for note in note_list:
        if note is None or note > 127 or note < 12 or type(note) != int:
            note = NOTE

    with mido.open_output("LoopBe Internal MIDI 1") as port:
        # Start all notes
        for note in note_list:
            note_on = mido.Message("note_on", note=note, velocity=velocity)
            port.send(note_on)
        # Wait for the specified note length (in seconds)
        time.sleep(note_length)
        # Stop all notes
        for note in note_list:
            note_off = mido.Message("note_off", note=note, velocity=velocity)
            port.send(note_off)


send_midi_notes(60, velocity=64, note_length=0.5)
notes_to_play = [60, 65, 72]
# send_multiple_notes(notes_to_play, velocity=64, note_length=0.5)
