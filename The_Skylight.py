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
import sqlite3

random.seed(time.time())

DEFAULT_DIRECTORY = "music"
SEARCH_ENGINE = f"https://duckduckgo.com/html/?q="
DB_FILE = 'songs.db'

settings = {"debug" : False,
            "playlist" : DEFAULT_DIRECTORY, #replaced with default playlist
            "reload" : False, #if true the player will restart, use when adding more songs or any cases where the player must restart without terminating the instance
            "paused" : False, 
            "num_songs" : 0, #this is a count of the number of songs, only modified once when initialised or restarted
            "count" : 0, #to keep track of which song is being currently played, this will loop around to 0 
            # "song_names" : [], #to be phased out
            "song_dict" : {}, #each entry is the queue number with (file name, file directory)
            "repeat" : False, #queue order, (name, path)
            } 

def reset_settings(): #used when restarting to reset the settings dictionary
    settings["num_songs"] = 0
    settings["count"] = 0
    settings["paused"] = False
    settings["reload"] = False
    settings["song_dict"] = {}
    settings["repeat"] = False

def bounds_check(): #might be useless, check later on
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
    # print(url)
    headers = {"User-Agent": "Mozilla/5.0"}
    
    response = requests.get(url, headers=headers)
    # print(response)
    soup = BeautifulSoup(response.text, "html.parser")
    results = soup.find_all('a', class_='result__a')
    
    # print(results)
    
    if results:
        # print(results[0].text)
        # print("\n")
        return results[0].text
    else:
        print("Error searching the web")
        return None
    
def initial_database_creation(): #database added in lyrics update
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS allsongs (
        song_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        file_directory TEXT NOT NULL,
        lyrics TEXT,
        artist_name TEXT,
        song_name TEXT,
        error INTEGER,
        downloaded_from TEXT
    )
    """)

    conn.commit()
    
    for i in range(settings["num_songs"]):
        cursor.execute("""
            INSERT INTO allsongs (file_directory)
            VALUES (?)
        """, (((settings["song_dict"])[i])[1],))
        
        conn.commit()
    conn.close()
    
def database_check(): #database added in lyrics update
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT file_directory FROM allsongs")
    db_file_list = cursor.fetchall()
    db_file_list = [row[0] for row in db_file_list]
    # print(db_file_list)
    added_count = 0
    
    for i in range(settings["num_songs"]):
        
        file_directory = ((settings["song_dict"])[i])[1]
        if file_directory not in db_file_list:
            # temp += 1
            # print(temp)
            cursor.execute("""
            INSERT INTO allsongs (file_directory)
            VALUES (?)
            """, (file_directory,))
            # print("success")
            added_count += 1
            
        
        # print(file_directory)
        # cursor.execute("""
        #     INSERT INTO allsongs (file_directory)
        #     VALUES (?)
        # """, (((settings["song_dict"])[i])[1],))
    
    #need to call the dictionary and run a check against the database to delect 
    #songs with no entry in the database
    
    print(f"Songs added to database {added_count}")

    conn.commit()
    conn.close()
    
def song_name_artist_extraction(filename):
    query = filename.replace(".mp3", "")
    search_result = search_web(query + "Genius Lyrics")
    print(search_result)
    search_result = search_result.replace("Lyrics | Genius Lyrics", "")
    search_result = search_result.replace("Lyrics - Genius", "")
    print(search_result)
    song_details = search_result.split("-")
    print(song_details)
    song_details = [detail.strip() for detail in song_details]
    print(song_details)
    
    #file_directory = settings["playlist"] + "/" + filename 
    file_directory = DEFAULT_DIRECTORY + "/" + filename 
    #Repurposing of the playlist setting for name instead of folder directory
    
    # print(file_directory)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE allsongs
        SET artist_name = ?, song_name = ?
        WHERE file_directory = ?
    """, (song_details[0], song_details[1], file_directory))
    
    confirmation = input(f"Is this correct (yes/no)?\nArtist: {song_details[0]}\nSong name: {song_details[1]}\n")
    
    if confirmation.lower() == 'yes':
        conn.commit()
        conn.close()
        try:
            lyric_extraction(song_details[0], song_details[1], file_directory)
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Operation cancelled")
        conn.close()
        return
    
def lyric_extraction(artist, song_name, file_directory):
    response = requests.get(f"https://api.lyrics.ovh/v1/{artist}/{song_name}")
    print(response)
    
    if response.status_code != 200:
        print("Query Failure")
        return
    
    lyrics = response.json().get('lyrics', '')
    
    print(lyrics)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
            UPDATE allsongs
            SET lyrics = ?
            WHERE file_directory = ?
            """, (lyrics, file_directory)
    )
    
    conn.commit()
    conn.close()

