import pyttsx3
import pathlib
import time
import pygame


directory = pathlib.Path(__file__).parent.absolute().joinpath('files').absolute()


class AUDIO_IDS:
    START_MESSAGE = 'start-message'
    ENABLE_CALIBRATION = 'enable-calibration'
    CHECKMATE = 'checkmate'
    WINNING = 'winning'
    PAWN_PROMOTION = 'pawn-promotion'
    PLEASE_PLACE_MY = 'please-place-my'
    ON = 'on'
    THEN_PRESS_BUTTON = 'then-press-button'
    QUEEN = 'queen'
    PAUSE_HALF_SECOND = '<&pause-id-0.5s&>'
    PAUSE_SECOND = '<&pause-id-1s&>'
    PAUSE_2_SECONDS = '<&pause-id-2s&>'
    CALIBRATION_COMPLETE = 'calibration-complete'


AudioMessages = {
    AUDIO_IDS.START_MESSAGE: 'Hello, my name is Beth, would you like to play me in chess?',
    AUDIO_IDS.ENABLE_CALIBRATION: 'Please enable calibration by pressing the x stop, followed by the closest y stop, the other y stop, and finally the player button.',
    AUDIO_IDS.CHECKMATE: 'Checkmate, I win!',
    AUDIO_IDS.WINNING: 'Looks like i\'m winning!',
    AUDIO_IDS.PAWN_PROMOTION: 'I am going to promote my pon with this move.',
    AUDIO_IDS.PLEASE_PLACE_MY: 'Please place my',
    AUDIO_IDS.ON: 'on',
    AUDIO_IDS.THEN_PRESS_BUTTON: 'Then press your button.',
    AUDIO_IDS.QUEEN: 'queen',
    AUDIO_IDS.CALIBRATION_COMPLETE: 'I have finished calibrating myself. I am ready to play.'
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
    pygame.mixer.init()
    for i in ids:
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
    # generate_audio_files(AudioMessages)
    play_audio_ids('a1')
