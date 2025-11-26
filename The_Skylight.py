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
import datetime

random.seed(time.time())

DEFAULT_DIRECTORY = "music"
DEFAULT_PLAYLIST = "default"
SEARCH_ENGINE = f"https://duckduckgo.com/html/?q="
DB_FILE = 'songs.db'


settings = {"debug" : False,
            "playlist" : DEFAULT_PLAYLIST, #replaced with default playlist
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

    #Songs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS allsongs (
        song_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        file_directory TEXT NOT NULL,
        lyrics TEXT,
        artist_name TEXT,
        song_name TEXT,
        error INTEGER,
        downloaded_from TEXT,
        times_listened INTEGER,
        times_skipped INTEGER,
        last_listened_to TEXT
    )
    """)
    #Note: Can add genre/ tag but would require user effort and seems a bit unnecessary
    
    #Playlist table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS playlist (
        playlist_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        playlist_name TEXT NOT NULL,
        playlist_song TEXT,
        playlist_description TEXT,
        playlist_created_on TEXT NOT NULL,
        playlist_switched_to INTEGER NOT NULL,
        playlist_songs_listened INTEGER NOT NULL,
        playlist_last_accessed TEXT
    )
    """)

    conn.commit()
    #No longer necessary as there is now database_check() which is run at startup
    
    # for i in range(settings["num_songs"]):
    #     cursor.execute("""
    #         INSERT INTO allsongs (file_directory)
    #         VALUES (?)
    #     """, (((settings["song_dict"])[i])[1],))
        
    #     conn.commit()
    # conn.close() 
    
def database_check(): #updated to scan instead of rely on dict, need to check if it works
    songs =  [f for f in os.listdir(DEFAULT_DIRECTORY) if f.endswith('.mp3')]
    
    file_directory = []
    
    for song in songs: #song paths
        decoded_song = unquote(song) 
        song_path = os.path.join(DEFAULT_DIRECTORY, decoded_song)
        # (settings["song_names"]).append(decoded_song)
        file_directory.append(song_path) #contains music/song_name.mp3 etc.
    
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT file_directory FROM allsongs")
    db_file_list = cursor.fetchall()
    db_file_list = [row[0] for row in db_file_list]
    # print(db_file_list)
    added_count = 0
    
    #also made it add it to the default playlist
    for i in range(settings["num_songs"]):
        if file_directory not in db_file_list:
            # temp += 1
            # print(temp)
            cursor.execute("""
                INSERT INTO allsongs (file_directory)
                VALUES (?)
            """, (file_directory,))
            
            add_song_to_default_playlist_via_file_directory(file_directory)
            
            
            added_count += 1
            
    print(f"Songs added to database {added_count}")

    conn.commit()
    conn.close()
    
