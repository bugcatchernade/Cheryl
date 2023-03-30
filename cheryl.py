import openai
import discord
from discord.ext import commands, tasks
from discord import Embed
import os
import random
import pandas as pd
import time
from dotenv import load_dotenv
from pydub import AudioSegment
import speech_recognition as sr
import feedparser
import asyncio
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from requests_html import AsyncHTMLSession
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-dev-shm-usage")
#chrome_options.add_argument("--remote-debugging-port=9222")

driver = webdriver.Chrome(executable_path="chromedriver", options=chrome_options)
class Colors():
    GREEN = '\u001b[32m'
    YELLOW = '\u001b[33m'
    CYAN = '\u001b[36m'
    DEFAULT = '\u001b[0m'
    MAGENTA = '\u001b[35m'



load_dotenv()
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
openai.api_key = os.getenv("OPENAI_KEY")
print(os.getenv("OPENAI_KEY"))
bot = commands.Bot(command_prefix='!', intents=intents)
rss_feeds_group1 = {
        "IGN": "http://feeds.ign.com/ign/all",
        "PC Gamer": "https://www.pcgamer.com/rss/",
        "Kotaku": "https://kotaku.com/rss",}
rss_feeds_group2 = {
        "ESPN Top Headlines": "http://www.espn.com/espn/rss/news",
        "BBC Sport Top Stories": "http://feeds.bbci.co.uk/sport/rss.xml?edition=int",
        "Yahoo Sports Top News": "https://sports.yahoo.com/rss/",
        "Sports Illustrated Top Stories": "https://www.si.com/rss/si_top_stories.rss",
        "CBS Sports Top Headlines": "https://www.cbssports.com/rss/headlines",
        "NBC Sports Top Stories": "https://profootballtalk.nbcsports.com/feed/",}

rss_feeds_group3 = {
        "BBC World News": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "CNN World News": "http://rss.cnn.com/rss/edition_world.rss",
        "The New York Times - World News": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "Al Jazeera English": "https://www.aljazeera.com/xml/rss/all.xml",
        "The Guardian - World News": "https://www.theguardian.com/world/rss",
        "Reuters - World News": "http://feeds.reuters.com/Reuters/worldNews",
        "NPR World News": "https://feeds.npr.org/1004/rss.xml",}
rss_feeds_group4 = {
        "TechCrunch": "http://feeds.feedburner.com/TechCrunch/",
        "The Verge": "https://www.theverge.com/rss/index.xml",
        "Ars Technica": "http://feeds.arstechnica.com/arstechnica/index",
        "CNET Top Stories": "https://www.cnet.com/rss/news/",
        "Wired Top Stories": "https://www.wired.com/feed/rss",
        "Engadget": "https://www.engadget.com/rss.xml",
        "Bleeping Computer": "https://www.bleepingcomputer.com/feed/",
        "Krebs on Security": "https://krebsonsecurity.com/feed/",
        "The Hacker News": "https://feeds.feedburner.com/TheHackersNews",
        "Dark Reading": "http://www.darkreading.com/rss_simple.asp",
        "Naked Security by Sophos": "https://nakedsecurity.sophos.com/feed/",}


CHANNEL_ID_GROUP1 = 1088767073775259648  #Gaming
CHANNEL_ID_GROUP2 = 1088835086323040409 #Sports
CHANNEL_ID_GROUP3 = 1088835126227632128 #News
CHANNEL_ID_GROUP4 = 1088835166878842961 #Tech

def initialize_latest_entries_published(feed_group):
    return {feed: None for feed in feed_group}
latest_entries_published_group1 = initialize_latest_entries_published(rss_feeds_group1)
latest_entries_published_group2 = initialize_latest_entries_published(rss_feeds_group2)
latest_entries_published_group3 = initialize_latest_entries_published(rss_feeds_group3)
latest_entries_published_group4 = initialize_latest_entries_published(rss_feeds_group4)



async def scrape_titles_and_paragraphs(url):
    session = AsyncHTMLSession()
    response = await session.get(url)
    # Render the JavaScript
    await response.html.arender()
    # Parse the HTML content with Beautiful Soup
    soup = BeautifulSoup(response.html.html, 'html.parser')
    titles = [title.text for title in soup.find_all('h1') + soup.find_all('h2') + soup.find_all('h3')]
    paragraphs = [p.text for p in soup.find_all('p')]
    prompt = "\n\n".join(titles + paragraphs)
    await session.close()
    return prompt



# EVENTS
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    post_rss.start()

