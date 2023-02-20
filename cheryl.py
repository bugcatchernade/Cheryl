import openai
import discord
from discord.ext import commands
import os
import random
from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.endpoints import scoreboardv2
import joblib
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures
from sklearn.preprocessing import OneHotEncoder
import time
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from dotenv import load_dotenv


class Colors():
    GREEN = '\u001b[32m'
    YELLOW = '\u001b[33m'
    CYAN = '\u001b[36m'
    DEFAULT = '\u001b[0m'
    MAGENTA = '\u001b[35m'


intents = discord.Intents.default()
intents.members = True
intents.message_content = True
openai.api_key = load_dotenv("OPENAI_KEY")
bot = commands.Bot(command_prefix='!', intents=intents)
teams = teams.get_teams()




# EVENTS
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.event
async def on_message(message):
    rand_int = random.randint(1,10)

    if message.author.name == 'Da Viper Lgnd' and rand_int == 7:

        result = openai.Completion.create( model="text-davinci-003", max_tokens=4000, prompt=message.content, temperature=0.9)

        await message.channel.send(result["choices"][0]["text"])


    elif message.author.name == 'Ape' and rand_int == 5:

        result = openai.Completion.create(model="text-davinci-003", max_tokens=4000, prompt=message.content, temperature=0.9)
        await message.channel.send(result["choices"][0]["text"])

    await bot.process_commands(message)






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
async def code(ctx, arg):

    response = openai.Completion.create(
         model="content-filter-alpha",
         prompt = "<|endoftext|>"+ arg +"\n--\nLabel:",
         temperature=0,
         max_tokens=1,
         top_p=0,
         logprobs=10)

    await ctx.send(response)



@bot.command()
async def NBA(ctx):
    await ctx.send('Charlotte Hornets = CHA\nDetroit Pistons = DET\nIndiana Pacers = IND\nGS Warriows = GSW\nOrlando Magic = ORL\nAtlanta Hawks = ATL\nToronto Raptors = TOR\nSacramento Kings = SAC\nChicago Bulls = CHI\nNY Knicks = NYK\nOKC Thunder = OKC\nMiami Heat = MIA\nSA Spurs = SAS\nPortland Trailblazers = POR\nDallas Mavericks = DAL\nCleveland Cavs = CLE\nDenver Nuggets = DEN\nWashington Wizards = WAS\nLA Clippers = LAC\nMinnesota T-Wolves = MIN')


