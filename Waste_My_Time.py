import time
import pygame

def play_song():
    try:
        pygame.mixer.init()
        pygame.mixer.music.load('Waste_My_Time.mp3')
        pygame.mixer.music.play()
    except Exception as e:
        print(f"Error playing audio: {e}")
        
def lyric_coefficient_method(lyrics, lyric_char_coefficient = 0.15):
    lyric_delay = []
    count = 0

    for line in lyrics:
        lyric_delay.append(0)
        for character in line:
            if character == ',':
                lyric_delay[count] += 0.5
            elif character == '​':
                lyric_delay[count] += 0.5 #Normal delay
            elif character == ' ':
                lyric_delay[count] += 0.8 #Extended delay
            else:
                lyric_delay[count] += lyric_char_coefficient
        count += 1
    return lyric_delay

waste_my_time = """This town has nothing left for me
Except for you
And I could leave this place today
If only you came with me
That's the only way I'd be happy
And I would waste my life living here -0.5
And I would waste my time sitting here for you, for you
And I would waste my eyes on this shitty view
If I could spend my nights laying next to you, my dear, my dear --
I've always wanted to live by the ocean side
But if you have to stay here I would change my mind
'Cause you mean more than me than luxury
And sand beneath my feet
And I'd be damned If I watched you walk away from here
And I would waste my life living here
And I would waste my time sitting here for you, for you
And I would waste my eyes on this shitty view
If I could spend my nights laying next to you, my dear, my dear
And if I had to, I would follow you - 0.3
If I had to, I would follow you
If I had to, I would follow you
If I had to, I would follow you
And I would waste my life living here
And I would waste my time sitting here for you, for you
And I would waste my eyes on this shitty view
If I could spend my nights laying
Next to you, my dear, my dear, my dear"""


play_song()
lyrics = waste_my_time.split('\n')

# lyric_delay = lyric_coefficient_method(0.16, lyrics)

#Manual
lyric_delay = [10.00, 4.70, 3.37, 2.98, 3.8, 10.0, 4.78, 9.79+4.13, 11.21, 7.57, 6.93, 5.31, 4.06, 3.16, 6.97, 4.03, 10.64, 3.73, 10.44, 6.57, 4.94, 6.92, 7.55, 4.07, 9.27, 4.48, 2.67, 10.95]

time.sleep(lyric_delay[0])

lyric_line = 1
for line in lyrics:
    time.sleep(lyric_delay[lyric_line])
    print(line)
    lyric_line += 1
    
input("Click enter to end the song")