def add_song_to_default_playlist_via_file_directory(file_directory):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT song_id FROM allsongs
        WHERE file_directory = ?
        """, (file_directory,))

    song_pk = str(((cursor.fetchall())[0])[0])

    cursor.execute("""
        SELECT playlist_song FROM playlist
        WHERE playlist_name = ?
        """, (DEFAULT_PLAYLIST,))
        
    playlist_songs = ((cursor.fetchall())[0])[0] #this could return none
    if playlist_songs == None:
        playlist_songs = ""
    print(f"playlist_songs = {playlist_songs}")


    playlist_songs = playlist_songs + song_pk + "," 
    print(f"playlist_songs2 = {playlist_songs}")

    cursor.execute("""
        UPDATE playlist
        SET playlist_song = ?
        WHERE playlist_name = ?
        """, (playlist_songs, DEFAULT_PLAYLIST)
    )
    
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
    file_directory = DEFAULT_DIRECTORY + "/" + filename
    
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
        
def song_from_index(song_query, output="name"):
    if output == "name":
        index = (int(song_query) - 1 + settings["count"]) % settings["num_songs"]
        selected_song = ((settings["song_dict"])[index])[0]  #need to loop this to prevent index error
        return selected_song
    elif output == "index":
        # if settings["count"] == 0: #exists because for some reason there is an issue with positioning when index is not 0
        #     index = (int(song_query) - 1 + settings["count"]) % settings["num_songs"]  #need to loop this to prevent index error
        # else:
        
        #the above was commented out because i realised the initial display upon starting or reloading shows all the songs and thsu was the cause of the issue
        
        index = (int(song_query) + settings["count"]) % settings["num_songs"]
        return index
    else:
        print("Unknown output function used")
        
class Playlist:
    def __init__(self):
        self.selected_playlist = "None"
    
    def create_playlists(self, playlist_name):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        created_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("""
            INSERT INTO playlist (
                playlist_name,
                playlist_created_on,
                playlist_switched_to,
                playlist_songs_listened)
            VALUES (?, ?, ?, ?)
            """, (playlist_name, created_time, 0, 0),)
        
        print(f"Playlist {playlist_name} successfully created!")
        
        conn.commit()
        conn.close()
    
    def selection_check(self):
        return self.selected_playlist == "None"
    
    def playlist_list(self):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
                SELECT playlist_name FROM playlist
            """)
        
        playlists = [row[0] for row in cursor.fetchall()]
        # print(playlists)
        conn.close()
        
        return playlists
        
        
    def playlist_search(self, playlist_query): #develop search function for playlists
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
                SELECT playlist_name FROM playlist
            """)
        
        playlists = [row[0] for row in cursor.fetchall()]
        
        match = search_query(playlist_query, playlists)
        
        conn.close()
        
        return match
    
    def universal_playlist(self):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM playlist WHERE playlist_name =?
                )
             """, (DEFAULT_PLAYLIST,))
        
        result = ((cursor.fetchall())[0])[0]
        # print(result)
        if result == 0:
            self.create_playlists(DEFAULT_PLAYLIST)
            
            cursor.execute("""
            SELECT song_id FROM allsongs
            """)
            
            song_pks = cursor.fetchall()
            # print(song_pks)
            
            for i in range(len(song_pks)): #remove the tuples
                song_pks[i] = str((song_pks[i])[0])
                
            pk_string = ""
            for pk in song_pks:
                pk_string += pk + "," 
                
            # print(pk_string)
            cursor.execute("""
                UPDATE playlist
                SET playlist_song = ?
                WHERE playlist_name = ?
                """, (pk_string, DEFAULT_PLAYLIST)
            )
            
        conn.commit()
        conn.close()
    
    def select_playlist(self, playlist_name): #select a playlist for editing
        match = self.playlist_search(playlist_name)
        if match:
            self.selected_playlist = match
            print(f"{self.selected_playlist} has been selected!")
        else:
            print("Unable to find playlist")
    
    def add_song(self, song): #functional
        if self.selection_check():
            print("No playlist selected!") #add command for selecting playlist
            return
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT song_id FROM allsongs
        WHERE file_directory = ?
        """, (song,))
        
        song_pk = str(((cursor.fetchall())[0])[0])
        # print(f"song_pk = {song_pk}")
        
        cursor.execute("""
        SELECT playlist_song FROM playlist
        WHERE playlist_name = ?
        """, (self.selected_playlist,))
        
        playlist_songs = ((cursor.fetchall())[0])[0] #this could return none
        if playlist_songs == None:
            playlist_songs = ""
        # print(f"playlist_songs = {playlist_songs}")

        
        playlist_songs = playlist_songs + song_pk + "," 
        # print(f"playlist_songs2 = {playlist_songs}")
        
        cursor.execute("""
            UPDATE playlist
            SET playlist_song = ?
            WHERE playlist_name = ?
            """, (playlist_songs, self.selected_playlist)
        )
        
        conn.commit() 
        conn.close()
    
    def delete_song(self, song_index): #accepting file names only
        if self.selection_check():
            print("No playlist selected!") #add command for selecting playlist
            return
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT song_id FROM allsongs
        WHERE file_directory = ?
        """, (song_index,))
        
        try:
            song_pk = str(((cursor.fetchall())[0])[0])
        except:
            print("Song not found in playlist")
        # print(f"song_pk = {song_pk}")
        
        cursor.execute("""
        SELECT playlist_song FROM playlist
        WHERE playlist_name = ?
        """, (self.selected_playlist,))
        
        playlist_songs = ((cursor.fetchall())[0])[0] #this could return none
        if playlist_songs == None:
            # playlist_songs = ""
            print("There are no songs in the playlist!")
            return
        print(f"playlist_songs = {playlist_songs}")

        #removing the string specified
        
        playlist_songs = playlist_songs.replace(f",{song_pk},", ",")
        
        print(f"playlist_songs2 = {playlist_songs}")
        
        cursor.execute("""
            UPDATE playlist
            SET playlist_song = ?
            WHERE playlist_name = ?
            """, (playlist_songs, self.selected_playlist)
        )
        
        # conn.commit() 
        conn.close()
    
        
    
        
    
    #To add:
    # delete_song(song)
    # add_description(description)
    # delete_playlist(playlist)
    # describe_playlist(playlist) #for showing all data
        
    #     cursor.execute("""
    # CREATE TABLE IF NOT EXISTS playlist (
    #     playlist_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    #     playlist_name TEXT NOT NULL,
    #     playlist_song TEXT,
    #     playlist_created_on TEXT NOT NULL,
    #     playlist_switched_to INTEGER NOT NULL,
    #     playlist_songs_listened INTEGER NOT NULL,
    # )
    # """)
        

