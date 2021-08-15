import pyttsx3
import pathlib
import time
import pygame
import random


directory = pathlib.Path(__file__).parent.absolute().joinpath('files').absolute()


class AUDIO_IDS:
    START_MESSAGE = 'start-message'
    BEFORE_1 = 'before-1'
    BEFORE_2 = 'before-2'
    ENABLE_CALIBRATION = 'enable-calibration'
    CHECKMATE = 'checkmate'
    WINNING = 'winning'
    HAHA = 'haha'
    PAWN_PROMOTION = 'pawn-promotion'
    PLEASE_PLACE_MY = 'please-place-my'
    ON = 'on'
    THEN_PRESS_BUTTON = 'then-press-button'
    QUEEN = 'queen'
    PAUSE_HALF_SECOND = '<&pause-id-0.5s&>'
    PAUSE_SECOND = '<&pause-id-1s&>'
    PAUSE_2_SECONDS = '<&pause-id-2s&>'
    CALIBRATION_COMPLETE = 'calibration-complete'
    X_STOP_PRESSED = 'x-stop-pressed'
    RIGHT_Y_STOP_PRESSED_0 = 'right-y-stop-pressed-0'
    RIGHT_Y_STOP_PRESSED_1 = 'right-y-stop-pressed-1'
    LEFT_Y_STOP_PRESSED_0 = 'left-y-stop-pressed-0'
    LEFT_Y_STOP_PRESSED_1 = 'left-y-stop-pressed-1'
    CALIBRATION_COMPLETE_AFTER = 'calibration-complete-after'


AudioMessages = {
    AUDIO_IDS.BEFORE_1: 'Before we play, I need to get myself ready.',
    AUDIO_IDS.BEFORE_2: 'Before I beat you in chess, I need to get myself ready.',
    AUDIO_IDS.START_MESSAGE: 'Hello, my name is Beth.',
    AUDIO_IDS.ENABLE_CALIBRATION: 'Please enable calibration by pressing the x stop.',
    AUDIO_IDS.CHECKMATE: 'Checkmate, I win!',
    AUDIO_IDS.WINNING: 'Looks like i\'m winning!',
    AUDIO_IDS.PAWN_PROMOTION: 'I am going to promote my pon with this move.',
    AUDIO_IDS.PLEASE_PLACE_MY: 'Please place my',
    AUDIO_IDS.ON: 'on',
    AUDIO_IDS.THEN_PRESS_BUTTON: 'Then press your button.',
    AUDIO_IDS.QUEEN: 'queen',
    AUDIO_IDS.CALIBRATION_COMPLETE: 'I have finished calibrating myself. I am ready to play.',
    AUDIO_IDS.CALIBRATION_COMPLETE_AFTER: 'And by that, I mean I am ready to beat you.',
    AUDIO_IDS.X_STOP_PRESSED: 'Good, now press the left Y stop.',
    AUDIO_IDS.RIGHT_Y_STOP_PRESSED_0: 'Perfect, now starting calibration. This might be a little noisy.',
    AUDIO_IDS.RIGHT_Y_STOP_PRESSED_1: 'Finally, took you long enough. Now I can start calibration. This might be a little noisy.',
    AUDIO_IDS.LEFT_Y_STOP_PRESSED_0: 'Ouch! Be more gentle next time buddy. Now press the other Y stop.',
    AUDIO_IDS.LEFT_Y_STOP_PRESSED_1: 'What are you? A snail? Let\'s hurry this up. Now press the other Y stop.',
    AUDIO_IDS.HAHA: 'ha. ha. ha'
}

for letter in 'abcdefgh':
    for number in range(1, 9):
        AudioMessages[f"{letter}{number}"] = f"{letter.replace('a', 'ayy')} {number}"


def generate_audio_files(audio_ids):
    engine = pyttsx3.init()
    voices = list(
        filter(lambda x: x.languages[0].startswith('en') and x.name in ['Samantha'], engine.getProperty('voices')))
    engine.setProperty('voice', voices[0].id)
    engine.setProperty('rate', 170)
    for audio_id in audio_ids:
        print(f"Generating audio for id {audio_id} saving to " + str(directory.joinpath(f"{audio_id}.wav").absolute()))
        engine.save_to_file(audio_ids[audio_id], str(directory.joinpath(f"{audio_id}.wav").absolute()))
    engine.runAndWait()


def play_audio_ids(*ids):
    """
    Plays the audio ids in the order they are listed. If a list of audio ids is
    supplied as
    """
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
        elif i == AUDIO_IDS.PAUSE_2_SECONDS:
            time.sleep(2)
            continue
        path = str(directory.joinpath(f"{i}.wav").absolute())
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue


if __name__ == '__main__':
    generate_audio_files(AudioMessages)
