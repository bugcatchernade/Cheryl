import discord
from discord.ext import commands, tasks
import os
import asyncio
import aiohttp
import aiofiles
from openai import OpenAI
from bs4 import BeautifulSoup
from requests_html import AsyncHTMLSession
from dotenv import load_dotenv
from pydub import AudioSegment
import feedparser
import speech_recognition as sr
import logging
from rss_feeds import rss_feeds

logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s %(message)s', level=logging.INFO)

# Setup Discord bot
load_dotenv()
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = OpenAI()
bot = commands.Bot(command_prefix='!', intents=intents)
CHANNEL_ID_FEED = 1088835166878842961

# Initialize RSS feed tracking
def initialize_latest_entries_published(feed_group):
    return {feed: None for feed in feed_group}

latest_entries_published = initialize_latest_entries_published(rss_feeds)

async def scrape_titles_and_paragraphs(url):
    session = AsyncHTMLSession()
    response = await session.get(url)
    await response.html.arender()
    soup = BeautifulSoup(response.html.html, 'html.parser')
    titles = [title.text for title in soup.find_all('h1') + soup.find_all('h2') + soup.find_all('h3')]
    paragraphs = [p.text for p in soup.find_all('p')]
    prompt = "\n\n".join(titles + paragraphs)
    await session.close()
    return prompt

# EVENTS
@bot.event
async def on_ready():
    logging.info(f' Logged in as {bot.user} (ID: {bot.user.id})')
    post_rss.start()

@tasks.loop(minutes=15)
async def post_rss():
    await post_rss_group(rss_feeds, latest_entries_published, CHANNEL_ID_FEED)

async def post_rss_group(rss_feeds, latest_entries_published, channel_id):
    channel = bot.get_channel(channel_id)
    async with aiohttp.ClientSession() as session:
        for feed_name, feed_url in rss_feeds.items():
            async with session.get(feed_url) as response:
                feed = feedparser.parse(await response.text())
                if not feed.entries:
                    continue
                latest_entry = feed.entries[0]
                latest_entry_published = latest_entries_published[feed_name]
                if latest_entry_published is None or latest_entry.published_parsed > latest_entry_published:
                    content = f"**{feed_name}**\n({latest_entry.link})"
                    content = content[:2000]  # Truncate content to 2000 characters if it's longer
                    await channel.send(content)
                    latest_entries_published[feed_name] = latest_entry.published_parsed

# COMMANDS

@bot.command()
async def reminder(ctx, time: int, *, text: str):
    await ctx.send(f"Reminder set! I'll remind you in {time} minutes.")
    await asyncio.sleep(time * 60)  # Convert minutes to seconds
    await ctx.author.send(f"Hi, {ctx.author.name}! This is your reminder: {text}")

@bot.command()
async def chat(ctx, *, arg):
    try:
        result = client.chat.completions.create(
            model="gpt-3.5-turbo",
            max_tokens=4000,
            messages=[{'role': 'user', 'content': arg}],
            temperature=0.9
        )
        await ctx.send(result.choices[0].message.content.strip())
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

@bot.command()
async def readme(ctx, url: str):
    prompt = await scrape_titles_and_paragraphs(url)
    prompt = f"Summarize the following content:\n\n{prompt}"
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            max_tokens=4000,
            n=1,
            stop=None,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.5
        )
        summary = response.choices[0].message.content.strip()
        await ctx.send(f"Summary:\n{summary}")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

@bot.command()
async def speech(ctx):
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        file_path = os.path.join("audio", attachment.filename)
        wav_file_path = os.path.join("audio", f"{attachment.filename.split('.')[0]}.wav")

        # Download the audio file asynchronously
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(await attachment.read())

        # Convert the audio to WAV using pydub (synchronous, unavoidable)
        audio = AudioSegment.from_file(file_path)
        audio.export(wav_file_path, format="wav")
        os.remove(file_path)

        recognizer = sr.Recognizer()

        # Transcribe the audio
        try:
            with sr.AudioFile(wav_file_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
                prompt = f"Give me a detailed summary of the following message: {text}"
                result = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    max_tokens=2000,
                    messages=[{'role':'user', 'content': prompt}],
                    temperature=0.9
                )
                await ctx.send(result.choices[0].message.content.strip())
        except sr.UnknownValueError:
            await ctx.send("Speech Recognition could not understand the audio")
        except sr.RequestError as e:
            await ctx.send(f"Could not request results from Google Speech Recognition service; {e}")
        finally:
            os.remove(wav_file_path)
    else:
        await ctx.send("Please attach an AMR or MP3 audio file.")

bot.run(os.getenv("DISCORD_KEY"))