async def play_song(song):
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, pygame.mixer.init)
        await loop.run_in_executor(None, pygame.mixer.music.load, song)
        await loop.run_in_executor(None, pygame.mixer.music.play)
    except Exception as e:
        print(f"Error playing audio: {e}")
        
async def user_conts(pl : Playlist):    
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
        # elif cmd.startswith("playlist "): # retired to be replaced with new system
        #     playlists = [entry.name for entry in os.scandir(DEFAULT_DIRECTORY) if entry.is_dir()]
        #     playlists.append(DEFAULT_DIRECTORY)
            
        #     playlist_query = cmd[len("playlist "):].strip()
        #     match = search_query(playlist_query, playlists)
        #     if match:
        #         if match != DEFAULT_DIRECTORY:
        #             settings["playlist"] = DEFAULT_DIRECTORY + "/" + match
        #             settings["repeat"] = False
        #             settings["reload"] = True
        #             pygame.mixer.music.stop()
        #             break
        #         else:
        #             settings["playlist"] = DEFAULT_DIRECTORY
        #             settings["repeat"] = False
        #             settings["reload"] = True
        #             pygame.mixer.music.stop()
        #             break
        #     else:
        #         print("Unable to find playlist")
        elif cmd.startswith("play "):
            song_name = cmd[len("play "):].strip() #song_name doesn't necessarily have to be a name, could a number
            
            if (song_name.strip()).isdigit() and int(song_name.strip()) <= settings["num_songs"]:
                match = song_from_index(song_name, output="index")
                settings["count"] = match - 1
                pygame.mixer.music.stop()
            else:
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
                    
                    add_song_to_default_playlist_via_file_directory(file_path)
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
            
        elif cmd.startswith("playlist"):
            if cmd == "playlist":
                playlists = pl.playlist_list()
                print()
                for playlist in playlists: print(playlist)
                
            elif cmd.startswith("playlist create "):
                playlist_name = cmd[len("playlist create "):].strip()
                # pl = Playlist()
                pl.create_playlists(playlist_name)
                
            elif cmd.startswith("playlist select "):
                playlist_name = cmd[len("playlist select "):].strip()
                pl.select_playlist(playlist_name)
                
            elif cmd.startswith("playlist add "):
                song_query = cmd[len("playlist add "):].strip()
                # print(settings["num_songs"])
                while True:
                    if (song_query.strip()).isdigit() and int(song_query.strip()) <= settings["num_songs"]:
                        index = (int(song_query) + settings["count"]) % settings["num_songs"]
                        selected_song = ((settings["song_dict"])[index])[0]  #need to loop this to prevent index error
                        confirmation = input(f"Add {selected_song} to playlist? (yes/no) \n")
                        if confirmation.lower() == "yes":
                            pl.add_song(DEFAULT_DIRECTORY + "/" + selected_song)
                            break
                        else: 
                            print("Operation Cancelled")
                            break
                        
                    if song_query == 'x':
                        print("Operation Cancelled")
                        break
                    song_directory = search_song(song_query)
                    if song_directory == None:
                        song_query = input("Unable to find song, please enter the song you want to add (enter x to quit): ")
                    else:
                        # print(song_directory)
                        confirmation = input(f"Add {song_directory} to playlist? (yes/no) \n")
                        if confirmation.lower() == "yes":
                            pl.add_song(DEFAULT_DIRECTORY + "/" + song_directory)
                            break
                        else: 
                            print("Operation Cancelled")
                            break
                        
            elif cmd.startswith("playlist remove "): #index search has the 0 error issue
                song_query = cmd[len("playlist remove "):].strip()
                if (song_query.strip()).isdigit() and int(song_query.strip()) <= settings["num_songs"]:
                    song_directory = ""
                    if settings["count"] != 0:
                        song_directory = song_from_index(int(song_query) + 1)
                    else:
                        song_directory = song_from_index(song_query)
                    
                    # print("song directory: " + song_directory)
                    
                    confirmation = input(f"Delete {song_directory} from playlist {pl.selected_playlist}? (yes/no) \n")
                    if confirmation.lower() == "yes":
                        pl.delete_song(DEFAULT_DIRECTORY + "/" + song_directory)
                    else:
                        print("Operation Cancelled")
                        
                else:
                    song_directory = search_song(song_query)
                    if song_directory == None:
                        print("Unable to find song; operation cancelled")
                    else:
                        # print(song_directory)
                        confirmation = input(f"Delete {song_directory} from playlist {pl.selected_playlist}? (yes/no) \n")
                        if confirmation.lower() == "yes":
                            pl.delete_song(DEFAULT_DIRECTORY + "/" + song_directory)
                        else:
                            print("Operation Cancelled")
                    
                
                
                
            elif cmd.startswith("playlist switch "):
                playlist_query = cmd[len("playlist switch "):].strip()
                
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                
                cursor.execute("""
                        SELECT playlist_name FROM playlist
                    """)
                
                playlists = [row[0] for row in cursor.fetchall()]
                
                match = search_query(playlist_query, playlists)
                if match:
                    if match != settings["playlist"]:
                        settings["playlist"] = match
                        settings["repeat"] = False
                        settings["reload"] = True
                        pygame.mixer.music.stop()
                        break
                    else:
                        print("You are already listening to the playlist!")
                else:
                    print("Unable to find playlist")
                                    
            #     playlists = [entry.name for entry in os.scandir(DEFAULT_DIRECTORY) if entry.is_dir()]
            #     playlists.append(DEFAULT_DIRECTORY)
                
            #     playlist_query = cmd[len("playlist "):].strip()
                        
                
            

        elif cmd == "test":
            pl.delete_song("music/Muse - Starlight [Official Music Video].mp3")
            
        elif cmd == "test2":
            database_check()
            
        #debug
        
        elif cmd == "num_songs":
            print(settings["num_songs"])
        elif cmd == "count":
            print(settings["count"])
        elif cmd == "song_dict":
            print(settings["song_dict"])
            
            
            
