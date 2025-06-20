import time
import pygame
import asyncio
import os
from urllib.parse import unquote
import random

random.seed(time.time())

settings = {"debug" : True,
            "paused" : False,
            "num_songs" : 0,
            "count" : 0,
            "song_names" : [],
            "song_dict" : {} } #queue order, (name, path)
song_queue = {}

def bounds_check():
    if settings["count"] >= settings["num_songs"]:
            # settings["count"] = settings["count"] - (settings["num_songs"])
            settings["count"] = (settings["count"]) % settings["num_songs"]

async def play_song(song):
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, pygame.mixer.init)
        await loop.run_in_executor(None, pygame.mixer.music.load, song)
        await loop.run_in_executor(None, pygame.mixer.music.play)
    except Exception as e:
        print(f"Error playing audio: {e}")
        
async def user_conts():
    while True:
        cmd = await asyncio.get_event_loop().run_in_executor(None, input)
        if cmd == " " or cmd == "k":
            if settings["paused"] == False: #pause unpause
                pygame.mixer.music.pause()
                settings["paused"] = True
            elif settings["paused"] == True:
                pygame.mixer.music.unpause()
                settings["paused"] = False
        elif cmd == "l": #skip to next song
            pygame.mixer.music.stop()
            settings["paused"] = False
            # settings["count"] += 1
        elif cmd == "j": #go back to previous song
            pygame.mixer.music.stop()
            settings["paused"] = False
            settings["count"] -= 2
            bounds_check()
        elif cmd == "Q": # quit player
            pygame.mixer.music.stop()
            print("Quitting player.")
            os._exit(0)
        elif cmd == "r": #random skip
            r_num = random.randint(0, settings["num_songs"])
            for i in range(r_num):
                pygame.mixer.music.stop()
                
            settings["count"] += r_num
            bounds_check()
        elif cmd == "Caddy and a Sunflower":
            print("The blind eyes turned, the excuses made, the insidious lies whispered into the ear of a child")
        elif cmd == '>': #whats next
            count = settings["count"]
            if count == settings["num_songs"] - 1:
                count = - 1
            print("Playing next: " + ((settings["song_dict"])[count + 1])[0])

        elif cmd == '<':
            count = settings["count"]
            print(count)
            if count == 0:
                count = settings["num_songs"]
                print(count)
            
            print("Played previously: " + ((settings["song_dict"])[count - 1])[0])
        elif cmd == 'n':
            print("Playing now: " + ((settings["song_dict"])[settings["count"]])[0])
        elif cmd == 'queue' or cmd == 'q':
            queue_count = settings["count"]
            # list_count = 1
            print(f"    Playing now: {(settings['song_names'])[queue_count]}") #playing now
            queue_count += 1
            for i in range(1, settings["num_songs"]):
                if queue_count >= settings["num_songs"]:
                    queue_count = queue_count - settings["num_songs"]
                print(f"    {i}. {(settings['song_names'])[queue_count]}")
                queue_count += 1
                # list_count += 1
        elif cmd == 'shuffle' or cmd == 's':
            #in development
            print((settings["song_dict"]))
            
            
            
async def main():
    songs =  [f for f in os.listdir('music') if f.endswith('.mp3')]
    
    song_paths = []
    
    queue_order = 0
    
    for song in songs: #song paths
        settings["num_songs"]+=1
        decoded_song = unquote(song) 
        song_path = os.path.join('music', decoded_song)
        (settings["song_names"]).append(decoded_song)
        song_paths.append(song_path)
        
        (settings["song_dict"])[queue_order] = (decoded_song, song_path)
        queue_order += 1
        
    print("Queue: ")
    queue_count = 0
    for song in settings["song_names"]:
        queue_count += 1
        print(f"    {queue_count}. {song}")
    print()
    
    while True:
        print(settings["num_songs"])
        if settings["count"] >= settings["num_songs"]:
            # settings["count"] = settings["count"] - (settings["num_songs"])
            settings["count"] = (settings["count"]) % settings["num_songs"]
            
        print("Now playing: " + (settings["song_names"])[settings["count"]])
        await play_song(song_paths[settings["count"]])
        if settings["debug"]:
            print("count is: " + str(settings["count"]))
            
        while True:
            if settings["paused"]:
                await asyncio.sleep(0.2)
            elif pygame.mixer.music.get_busy():
                await asyncio.sleep(0.2)
            else:
                settings["count"] += 1
                break
        
async def run_player():
    await asyncio.gather(main(), user_conts())
        
        
asyncio.run(run_player())