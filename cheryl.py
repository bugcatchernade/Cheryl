import openai
import discord
from discord.ext import commands
import os
import random
import pandas as pd
import time
from dotenv import load_dotenv
from pydub import AudioSegment
import speech_recognition as sr

class Colors():
    GREEN = '\u001b[32m'
    YELLOW = '\u001b[33m'
    CYAN = '\u001b[36m'
    DEFAULT = '\u001b[0m'
    MAGENTA = '\u001b[35m'




intents = discord.Intents.default()
intents.members = True
intents.message_content = True
openai.api_key = os.getenv("OPENAI_KEY")
bot = commands.Bot(command_prefix='!', intents=intents)
load_dotenv()



# EVENTS
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.event
async def on_message(message):
    if message.content > 15:
        
        rand_int = random.randint(1,10)

        if message.author.name == 'Da Viper Lgnd' and rand_int == 7:

            result = openai.Completion.create( model="text-davinci-003", max_tokens=4000, prompt=message.content, temperature=0.9)

            await message.channel.send(result["choices"][0]["text"])


        if message.author.name == 'Ape' and rand_int == 5:

            result = openai.Completion.create(model="text-davinci-003", max_tokens=4000, prompt=message.content, temperature=0.9)
            await message.channel.send(result["choices"][0]["text"])

        await bot.process_commands(message)
    else:
        return





### COMMANDS

@bot.command()
async def joined(ctx, member: discord.Member):
    """Says when a member joined."""
    await ctx.send(f'{member.name} joined {discord.utils.format_dt(member.joined_at)}')


@bot.command()
async def chat(ctx, * , arg):

    result = openai.Completion.create(
            model="text-davinci-003",
            max_tokens = 4000,
            prompt= arg,
            temperature=0.9
)
    await ctx.send(result["choices"][0]["text"])

@bot.command()
async def image(ctx, * , arg):

    result = openai.Image.create(
            prompt= arg,
            n=2,
            size = "1024x1024"
)
    await ctx.send(result["data"][0]["url"])

@bot.command()
async def audiototext(ctx):
    # Check if the message has an attachment
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        file_path = os.path.join("audio", f"{attachment.filename}")
        wav_file_path = os.path.join("audio", f"{attachment.filename.split('.')[0]}.wav")

        # Download the audio file
        await attachment.save(file_path)

        # Get the file extension and format
        file_extension = file_path.split('.')[-1]
        audio_format = 'amr' if file_extension.lower() == 'amr' else 'mp3'

        # Convert the audio to WAV
        audio = AudioSegment.from_file(file_path, format=audio_format)
        audio.export(wav_file_path, format="wav")

        # Remove the original audio file
        os.remove(file_path)

        # Transcribe the audio
        with sr.AudioFile(wav_file_path) as source:
            audio = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio)
                await ctx.send(f"Transcription: {text}")
            except sr.UnknownValueError:
                await ctx.send("Speech Recognition could not understand the audio")
            except sr.RequestError as e:
                await ctx.send(f"Could not request results from Google Speech Recognition service; {e}")

        # Remove the WAV file
        os.remove(wav_file_path)
    else:
        await ctx.send("Please attach an AMR or MP3 audio file.")

bot.run(os.getenv("DISCORD_KEY"))