#@bot.event
#async def on_message(message):
#        
#        rand_int = random.randint(1,10)
#
#        if message.author.name == 'Da Viper Lgnd' and rand_int == 7:
#
#            result = openai.Completion.create( model="text-davinci-003", max_tokens=4000, prompt=message.content, temperature=0.9)
#
#            await message.channel.send(result["choices"][0]["text"])
#
#
#         if message.author.name == 'Ape' and rand_int == 5:
#
#            result = openai.Completion.create(model="text-davinci-003", max_tokens=4000, prompt=message.content, temperature=0.9)
#            await message.channel.send(result["choices"][0]["text"])
#
 #       await bot.process_commands(message)
    

@tasks.loop(minutes=15)
async def post_rss():
    await post_rss_group(rss_feeds_group1, latest_entries_published_group1, CHANNEL_ID_GROUP1)
    await post_rss_group(rss_feeds_group2, latest_entries_published_group2, CHANNEL_ID_GROUP2)
    await post_rss_group(rss_feeds_group3, latest_entries_published_group3, CHANNEL_ID_GROUP3)
    await post_rss_group(rss_feeds_group4, latest_entries_published_group4, CHANNEL_ID_GROUP4)



async def post_rss_group(rss_feeds, latest_entries_published, channel_id):
    channel = bot.get_channel(channel_id)
    for feed_name, feed_url in rss_feeds.items():
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            continue
        latest_entry = feed.entries[0]
        latest_entry_published = latest_entries_published[feed_name]
        if latest_entry_published is None or latest_entry.published_parsed > latest_entry_published:
            content = f"**{feed_name}**\n({latest_entry.link})"
            content = content[:2000]  # Truncate content to 2000 characters if it's longer
            await channel.send(content)
            latest_entries_published[feed_name] = latest_entry.published_parsed




### COMMANDS

@bot.command()
async def reminder(ctx, time: int, *, text: str):
    await ctx.send(f"Reminder set! I'll remind you in {time} minutes.")
    await asyncio.sleep(time * 60)  # Convert minutes to seconds
    await ctx.author.send(f"Hi, {ctx.author.name}! This is your reminder: {text}")
@bot.command()
async def chat(ctx, * , arg):

    result = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            max_tokens = 4000,
            messages= [{'role': 'user', 'content' : arg}],
            temperature=0.9
)
    await ctx.send(result["choices"][0]["message"]["content"])

@bot.command()
async def image(ctx, * , arg):

    result = openai.Image.create(
            prompt= arg,
            n=2,
            size = "1024x1024"
)
    await ctx.send(result["data"][0]["url"])


@bot.command()
async def readme(ctx, url: str):
    prompt = await scrape_titles_and_paragraphs(url)
    prompt = f"Summarize the following content:\n\n{prompt}"
    # Make the OpenAI API request
    response = openai.Completion.create(engine="text-davinci-002", prompt=prompt, max_tokens=100, n=1, stop=None, temperature=0.5)
    summary = response.choices[0].text.strip()
    await ctx.send(f"Summary:\n{summary}")





@bot.command()
async def speech(ctx):
    print('Audio to txt command')
    # Check if the message has an attachment
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        file_path = os.path.join("audio", f"{attachment.filename}")
        wav_file_path = os.path.join("audio", f"{attachment.filename.split('.')[0]}.wav")

        # Download the audio file
        await attachment.save(file_path)

        # Get the file extension and format
        file_extension = file_path.split('.')[-1]
        if file_extension.lower() == 'amr':
            audio_format = 'amr'
        elif file_extension.lower() == 'mp3':
            audio_format = 'mp3'
        elif file_extension.lower() == 'm4a':
            audio_format = 'm4a'

        # Convert the audio to WAV
        audio = AudioSegment.from_file(file_path, format=audio_format)
        audio.export(wav_file_path, format="wav")

        # Remove the original audio file
        os.remove(file_path)
        recognizer = sr.Recognizer()
        # Transcribe the audio
        with sr.AudioFile(wav_file_path) as source:
            audio = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio)
                prompt = "Give me a detailed summary of the following message " + text
                result = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        max_tokens=2000,
                        messages=[{'role':'user', 'content': prompt}],
                        temperature=0.9)

                await ctx.send(result["choices"][0]["message"]["content"])
            except sr.UnknownValueError:
                await ctx.send("Speech Recognition could not understand the audio")
            except sr.RequestError as e:
                await ctx.send(f"Could not request results from Google Speech Recognition service; {e}")

        # Remove the WAV file
        os.remove(wav_file_path)
    else:
        await ctx.send("Please attach an AMR or MP3 audio file.")

bot.run(os.getenv("DISCORD_KEY"))