def display_lyrics(filename): #input is file name
    file_directory = settings["playlist"] + "/" + filename
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    
    cursor.execute("""
        SELECT lyrics FROM allsongs
        WHERE file_directory = ?
    """, (file_directory,))
    
    result = cursor.fetchall()
    conn.close()
    
    if result and result[0]:
        print("\n———————— Lyrics ————————\n")
        print(result[0][0])
    else:
        print("No lyrics found for this song")
    

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
        elif cmd.startswith("playlist "): #playlist must be repurposed
            playlists = [entry.name for entry in os.scandir(DEFAULT_DIRECTORY) if entry.is_dir()]
            playlists.append(DEFAULT_DIRECTORY)
            
            playlist_query = cmd[len("playlist "):].strip()
            match = search_query(playlist_query, playlists)
            if match:
                if match != DEFAULT_DIRECTORY:
                    settings["playlist"] = DEFAULT_DIRECTORY + "/" + match
                    settings["repeat"] = False
                    settings["reload"] = True
                    pygame.mixer.music.stop()
                    break
                else:
                    settings["playlist"] = DEFAULT_DIRECTORY
                    settings["repeat"] = False
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
            
            while response.startswith("query ") or response.isdigit(): #idea here is to loop continuously until user selects a video or exits
                if response == "query more":
                    count = 1
                    for video in results['result']:
                        
                        print(f"{count}.\t{video["title"]}")
                        print(video["link"] + "\n")
                        
                        count += 1
                        
                        print("To select a video for download, use query [list position]")
                elif response.startswith("query "):
                    print("Unknown command, please enter a valid command")
                elif (response.isdigit()):
                    index = int(response) - 1
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
                    
                    print("\nDownload complete!")
                    
                    file_path = f"{DEFAULT_DIRECTORY}/{selected_video[0]}.mp3"
                    
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT INTO allsongs (file_directory, downloaded_from)
                        VALUES (?, ?)
                    """, (file_path, selected_video[1]))
                    
                    conn.commit()
                    conn.close()
            else: 
                print("Operation cancelled")
        elif cmd == "reload":
            settings["reload"] = True
            settings["repeat"] = False
            pygame.mixer.music.stop()
            break
        elif cmd.startswith("lyrics "):
            if cmd.startswith("lyrics search "):
                lyrics_query = cmd[len("lyrics search "):].strip()
                print(lyrics_query)
                
                song_directory = ''
                
                # lock = False
                
                while True:
                    if lyrics_query == 'x':
                        print("Operation Cancelled")
                        break
                    song_directory = search_song(lyrics_query)
                    if song_directory == None:
                        lyrics_query = input("Unable to find song, please enter the song you want lyrics for (enter x to quit): ")
                    else:
                        print(song_directory)
                        confirmation = input(f"Find lyrics for {song_directory}? (yes/no) \n")
                        if confirmation.lower() == "yes":
                            song_name_artist_extraction(song_directory)
                            break
                        else: 
                            print("Operation Cancelled")
                            break
                #         else:
                #             lyrics_query = input("Please enter the song you want lyrics for (enter x to quit): ")
                            
                # if lyrics_query != 'x':
            elif cmd == "lyrics -c":
                song_name_artist_extraction(((settings["song_dict"])[settings["count"]])[0])
                
                
        # """ Kind of a redundant feature since any use would be for the current song"""        
        # elif cmd.startswith("lyrics "):
        #     lyrics_query = cmd[len("lyrics "):].strip()
        #     while True:
        #         song_directory = search_song(lyrics_query)
        #         if song_directory == None:
        #             lyrics_query = input("Unable to find song, please enter the song you want lyrics for (enter x to quit): ")
        #         elif lyrics_query == 'x':
        #             break
        #         else:
        #             print(song_directory)
        #             confirmation = input(f"Find lyrics for {song_directory}? (yes/no) \n")
        #             if confirmation.lower() == "yes":
        #                 break
        #             else:
        #                 lyrics_query = input("Please enter the song you want lyrics for (enter x to quit): ")

        #     if lyrics_query != 'x':
        #         display_lyrics(song_directory)
        
        elif cmd == "lyrics":
            song_directory = ((settings["song_dict"])[settings["count"]])[0] #current song
            # print(song_directory)
            display_lyrics(song_directory)

        elif cmd == "test":
            
            results = []
            song_name_list = []
            
            for i in range(settings["num_songs"]):
                song_name_list.append((((settings["song_dict"])[i])[0]).replace(".mp3", ""))
            
            for j in song_name_list:
                # print(i)
                # print(j)
                # print(search_web(j + " Genius Lyrics"))
                results.append(search_web(j + "Genius Lyrics"))
                time.sleep(3)
                
            # for result in results:
            #     print(result + "\n")
            
        elif cmd == "test2":
            database_check()
            
            
            
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
            
    database_check() #check if any songs are not in the database
        
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