async def player(pl : Playlist):
    # songs =  [f for f in os.listdir(settings["playlist"]) if f.endswith('.mp3')]
    
    # song_paths = []
    
    # queue_order = 0
    
    # for song in songs: #song paths
    #     decoded_song = unquote(song) 
    #     song_path = os.path.join(settings["playlist"], decoded_song)
    #     # (settings["song_names"]).append(decoded_song)
    #     song_paths.append(song_path)
        
    #     (settings["song_dict"])[queue_order] = (decoded_song, song_path)
    #     queue_order += 1
    #     settings["num_songs"]+=1
    #     if settings["debug"]:
    #         print("num_songs_main is: " + str(settings["num_songs"]))
    
    # song_paths = []
    
    database_check() #check if any songs are not in the database

    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT playlist_song FROM playlist
    WHERE playlist_name = ?
    """, (settings["playlist"],))
    
    song_pk = ((cursor.fetchall())[0])[0]
    # print(f"song_pk = {song_pk}")
    
    pk_list = song_pk.split(",")
    pk_list.pop()
    # print(pk_list)
    
    placeholders = ",".join("(?, ?)" for _ in pk_list)
    sql = f"""
    WITH ids(id, ord) AS (VALUES {placeholders})
    SELECT a.file_directory
    FROM allsongs AS a
    JOIN ids ON a.song_id = ids.id
    ORDER BY ids.ord;
    """
    params = []
    for i, pk in enumerate(pk_list):
        params.extend((pk, i))

    cursor.execute(sql, params)
    file_dirs = [row[0] for row in cursor.fetchall()]
    
    # print(len(file_dirs))
    # print(file_dirs)
    
    settings["num_songs"] = len(file_dirs)

    queue_order = 0
    
    for song_dir in file_dirs:
        (settings["song_dict"])[queue_order] = (song_dir[len(DEFAULT_DIRECTORY + "/"):].strip(), song_dir)
        queue_order += 1
        # settings["num_songs"]+=1 no need to count anymore
            
        
    print("Queue: ")
    # queue_count = 0
    for song in range(1, settings["num_songs"] + 1):
        # queue_count += 1
        print(f"    {song}. {((settings["song_dict"])[song - 1])[0]}")
    print()
    
    while True: #the main player loop
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
        pl = Playlist()
        pl.universal_playlist() #in process of switching to playlist-based playing
        await asyncio.gather(player(pl), user_conts(pl))
        

asyncio.run(run_player())