import pyttsx3
import pathlib
import time
import pygame
import random


directory = pathlib.Path(__file__).parent.absolute().joinpath('files').absolute()


class AUDIO_IDS:
    PAUSE_HALF_SECOND = '<&p-0.5>'
    PAUSE_SECOND = '<&p-1>'
    START_MESSAGE = 'start-message'
    WAKEUP = 'wakeup'
    CALIBRATION_0 = 'calibration-0'
    CALIBRATION_1 = 'calibration-1'
    CALIBRATION_2 = 'calibration-2'
    CALIBRATION_3 = 'calibration-3'
    CALIBRATION_COMPLETE = 'calibration-complete'
    SASS_0 = 'sass-0'


AudioMessages = {
    AUDIO_IDS.START_MESSAGE: 'Hello, my name is Beth.',
    AUDIO_IDS.WAKEUP: 'I just woke up from a nap and am a little disoriented. I going to need you to make sure that I am working properly.',
    AUDIO_IDS.CALIBRATION_0: 'Please press the button next to the motor on the top of my gantry. You will see it on the left hand side.',
    AUDIO_IDS.CALIBRATION_1: 'Ouch! Be more gentle next time buddy. Now press the button closes to the motor below the button you just pressed.',
    AUDIO_IDS.CALIBRATION_2: 'What are you? A snail? Let\'s hurry this up. Now press the button on the opposite side.',
    AUDIO_IDS.CALIBRATION_3: 'Finally, took you long enough. Now I can start my calibration. This might be a little noisy.',
    AUDIO_IDS.CALIBRATION_COMPLETE: 'Okay, I am all calibrated and ready to play.',
    AUDIO_IDS.SASS_0: 'And by that, I mean that I am ready to beat you. ha. ha. ha'
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
