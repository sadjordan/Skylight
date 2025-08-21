import time
import pygame
import asyncio
import os
from urllib.parse import unquote
import random
from rapidfuzz import process
from youtubesearchpython import VideosSearch
import yt_dlp
import requests
from bs4 import BeautifulSoup

random.seed(time.time())

DEFAULT_DIRECTORY = "music"
SEARCH_ENGINE = f"https://duckduckgo.com/html/?q="

settings = {"debug" : False,
            "playlist" : "music", #music is default directory
            "reload" : False,
            "paused" : False,
            "num_songs" : 0,
            "count" : 0,
            # "song_names" : [], #to be phased out
            "song_dict" : {},
            "repeat" : False, #queue order, (name, path)
            } 

def reset_settings():
    settings["num_songs"] = 0
    settings["count"] = 0
    settings["paused"] = False
    settings["reload"] = False
    settings["song_dict"] = {}
    settings["repeat"] = False

def bounds_check(): #might be useless
    if settings["count"] >= settings["num_songs"]:
            # settings["count"] = settings["count"] - (settings["num_songs"])
            settings["count"] = (settings["count"]) % settings["num_songs"]
            
def search_song(query):
    song_names = []
    
    for i in range(settings["num_songs"]):
        song_names.append(((settings["song_dict"])[i])[0])
        
    match, score, idx = process.extractOne(query, song_names)
    if score > 60:
        return match
    else:
        return None
    
def search_query(query, search_within):
    match, score, idx = process.extractOne(query, search_within)
    if score > 60:
        return match
    else:
        return None
    
def search_web(query):
    url = f"{SEARCH_ENGINE}{query.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

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
            if settings["debug"]: print("count within j after stop(): " + str(settings["count"]))
            if settings["count"] == 0:
                settings["paused"] = False
                settings["count"] = settings["num_songs"]
                # settings["count"] -= 1
            settings["paused"] = False
            settings["count"] -= 2
            bounds_check()
        elif cmd == "Q" or cmd == "quit": # quit player
            pygame.mixer.music.stop()
            print("Quitting player.")
            os._exit(0)
        elif cmd == "R": #random skip
            r_num = random.randint(0, settings["num_songs"])
            for i in range(r_num):
                pygame.mixer.music.stop()
                
            settings["count"] += r_num
            bounds_check()
        elif cmd == "Caddy and a Sunflower":
            print("The blind eyes turned, the excuses made, the insidious lies whispered into the ear of a child")
        elif cmd == '>': #whats next
            bounds_check()
            count = settings["count"]
            if count == settings["num_songs"] - 1:
                count = - 1
                if settings["debug"]:
                    print(count)
            print("Playing next: " + ((settings["song_dict"])[count + 1])[0])
        elif cmd == '<':
            bounds_check()
            if settings["count"] == -1:
                print("You just shuffled the playlist, unable to display previous song") #fix at a later date
                continue
            count = settings["count"]
            if settings["debug"]:
                print(count)
            if count == 0:
                count = settings["num_songs"]
                if settings["debug"]:
                    print(count)
            print("Played previously: " + ((settings["song_dict"])[count - 1])[0])
        elif cmd == 'n':
            if settings["count"] == -1:
                print("You just shuffled the playlist, unable to display previous song") #fix at a later date
                continue
            print("Playing now: " + ((settings["song_dict"])[settings["count"]])[0])
        elif cmd == 'queue' or cmd == 'q':
            queue_count = settings["count"]
            # list_count = 1
            print(f"    Playing now: {((settings["song_dict"])[settings["count"]])[0]}") #playing now
            queue_count += 1
            for i in range(1, settings["num_songs"]):
                if queue_count >= settings["num_songs"]:
                    queue_count = queue_count - settings["num_songs"]
                print(f"    {i}. {((settings["song_dict"])[queue_count])[0]}")
                queue_count += 1
                # list_count += 1
        elif cmd == 'shuffle' or cmd == 's':
            #in development
            bounds_check()
            song_list = list(settings["song_dict"].values())
            if settings["debug"]:
                print("song_list length: " + str(len(song_list)))
            random.shuffle(song_list)
            if settings["debug"]:
                print(settings["num_songs"])
                print(len([0, 1]))
            for i in range(settings["num_songs"]):
                if settings["debug"]:
                    print("shuffle i = " + str(i))
                (settings["song_dict"])[i] = song_list[i]
                
            queue_count = 1
            print("New Shuffled Queue")
            print(f"    Playing next: {((settings['song_dict'])[queue_count])[0]}")
            queue_count += 1
            for i in range(1, settings["num_songs"]):
                if queue_count >= settings["num_songs"]:
                    queue_count = queue_count - settings["num_songs"]
                print(f"    {i + 1}. {((settings['song_dict'])[queue_count])[0]}")
                queue_count += 1        
            settings["count"] = 0
            # if settings["debug"]:
            #     print("Current count: " + str(settings["count"]))
            #     print("Song at current count: " + str(((settings['song_dict'])[(settings["count"])])[0]))
        elif cmd == "r":
            settings["repeat"] =  not settings["repeat"]
            if settings["repeat"]:
                print("Repeating Current Song")
            else:
                print("Repeat Disabled")
        elif cmd.startswith("playlist "): #using the search function initially developed for song names 
            playlists = [entry.name for entry in os.scandir(DEFAULT_DIRECTORY) if entry.is_dir()]
            playlists.append(DEFAULT_DIRECTORY)
            
            playlist_query = cmd[len("playlist "):].strip()
            match = search_query(playlist_query, playlists)
            if match:
                if match != DEFAULT_DIRECTORY:
                    settings["playlist"] = DEFAULT_DIRECTORY + "/" + match
                    settings["reload"] = True
                    pygame.mixer.music.stop()
                    break
                else:
                    settings["playlist"] = DEFAULT_DIRECTORY
                    settings["reload"] = True
                    pygame.mixer.music.stop()
                    break
            else:
                print("Unable to find playlist")
        elif cmd.startswith("play "):
            song_name = cmd[len("play "):].strip()
            match = search_song(song_name)
            if match:
                for i in range(settings["num_songs"]):
                    if (settings["song_dict"][i][0] == match):
                        settings["count"] = i - 1
                        pygame.mixer.music.stop()
                        break
            else:
                print("Unable to find song")
        elif cmd.startswith("query "):
            yt_query = cmd[len("query "):].strip()
            ytSearch = VideosSearch(yt_query, limit = 10)
            results = ytSearch.result()
            
            top_video = results['result'][0]
            print("Top result: ")
            print(top_video["title"])
            print(top_video["link"])

            selected_video = [top_video["title"], top_video["link"]]
            response = input("Would you like to download this? (For more results use query more) \n")
            
            while response.startswith("query "):
                if response == "query more":
                    count = 1
                    for video in results['result']:
                        
                        print(f"{count}.\t{video["title"]}")
                        print(video["link"] + "\n")
                        
                        count += 1
                        
                        print("To select a video for download, use query [list position]")
                if (response[len("query "):].strip()).isdigit():
                    index = int(response[len("query "):].strip()) - 1
                    temp = results['result'][index]
                    selected_video = [temp["title"], temp["link"]]
                    
                response = input(f"Would you like to download the selected video ({selected_video[0]})? \n")
            
            if response.lower() == "yes":
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': f'{DEFAULT_DIRECTORY}/%(title)s.%(ext)s',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([(selected_video[1])])
                    print("\nOperation complete!")
            else: 
                print("Operation cancelled")

            
        elif cmd == "test":
            search_web("History of Man" + " Lyrics")
                
            
            
            
