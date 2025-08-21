Current features:
- Pause, unpause
- Skip forward or return 1 song
- Random skip
- Shuffle
- Display queue
- Play specific song
- Added a search function for queries for playlists or songs so they do not have to be exact
- Playlists
- Song Downloader

In-progress features:
- Lyrics
    - Find a service which provides lyrics for songs
        - lyrics.ovh is API-free which means less hassle for the user
        - I'm thinking the flow could be:
            - User inputs song or user downloads song
            - Format the song data into artist name and song name (chatgpt? but needs an API, could use google)
            - Use lyrics.ovh to get the lyrics
    - Save the lyrics (might want to implement a db song paths and lyrics are stored for efficiency instead of interating through the whole folder)
    - OPTIONAL: Sync lyrics to music (more difficult, but we will see)

Future features:
- Weighted skips
    - Store information on skips (including shuffles, searches) and fully listened to.
    - We could actually try ML for this
- Chrome extension to analyse Youtube Music song choices
- UI 
    - UI will be used to create playlists and offer playlist management services
    - Actually might need to turn music into the master folder so that songs can be added
    - Features to be added: Create, Clone, Archive and Delete