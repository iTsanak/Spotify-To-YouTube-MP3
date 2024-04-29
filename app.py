from flask import Flask, url_for, session, request, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
from dotenv import load_dotenv
import os
import pandas as pd
from mp3Downloader import DownloadVideosFromTitles


app = Flask(__name__)
app.secret_key = "fzjmaonfow20"
app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session'
TOKEN_INFO = 'token_info'                                   # Dictionary key for the token info in the session
load_dotenv()

'''
This route is called when the user wants to login to Spotify.
'''
@app.route('/')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

'''
This route is called when the user is redirected from the Spotify login page.
The code is in the request, so we use it to get the token info and save it to the session.    
'''
@app.route('/redirect')
def redirectPage():
    sp_oauth = create_spotify_oauth()                       # Create the SpotifyOauth object
    session.clear()                     
    code = request.args.get('code')                         # Get the code from the request
    token_info = sp_oauth.get_access_token(code)            # Get the token info from the code
    session[TOKEN_INFO] = token_info                        # Save the token info to the session
    return redirect(url_for('getTracks', _external=True))           

@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')

@app.route('/getTracks')
def getTracks():
    try:
        token_info = get_token()
    except:
        print("Error: User not signed in")
        return redirect(url_for('login', _external=False))  
    cur_playlist_name = "Liked Songs"              # The name of the playlist to get the tracks from
    sp = spotipy.Spotify(auth=token_info['access_token'])   # Create a Spotify object with the access token
    playlists = sp.current_user_playlists()
    cur_playlist_id = None
    for playlist in playlists['items']:
        if playlist['name'] == cur_playlist_name:
            cur_playlist_id = playlist['id']
            break
    
    all_songs = []
    iteration = 0
    track_names = []
    if cur_playlist_id is None:
        if cur_playlist_name == 'Liked Songs':
            while True:
                items = sp.current_user_saved_tracks(limit=50, offset=iteration * 50)['items'] # Get the user's saved tracks (50 at a time, starting from the first track)
                iteration += 1
                all_songs += items
                if len(items) < 50:
                    break
            track_names = [item['track']['name'] + "," + item['track']['artists'][0]['name'] for item in all_songs] 
        else:
            print("Error: Playlist not found")
            return redirect(url_for('login', _external=False))
    
    if cur_playlist_id:
        while True:
            items = sp.playlist_tracks(cur_playlist_id, limit=50, offset=iteration * 50)['items'] # Get the user's saved tracks (50 at a time, starting from the first track)
            iteration += 1
            all_songs += items
            if len(items) < 50:
                break
        track_names = [item['track']['name'] + "," + item['track']['artists'][0]['name'] for item in all_songs] 
    df = pd.DataFrame(track_names, columns=["song names"]) 
    df.to_csv('songs.csv', index=False)
    return "Done"

'''
This function gets the token info from the session and returns the access token.
'''
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        raise Exception("Token info not found in session")
    now = int(time.time())
    if token_info['expires_at'] - now < 60: # If the token is about to expire in 60 seconds
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info

'''
This function creates a SpotifyOAuth object with the client_id, client_secret and redirect_uri.
'''
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=os.getenv('SPOTIPY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
        redirect_uri=url_for('redirectPage', _external=True),
        scope='user-library-read'
    )
