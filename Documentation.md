## Version 0.1 Beginning of Versioning:
- Lyrics
    - Artist name and song name found via duck duck go search and using the format of the genius website title that is usually the first result returned.
    - Lyrics provided by lyrics.ovh, a free key-less API
    - Lyrics saved to db.
    - lyrics.ovh is often down

    - Final Flow: Duck duck go search --> song info retrieved --> lyrics.ovh request with song details --> lyrics stored to db

## Version 0.2 Playlist Rework:
- Playlists
    - Reimplemented playlists to no longer rely on a folder-based system and now uses a .db implementation with songs being saved in a string of their PKs.
    - Reworked main-loop to use references to the database instead of scanning the folder.
    - Added meta-fields to the .db, to be implemented in the future.
    - Ability to create, delete, modify (add or remove songs) playlists, and add a playlist description (edit yet to be implemented).
    - Implemented a universal playlist with PKs of all songs.