import pyttsx3
import pathlib
import time
from sys import argv

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

SKIP_AUDIO = '--skip-audio' in argv

import pygame
import random


directory = pathlib.Path(__file__).parent.absolute().joinpath('files').absolute()


class AUDIO_IDS:
    PAUSE_HALF_SECOND = '<&p-0.5>'
    PAUSE_SECOND = '<&p-1>'
    START_MESSAGE = 'start-message'
    WAKEUP = 'wakeup'
    CALIBRATION_COMPLETE = 'calibration-complete'
    SASS_0 = 'sass-0'
    HAHA = 'haha'
    BEFORE_GAME = 'before-game'
    GOOD_LUCK = 'good-luck'
    OPTIONS_CHECK = 'options-check'
    USER_CHECK_BOARD = 'user-check-board'
    INVALID_MOVE = 'invalid-move'
    LOST = 'lost'
    WON = 'won'
    DING = 'ding-1'



AudioMessages = {
    AUDIO_IDS.START_MESSAGE: 'Hello, my name is Beth.',
    AUDIO_IDS.WAKEUP: 'I just woke up from a nap and need to recalibrate myself. This might be a little noisy.',
    AUDIO_IDS.CALIBRATION_COMPLETE: 'Okay, I am all calibrated and ready to play.',
    AUDIO_IDS.SASS_0: 'And by that, I mean that I am ready to beat you.',
    AUDIO_IDS.HAHA: 'ha. ha. ha',
    AUDIO_IDS.BEFORE_GAME: 'Press the button when you have made your move.',
    AUDIO_IDS.GOOD_LUCK: 'Good luck, and don\'t fuck it up.',
    AUDIO_IDS.OPTIONS_CHECK: 'Place options cards in the center of the board to set game options. Press the button to continue.',
    AUDIO_IDS.USER_CHECK_BOARD: 'I am having a hard time analyzing the board. Please clean it up and then press your button.',
    AUDIO_IDS.INVALID_MOVE: 'Invalid move detected, please make a different move.',
    AUDIO_IDS.LOST: 'Congratulations, you have won.',
    AUDIO_IDS.WON: 'Checkmate, I have won!'
}

for letter in 'abcdefgh':
    for number in range(1, 9):
        AudioMessages[f"{letter}{number}"] = f"{letter.replace('a', 'ayy')} {number}"


def generate_audio_files(audio_ids):
    engine = pyttsx3.init()
    voices = list(
        filter(lambda x: x.languages[0].startswith('en') and x.name in ['Samantha'], engine.getProperty('voices')))
    engine.setProperty('voice', voices[0].id)
    engine.setProperty('rate', 180)
    for audio_id in audio_ids:
        print(f"Generating audio for id {audio_id} saving to " + str(directory.joinpath(f"{audio_id}.wav").absolute()))
        engine.save_to_file(audio_ids[audio_id], str(directory.joinpath(f"{audio_id}.wav").absolute()))
    engine.runAndWait()


def play_audio_ids(*ids):
    """
    Plays the audio ids in the order they are listed. If a list of audio ids is
    supplied as
    """
    if SKIP_AUDIO:
        return
    pygame.mixer.init()
    for i in ids:
        if len(i) == 0:
            continue
        if type(i) == list:
            i = random.choice(i)
        if i == AUDIO_IDS.PAUSE_HALF_SECOND:
            time.sleep(0.5)
            continue
        elif i == AUDIO_IDS.PAUSE_SECOND:
            time.sleep(1)
            continue
        path = str(directory.joinpath(f"{i}.wav").absolute())
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue


if __name__ == '__main__':
    generate_audio_files(AudioMessages)