async def player():
    songs =  [f for f in os.listdir(settings["playlist"]) if f.endswith('.mp3')]
    
    song_paths = []
    
    queue_order = 0
    
    for song in songs: #song paths
        decoded_song = unquote(song) 
        song_path = os.path.join(settings["playlist"], decoded_song)
        # (settings["song_names"]).append(decoded_song)
        song_paths.append(song_path)
        
        (settings["song_dict"])[queue_order] = (decoded_song, song_path)
        queue_order += 1
        settings["num_songs"]+=1
        if settings["debug"]:
            print("num_songs_main is: " + str(settings["num_songs"]))
        
    print("Queue: ")
    # queue_count = 0
    for song in range(1, settings["num_songs"] + 1):
        # queue_count += 1
        print(f"    {song}. {((settings["song_dict"])[song - 1])[0]}")
    print()
    
    while True:
        if settings["debug"]: 
            print(settings["num_songs"])
        if settings["count"] >= settings["num_songs"]:
            # settings["count"] = settings["count"] - (settings["num_songs"])
            settings["count"] = (settings["count"]) % settings["num_songs"]
            
        print("Now playing: " + ((settings["song_dict"])[settings["count"]])[0])
        await play_song(((settings["song_dict"])[settings["count"]])[1])
        if settings["debug"]:
            print("count is: " + str(settings["count"]))
            
        while True:
            if settings["paused"]:
                await asyncio.sleep(0.2)
            elif pygame.mixer.music.get_busy():
                await asyncio.sleep(0.2)
            elif settings["repeat"]:
                break
            elif settings["reload"]:
                reset_settings()
                return
            else:
                settings["count"] += 1
                break
        
async def run_player():
    while True:
        await asyncio.gather(player(), user_conts())
        

asyncio.run(run_player())