@bot.command()
async def predict(ctx, arg1, arg2):
    # Load models
    forest_model = joblib.load('models/forest_reg_model.pkl')
    lin_model = joblib.load('models/lin_reg_model.pkl')
    tree_model = joblib.load('models/tree_reg_model.pkl')
    grid_model = joblib.load('models/grid_search_model.pkl')
    ridge_model = joblib.load('models/ridge_reg_model.pkl')

    # Get user input
    recent_games = 10 #input('How many recent games? ')
    # [HOME, AWAY]
    match_list = [[arg1,arg2]]


    for match in match_list:
        home = match[0]
        away = match[1]
        home_info = [x for x in teams if x['abbreviation'] == home][0]
        away_info = [x for x in teams if x['abbreviation'] == away][0]
        
        # Get Team data
        home_log = leaguegamefinder.LeagueGameFinder(team_id_nullable=home_info['id']).get_data_frames()[0]
        away_log = leaguegamefinder.LeagueGameFinder(team_id_nullable=away_info['id']).get_data_frames()[0]
        home_log = home_log.head(int(recent_games))
        away_log = away_log.head(int(recent_games))
        prediction_list = []

        # Use this for direct input
        #home_fg_pct = input('HOME FG%: ')
        #away_fg_pct = input('AWAY FG%: ')
        #home_feature_list = [1, round(away_log['FGA'].mean()), round(away_log['FG3A'].mean()), round(away_log['FTA'].mean()), round(away_log['PF'].mean()), round(away_log['REB'].mean()),round(away_log['DREB'].mean()),round(away_log['STL'].mean()),round(away_log['BLK'].mean()),round(home_log['AST'].mean()), home_fg_pct, round(home_log['TOV'].mean()), round(home_log['FGA'].mean()), round(home_log['FG3A'].mean()), round(home_log['FG3_PCT'].mean(),3)]
        #away_feature_list = [0, round(home_log['FGA'].mean()), round(home_log['FG3A'].mean()), round(home_log['FTA'].mean()), round(home_log['PF'].mean()), round(home_log['REB'].mean()),round(home_log['DREB'].mean()),round(home_log['STL'].mean()),round(home_log['BLK'].mean()),round(away_log['AST'].mean()), away_fg_pct, round(away_log['TOV'].mean()), round(away_log['FGA'].mean()), round(away_log['FG3A'].mean()), round(away_log['FG3_PCT'].mean(),3)]

        # Use this for auto-retrieve
        home_feature_list = [1, round(away_log['FGA'].mean()), round(away_log['FG3A'].mean()), round(away_log['FTA'].mean()), round(away_log['PF'].mean()), round(away_log['REB'].mean()),round(away_log['DREB'].mean()),round(away_log['STL'].mean()),round(away_log['BLK'].mean()),round(home_log['AST'].mean()),round(home_log['FG_PCT'].mean(), 3), round(home_log['TOV'].mean()), round(home_log['FGA'].mean()), round(home_log['FG3A'].mean()), round(home_log['FG3_PCT'].mean(),3), round(home_log['REB'].mean())]
        away_feature_list = [0, round(home_log['FGA'].mean()), round(home_log['FG3A'].mean()), round(home_log['FTA'].mean()), round(home_log['PF'].mean()), round(home_log['REB'].mean()),round(home_log['DREB'].mean()),round(home_log['STL'].mean()),round(home_log['BLK'].mean()),round(away_log['AST'].mean()),round(away_log['FG_PCT'].mean(), 3), round(away_log['TOV'].mean()), round(away_log['FGA'].mean()), round(away_log['FG3A'].mean()), round(away_log['FG3_PCT'].mean(),3), round(away_log['REB'].mean())]
        prediction_list.append(home_feature_list)
        prediction_list.append(away_feature_list)


        # Put features into dataframe
        features = pd.DataFrame(prediction_list, columns=['HOME_AWAY','FGA_AGST', 'FG3A_AGST', 'FTA_AGST', 'PF_AGST', 'REB_AGST', 'DREB_AGST', 'STL_AGST', 'BLK_AGST', 'AST_FOR','FG_PCT_FOR', 'TOV_FOR', 'FGA_FOR', 'FG3A_FOR','FG3_PCT_FOR', 'REB_FOR'])
        features = features.drop(['FG3A_AGST','REB_AGST','FTA_AGST','FGA_AGST'], axis=1)

        # Transform Pipeline
        imputer = SimpleImputer(strategy='median')
        # Since median can only be computed on #'s we copy data with text categories
        stats_num = features.drop('HOME_AWAY', axis=1)
        imputer.fit(stats_num)
        # Use imputer on dataset to replace missing values with learned medians
        X = imputer.transform(stats_num)
        # Put the data back into a dataframe
        stats_tr = pd.DataFrame(X, columns=stats_num.columns, index=stats_num.index)
        num_pipeline = Pipeline([('imputer', SimpleImputer(strategy='median')), ('std_scaler', StandardScaler())])
        stats_num_tr = num_pipeline.fit_transform(stats_num)
        num_attribs = list(stats_num)
        cat_attribs = ['HOME_AWAY']
        full_pipeline = ColumnTransformer([('num', num_pipeline, num_attribs), ('cat', OneHotEncoder(), cat_attribs)])
        # Final prepared data
        stats_prepared = full_pipeline.fit_transform(features)

        # Make predictions based on features
        trans = PolynomialFeatures(degree=3)
        trans_x = trans.fit_transform(stats_prepared)
        scores = forest_model.predict(stats_prepared)
        scores2 = lin_model.predict(trans_x)
        scores3 = tree_model.predict(stats_prepared)
        scores4 = grid_model.predict(stats_prepared)
        scores5 = ridge_model.predict(stats_prepared)
        ens_avg_home = round((scores[0] + scores2[0] + scores3[0] + scores4[0] + scores5[0]) / 5)
        ens_avg_away = round((scores[1] + scores2[1] + scores3[1] + scores4[1] + scores5[1]) / 5)

        str0 = 'HOME -> %s | AWAY -> %s' % (home, away)
        str1 = '\nForest Predictions: ' + '%s %d %s %d' % (home, scores[0], away, scores[1]) + ' Total: %d ' % round(scores[0] + scores[1],2)
        str2 = '\nLinear Predictions: ' + '%s %d %s %d' % (home, scores2[0], away, scores2[1]) + ' Total: %d ' % round(scores2[0] + scores2[1],2)
        str3 = '\nDecision Tree Predictions: ' + '%s %d %s %d' % (home, scores3[0], away, scores3[1]) + ' Total: %d ' % round(scores3[0] + scores3[1],2)
        str4 = '\nGrid Predictions: ' + '%s %d %s %d' % (home, scores4[0], away, scores4[1]) + ' Total: %d ' % round(scores4[0] + scores4[1],2)
        str5 = '\nRidge Predictions: ' + '%s %d %s %d' % (home, scores5[0], away, scores5[1]) + ' Total: %d ' % round(scores5[0] + scores5[1],2)
        str6 = '\nAverage: ' + '%s %d %s %d' % (home, ens_avg_home, away, ens_avg_away) + ' Total: %d ' % round(ens_avg_home + ens_avg_away,2)
        final_output = '```' + str0 + str1 + str2 + str3 + str4 + str5 + str6 + '```'
        await ctx.send(final_output)
      

bot.run(load_dotenv("DISCORD_KEY"))