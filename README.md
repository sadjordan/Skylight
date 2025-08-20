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
- Song Downloader:
    - Search function for songs on YouTube (100%)
        - Search via terminal
        - Immediate return of result
            - OPTIONAL: Return results other than the top
        - Confirmation of download
    - API or function to download (100%) — using a library
    - Add to playlists (or master folder) (100%) — saved in music folder

- Lyrics
    - Find a service which provides lyrics for songs
    - Save the lyrics (might want to implement a db song paths and lyrics are stored for efficiency instead of interating through the whole folder)
    - Sync lyrics to music (more difficult, but we will see)

Future features:
- Weighted skips
    - Store information on skips (including shuffles, searches) and fully listened to.
    - We could actually try ML for this
- Chrome extension to analyse Youtube Music song choices
- UI 
    - UI will be used to create playlists and offer playlist management services
    - Actually might need to turn music into the master folder so that songs can be added
    - Features to be added: Create, Clone, Archive and Delete