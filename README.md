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

In-progress features: Version 0.2 Song storage overhaul

- Reform playlists
    - A single master folder of songs
    - Metadata of songs stored in the .db
    - Playlist information stored in database entries structured like <1,18,19, ...> (the numbers being pk's of the songs)
    - Create, delete playlists
    - Method to add new songs externally added to the database
    - Add a new column, "date added" to the database.


Future features:
- Weighted skips
    - Store information on skips (including shuffles, searches) and fully listened to.
    - We could actually try ML for this
- Chrome extension to analyse Youtube Music song choices
- UI 
    - UI will be used to create playlists and offer playlist management services
    - Actually might need to turn music into the master folder so that songs can be added
    - Features to be added: Create, Clone, Archive and Delete
- Duplication detection
- Better application file structure; split by responsibility [implement in 0.3?]
- Delete songs
- Background or automated lyrics extraction to compensate for lyrics.ovh

- Ability to speed up/ slow down songs
- Expanded metadata file
    - Times listened to
    - Times skipped
    - Genre/ tags
- A help function because I can barely remember all the function keywords and I made this thing

- Lyrics 2.0
    - Sync lyrics to music (more difficult, but we will see)
    - Improve the system of getting artist and song details; allows users to directly modify or provide the details
    - Improve the formatting of the lyrics
    - Allow users to directly add or edit lyrics for any song (may have to wait for UI)

Bugs:
- Not really a bug but the search service is imprecise at times, should find a replacement similar to the 'z' used in terminal.
