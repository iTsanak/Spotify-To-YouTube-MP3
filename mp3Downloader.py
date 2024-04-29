#from bs4 import BeautifulSoup
#from requests_html import AsyncHTMLSession
from pathlib import Path
import youtube_dl
import pandas
import asyncio
import os
from pyppeteer import launch  # Import the launch function for Pyppeteer

# This function is called when the user wants to download the songs from the playlist.
# It uses the song names to get the video ids from YouTube and then calls DownloadVideosFromIds().
# The song names are passed as a list.
async def DownloadVideosFromTitles(titles, browser):
    id_list = []
    for title in titles:
        vid_id = await ScrapeVidId(title, browser)
        #print("Video id:", vid_id)
        if vid_id:
            id_list.append(vid_id)
            #print("Added video id:", title)
    await DownloadVideosFromIds(id_list)


# This function is called to get the video id of a song from YouTube.
# It uses Pyppeteer to scrape the video id from the YouTube search results.
# The query is the song name.
async def ScrapeVidId(query, browser):
    print("Getting video id for:", query)
    BASIC = "http://www.youtube.com/results?search_query="
    URL = BASIC + query.replace(',', '+').replace(' ', '+')
    try:
        page = await browser.newPage()
        print("Opening page:", URL)
        await page.goto(URL)
        await page.waitForSelector('#video-title')
        results = await page.querySelector('#video-title')
        if results:
            print("Found video id for:", query)
            element = await results.getProperty('href')
            vid_id = await element.jsonValue()
            vid_id = vid_id.split("/watch?v=")[1]
            #print("Video id:", vid_id)
            await page.close()
            return vid_id
    except Exception as e:
        print("An error occurred:", e)
    return None

# This function is called to download the songs from YouTube.
# It uses the video ids to download the songs.
# The video ids are passed as a list.
async def DownloadVideosFromIds(ids):
    #print('Entered download videos from ids')
    SAVE_PATH = os.path.join(Path.home(), "Downloads", "songs")
    print("Downloading songs to:", SAVE_PATH)
    try:
        os.mkdir(SAVE_PATH)
    except:
        print("Download folder exists")
    # Settings for the YouTube downloader
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': SAVE_PATH + '/%(title)s.%(ext)s',
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download(ids)

# This function is called to get the video id of a song from YouTube.
# It uses the requests_html library to scrape the video id from the YouTube search results.
# The query is the song name.
async def main():
    data = pandas.read_csv('songs.csv')
    song_names = data['song names'].tolist()
    print("Found", len(song_names), "songs!")
    browser = await launch()
    try:
        await DownloadVideosFromTitles(song_names, browser)
    finally:
        await browser.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("An error occurred:", e)
        
