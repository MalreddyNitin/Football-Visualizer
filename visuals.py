import pandas as pd
import numpy as np
from mplsoccer.pitch import Pitch, VerticalPitch
from matplotlib.colors import to_rgba
from matplotlib.patches import ConnectionPatch
from itertools import combinations
import seaborn as sns
import matplotlib.pyplot as plt
from highlight_text import fig_text
from sklearn.cluster import KMeans
import matplotlib as mpl


def createShotmap(events_df, hometeam, awayteam, homeid, awayid, pitchcolor, shotcolor, goalcolor,
                  titlecolor, legendcolor, marker_size):
    #events_df['expectedGoals'] = events_df['expectedGoals'].astype(float)
    total_shots = events_df.loc[(events_df['isOwnGoal'] != True)].reset_index(drop=True)
    team_shots = total_shots.loc[(total_shots['teamId'] == homeid)].reset_index(drop=True)
    # team_shots['x'] = 105 - team_shots['x']
    # team_shots['y'] = 68 - team_shots['y']
    goal = team_shots.loc[(team_shots['type'] == 'Goal')].reset_index(drop=True)
    shot = team_shots.loc[
        team_shots['type'].isin(['MissedShots', 'SavedShot', 'ShotOnPost'])
    ].reset_index(drop=True)

    team_shotso = total_shots.loc[(total_shots['teamId'] == awayid)].reset_index(drop=True)
    team_shotso['x'] = 100 - team_shotso['x']
    goalo = team_shotso.loc[(team_shotso['type'] == 'Goal')].reset_index(drop=True)
    shoto = team_shotso.loc[team_shotso['type'].isin(['MissedShots', 'SavedShot', 'ShotOnPost'])].reset_index(drop=True)
    #print(goalo)

    # Setup the pitch
    # orientation='vertical'
    fig, ax = plt.subplots(figsize=(16, 11))
    pitch = Pitch(pitch_type='opta', pitch_color=pitchcolor, line_color='#c7d5cc',
                  half=False, goal_type='box')  # , pad_top=2)
    pitch.draw(ax=ax, tight_layout=True, constrained_layout=True)

    pitch.scatter(50, 160, s=marker_size,
                  edgecolors='black', c=goalcolor, zorder=2,
                  label='goal', ax=ax)
    pitch.scatter(50, 160, s=marker_size,
                  edgecolors='grey', c=shotcolor, zorder=2,
                  label='shot', ax=ax)
    # Plot the goals
    pitch.scatter(goal.x, goal.y, s = 40, #s=goal.expectedGoals * 900,
                  edgecolors='black', c=goalcolor, zorder=2,
                  ax=ax)
    pitch.scatter(shot.x, shot.y, s = 40,
                  edgecolors='grey', c=shotcolor, #s=shot.expectedGoals * 900,
                  zorder=2,
                  ax=ax)

    pitch.scatter(goalo.x, goalo.y,s=40, #s=goalo.expectedGoals * 900,
                 edgecolors='black', c=goalcolor, zorder=2,
                 ax=ax)
    pitch.scatter(shoto.x, shoto.y,s=40,
                 edgecolors='grey', c=shotcolor, #s=shoto.expectedGoals * 900,
                  zorder=2,
                 ax=ax)
    # Set the title
    ax.set_title(f'{hometeam} vs {awayteam}\n Shotmap', fontsize=30, color=titlecolor)

    # set legend
    leg = ax.legend(facecolor=pitchcolor, edgecolor='None', fontsize=20, loc='lower center', handlelength=4)
    leg_texts = leg.get_texts()  # list of matplotlib Text instances.
    leg_texts[0].set_color(legendcolor)
    leg_texts[1].set_color(legendcolor)

    #ax.scatter(np.array([3, 3+4.27,3+4.27+4.27, 3+4.27+4.27+4.27]), np.array([-1.2] * 4), s=np.array([100, 80, 60, 40]), c='white',
               #edgecolor='w')
    # ax.text(-4.5, -3.6, 'Higher Shot Quality', family='Candara', c='w', size=13)
    # ax.text(5.8+2.8+0.03+0.07+3, -3.6, 'Lower Shot Quality', family='Candara', c='w', size=13)

    # Set the figure facecolor
    fig.set_facecolor(pitchcolor)

    return fig
    
    
    
    


def createPassNetworks(match_data, events_df, matchId, team, max_line_width, 
                       marker_size, edgewidth, dh_arrow_width, marker_color, 
                       marker_edge_color, shrink,  kit_no_size=20):
    
    # getting team id and venue
    if match_data['home']['name'] == team:
        teamId = match_data['home']['teamId']
        venue = 'home'
    else:
        teamId = match_data['away']['teamId']
        venue = 'away'
    
    
    # getting opponent   
    if venue == 'home':
        opponent = match_data['away']['name']
    else:
        opponent = match_data['home']['name']
    
    
    # getting player dictionary
    team_players_dict = {}
    for player in match_data[venue]['players']:
        team_players_dict[player['playerId']] = player['name']
    
    
    # getting minute of first substitution
    for i in events_df.index:
        if events_df.loc[i, 'type'] == 'SubstitutionOn' and events_df.loc[i, 'teamId'] == teamId:
            sub_minute = str(events_df.loc[i, 'minute'])
            break
    
    
    # getting players dataframe
    match_players_df = pd.DataFrame()
    player_names = []
    player_ids = []
    player_pos = []
    player_kit_number = []


    for player in match_data[venue]['players']:
        player_names.append(player['name'])
        player_ids.append(player['playerId'])
        player_pos.append(player['position'])
        player_kit_number.append(player['shirtNo'])

    match_players_df['playerId'] = player_ids
    match_players_df['playerName'] = player_names
    match_players_df['playerPos'] = player_pos
    match_players_df['playerKitNumber'] = player_kit_number
    
    # extracting passes
    passes_df = events_df.loc[events_df['teamId'] == teamId].reset_index().drop('index', axis=1)
    passes_df['playerId'] = passes_df['playerId'].astype('float').astype('Int64')
    if 'playerName' in passes_df.columns:
        passes_df = passes_df.drop(columns='playerName')
    passes_df.dropna(subset=["playerId"], inplace=True)
    passes_df.insert(27, column='playerName', value=[team_players_dict[i] for i in list(passes_df['playerId'])])
    if 'passRecipientId' in passes_df.columns:
        passes_df = passes_df.drop(columns='passRecipientId')
        passes_df = passes_df.drop(columns='passRecipientName')
    passes_df.insert(28, column='passRecipientId', value=passes_df['playerId'].shift(-1))  
    passes_df.insert(29, column='passRecipientName', value=passes_df['playerName'].shift(-1))  
    passes_df.dropna(subset=["passRecipientName"], inplace=True)
    # passes_df = passes_df.loc[events_df['type'] == 'Pass', :].reset_index(drop=True)
    # passes_df = passes_df.loc[events_df['outcomeType'] == 'Successful', :].reset_index(drop=True)
    passes_df = passes_df.loc[passes_df['type'] == 'Pass'].reset_index(drop=True)
    passes_df = passes_df.loc[passes_df['outcomeType'] == 'Successful'].reset_index(drop=True)

    index_names = passes_df.loc[passes_df['playerName']==passes_df['passRecipientName']].index
    passes_df.drop(index_names, inplace=True)
    passes_df = passes_df.merge(match_players_df, on=['playerId', 'playerName'], how='left', validate='m:1')
    passes_df = passes_df.merge(match_players_df.rename({'playerId': 'passRecipientId', 'playerName':'passRecipientName'},
                                                        axis='columns'), on=['passRecipientId', 'passRecipientName'],
                                                        how='left', validate='m:1', suffixes=['', 'Receipt'])
    passes_df = passes_df[passes_df['playerPos'] != 'Sub']
    
    
    # getting team formation
    formation = match_data[venue]['formations'][0]['formationName']
    formation = '-'.join(formation)
    
    
    # getting player average locations
    location_formation = passes_df[['playerKitNumber', 'x', 'y']]
    average_locs_and_count = location_formation.groupby('playerKitNumber').agg({'x': ['mean'], 'y': ['mean', 'count']})
    average_locs_and_count.columns = ['x', 'y', 'count']

    
    # getting separate dataframe for selected columns 
    passes_formation = passes_df[['id', 'playerKitNumber', 'playerKitNumberReceipt', 'playerName', 'passRecipientName']].copy()
    passes_formation['EPV'] = passes_df['EPV']

    
    # getting dataframe for passes between players
    passes_between = passes_formation.groupby(['playerKitNumber', 'playerKitNumberReceipt', 'playerName', 'passRecipientName']).agg({ 'id' : 'count', 'EPV' : 'sum'}).reset_index()        
    passes_between.rename({'id': 'pass_count'}, axis='columns', inplace=True)
    passes_between = passes_between.merge(average_locs_and_count, left_on='playerKitNumberReceipt', right_index=True)
    passes_between = passes_between.merge(average_locs_and_count, left_on='playerKitNumber', right_index=True,
                                          suffixes=['', '_end'])

    
    # filtering passes
    pass_filter = int(passes_between['pass_count'].mean())
    passes_between = passes_between.loc[passes_between['pass_count'] > pass_filter]
    
    
    # calculating the line width 
    passes_between['width'] = passes_between.pass_count / passes_between.pass_count.max() * max_line_width
    passes_between = passes_between.reset_index(drop=True)
    
    
    # setting color to make the lines more transparent when less EPV passes are made
    min_transparency = 0.3
    color = np.array(to_rgba('white'))
    color = np.tile(color, (len(passes_between), 1))
    #c_transparency = passes_between.pass_count / passes_between.pass_count.max()
    #c_transparency = (c_transparency * (1 - min_transparency)) + min_transparency
    c_transparency = passes_between.EPV
    c_transparency = (c_transparency * (1 - min_transparency)) + min_transparency
    color[:, 3] = c_transparency
    passes_between['alpha'] = color.tolist()

    
    # separating paired passes from normal passes
    passes_between_threshold = 15
    filtered_pair_df = []
    pair_list = [comb for comb in combinations(passes_between['playerKitNumber'].unique(), 2)]
    for pair in pair_list:
        df = passes_between[((passes_between['playerKitNumber']==pair[0]) & (passes_between['playerKitNumberReceipt']==pair[1])) |
                            ((passes_between['playerKitNumber']==pair[1]) & (passes_between['playerKitNumberReceipt']==pair[0]))]
        if df.shape[0] == 2:
            if (np.array(df.pass_count)[0] >= passes_between_threshold) and (np.array(df.pass_count)[1] >= passes_between_threshold):
                filtered_pair_df.append(df)
                passes_between.drop(df.index, inplace=True)
    if len(filtered_pair_df) > 0:
        filtered_pair_df = pd.concat(filtered_pair_df).reset_index(drop=True)
        passes_between = passes_between.reset_index(drop=True)
    
    
    # plotting
    fig, ax = plt.subplots(figsize=(16, 11))
    pitch = Pitch(pitch_type='opta', pitch_color='#171717', line_color='#5c5c5c',
                  goal_type='box')
    pitch.draw(ax=ax, constrained_layout=True, tight_layout=True)
    average_locs_and_count['zorder'] = list(np.linspace(1,5,11))
    for i in average_locs_and_count.index:
        pitch.scatter(average_locs_and_count.loc[i, 'x'], average_locs_and_count.loc[i, 'y'], s=marker_size,
                      color=marker_color, edgecolors=marker_edge_color, linewidth=edgewidth, 
                      alpha=1, zorder=average_locs_and_count.loc[i, 'zorder'], ax=ax)
    
    for i in passes_between.index:
        x = passes_between.loc[i, 'x']
        y = passes_between.loc[i, 'y']
        endX = passes_between.loc[i, 'x_end']
        endY = passes_between.loc[i, 'y_end']
        coordsA = "data"
        coordsB = "data"
        con = ConnectionPatch([endX, endY], [x, y],
                              coordsA, coordsB,
                              arrowstyle="simple", shrinkA=shrink, shrinkB=shrink,
                              mutation_scale=passes_between.loc[i, 'width']*max_line_width, color=passes_between.loc[i, 'alpha'])
        ax.add_artist(con)
    
    if len(filtered_pair_df) > 0:
        for i in filtered_pair_df.index:
            x = filtered_pair_df.loc[i, 'x']
            y = filtered_pair_df.loc[i, 'y']
            endX = filtered_pair_df.loc[i, 'x_end']
            endY = filtered_pair_df.loc[i, 'y_end']
            coordsA = "data"
            coordsB = "data"
            con = ConnectionPatch([endX, endY], [x, y],
                                  coordsA, coordsB,
                                  arrowstyle="<|-|>", shrinkA=shrink, shrinkB=shrink,
                                  mutation_scale=dh_arrow_width, lw=filtered_pair_df.loc[i, 'width']*max_line_width/5, 
                                  color=filtered_pair_df.loc[i, 'alpha'])
            ax.add_artist(con)
    
    for i in average_locs_and_count.index:
        pitch.annotate(i, xy=(average_locs_and_count.loc[i, 'x'], average_locs_and_count.loc[i, 'y']), 
                       family='DejaVu Sans', c='white', 
                       va='center', ha='center', zorder=average_locs_and_count.loc[i, 'zorder'], size=kit_no_size, weight='bold', ax=ax)
  #  ax.text(50, 104, "{} (Mins 1-{})".format(team, sub_minute).upper(), size=10, fontweight='bold', ha='center',
          # va='center')
    ax.text(2, 3, '{}'.format(formation), size=9, c='grey')

    def custom_div_cmap(numcolors=11, name='custom_div_cmap',
                        mincol='blue', midcol='white', maxcol='red'):
        """ Create a custom diverging colormap with three colors

        Default is blue to white to red with 11 colors.  Colors can be specified
        in any way understandable by matplotlib.colors.ColorConverter.to_rgb()
        """

        from matplotlib.colors import LinearSegmentedColormap

        cmap = LinearSegmentedColormap.from_list(name=name,
                                                 colors=[mincol, midcol, maxcol],
                                                 N=numcolors)
        return cmap

    custom_map = custom_div_cmap(7, mincol='#A9A9A9', midcol='0.9', maxcol='#FFFFFF')
    #plt.tight_layout()
    N = 7
    #cmap = plt.get_cmap('white', N)
    # Normalizer
    norm = mpl.colors.Normalize(vmin=0, vmax=1)

    # creating ScalarMappable
    sm = plt.cm.ScalarMappable(cmap=custom_map, norm=norm)
    sm.set_array([])

    plt.colorbar(sm, ticks=[] ,ax=ax, location= 'bottom', shrink=0.23,pad=0,anchor=(0.884, 1.46))
    ax.text(72, -2.3, 'Low EPV', size=12, c='grey',zorder=4)
    ax.text(93.8, -2.3, 'High EPV', size=12, c='grey', zorder=4)
    plt.tight_layout()
    #plt.show()
    return fig

    
    
    
    
    
def createAttPassNetworks(match_data, events_df, matchId, team, max_line_width, 
                      marker_size, edgewidth, dh_arrow_width, marker_color, 
                      marker_edge_color, shrink, ax, kit_no_size = 20):
    
    # getting team id and venue
    if match_data['home']['name'] == team:
        teamId = match_data['home']['teamId']
        venue = 'home'
    else:
        teamId = match_data['away']['teamId']
        venue = 'away'
    
    
    # getting opponent   
    if venue == 'home':
        opponent = match_data['away']['name']
    else:
        opponent = match_data['home']['name']
    
    
    # getting player dictionary
    team_players_dict = {}
    for player in match_data[venue]['players']:
        team_players_dict[player['playerId']] = player['name']
    
    
    # getting minute of first substitution
    for i in events_df.index:
        if events_df.loc[i, 'type'] == 'SubstitutionOn' and events_df.loc[i, 'teamId'] == teamId:
            sub_minute = str(events_df.loc[i, 'minute'])
            break
    
    
    # getting players dataframe
    match_players_df = pd.DataFrame()
    player_names = []
    player_ids = []
    player_pos = []
    player_kit_number = []


    for player in match_data[venue]['players']:
        player_names.append(player['name'])
        player_ids.append(player['playerId'])
        player_pos.append(player['position'])
        player_kit_number.append(player['shirtNo'])

    match_players_df['playerId'] = player_ids
    match_players_df['playerName'] = player_names
    match_players_df['playerPos'] = player_pos
    match_players_df['playerKitNumber'] = player_kit_number
    
    
    # extracting passes
    passes_df = events_df.loc[events_df['teamId'] == teamId].reset_index().drop('index', axis=1)
    passes_df['playerId'] = passes_df['playerId'].astype('float').astype('Int64')
    if 'playerName' in passes_df.columns:
        passes_df = passes_df.drop(columns='playerName')
    passes_df.dropna(subset=["playerId"], inplace=True)
    passes_df.insert(27, column='playerName', value=[team_players_dict[i] for i in list(passes_df['playerId'])])
    if 'passRecipientId' in passes_df.columns:
        passes_df = passes_df.drop(columns='passRecipientId')
        passes_df = passes_df.drop(columns='passRecipientName')
    passes_df.insert(28, column='passRecipientId', value=passes_df['playerId'].shift(-1))  
    passes_df.insert(29, column='passRecipientName', value=passes_df['playerName'].shift(-1))  
    passes_df.dropna(subset=["passRecipientName"], inplace=True)
    # passes_df = passes_df.loc[events_df['type'] == 'Pass', :].reset_index(drop=True)
    # passes_df = passes_df.loc[events_df['outcomeType'] == 'Successful', :].reset_index(drop=True)
    passes_df = passes_df.loc[passes_df['type'] == 'Pass'].reset_index(drop=True)
    passes_df = passes_df.loc[passes_df['outcomeType'] == 'Successful'].reset_index(drop=True)

    index_names = passes_df.loc[passes_df['playerName']==passes_df['passRecipientName']].index
    passes_df.drop(index_names, inplace=True)
    passes_df = passes_df.merge(match_players_df, on=['playerId', 'playerName'], how='left', validate='m:1')
    passes_df = passes_df.merge(match_players_df.rename({'playerId': 'passRecipientId', 'playerName':'passRecipientName'},
                                                        axis='columns'), on=['passRecipientId', 'passRecipientName'],
                                                        how='left', validate='m:1', suffixes=['', 'Receipt'])
    passes_df = passes_df[passes_df['playerPos'] != 'Sub']
    
    
    # getting team formation
    formation = match_data[venue]['formations'][0]['formationName']
    formation = '-'.join(formation)
    
    
    # getting player average locations
    location_formation = passes_df[['playerKitNumber', 'x', 'y']]
    average_locs_and_count = location_formation.groupby('playerKitNumber').agg({'x': ['mean'], 'y': ['mean', 'count']})
    average_locs_and_count.columns = ['x', 'y', 'count']
    
    
    # filtering progressive passes 
    passes_df = passes_df.loc[passes_df['EPV'] > 0]

    
    # getting separate dataframe for selected columns 
    passes_formation = passes_df[['id', 'playerKitNumber', 'playerKitNumberReceipt']].copy()
    passes_formation['EPV'] = passes_df['EPV']


    # getting dataframe for passes between players
    passes_between = passes_formation.groupby(['playerKitNumber', 'playerKitNumberReceipt']).agg({ 'id' : 'count', 'EPV' : 'sum'}).reset_index()
    passes_between.rename({'id': 'pass_count'}, axis='columns', inplace=True)
    passes_between = passes_between.merge(average_locs_and_count, left_on='playerKitNumberReceipt', right_index=True)
    passes_between = passes_between.merge(average_locs_and_count, left_on='playerKitNumber', right_index=True,
                                          suffixes=['', '_end'])
    
    
    # filtering passes
    pass_filter = int(passes_between['pass_count'].mean())
    passes_between = passes_between.loc[passes_between['pass_count'] > pass_filter*2]
    
    
    # calculating the line width and marker sizes relative to the largest counts
    passes_between['width'] = passes_between.pass_count / passes_between.pass_count.max() * max_line_width
    passes_between = passes_between.reset_index(drop=True)
    
    
    # setting color to make the lines more transparent when fewer passes are made
    min_transparency = 0.3
    color = np.array(to_rgba('white'))
    color = np.tile(color, (len(passes_between), 1))
    c_transparency = passes_between.EPV / passes_between.EPV.max()
    c_transparency = (c_transparency * (1 - min_transparency)) + min_transparency
    color[:, 3] = c_transparency
    passes_between['alpha'] = color.tolist()
    
    
    # separating paired passes from normal passes
    passes_between_threshold = 20
    filtered_pair_df = []
    pair_list = [comb for comb in combinations(passes_between['playerKitNumber'].unique(), 2)]
    for pair in pair_list:
        df = passes_between[((passes_between['playerKitNumber']==pair[0]) & (passes_between['playerKitNumberReceipt']==pair[1])) | 
                            ((passes_between['playerKitNumber']==pair[1]) & (passes_between['playerKitNumberReceipt']==pair[0]))]
        if df.shape[0] == 2:
            if np.array(df.pass_count)[0]+np.array(df.pass_count)[1] >= passes_between_threshold:
                filtered_pair_df.append(df)
                passes_between.drop(df.index, inplace=True)
    if len(filtered_pair_df) > 0:
        filtered_pair_df = pd.concat(filtered_pair_df).reset_index(drop=True)
        passes_between = passes_between.reset_index(drop=True)
    
    
    # plotting
    pitch = Pitch(pitch_type='opta', pitch_color='#171717', line_color='#5c5c5c',
                  goal_type='box')
    pitch.draw(ax=ax, constrained_layout=True, tight_layout=True)
    
    average_locs_and_count['zorder'] = list(np.linspace(1,5,11))
    for i in average_locs_and_count.index:
        pitch.scatter(average_locs_and_count.loc[i, 'x'], average_locs_and_count.loc[i, 'y'], s=marker_size,
                      color=marker_color, edgecolors=marker_edge_color, linewidth=edgewidth, 
                      alpha=1, zorder=average_locs_and_count.loc[i, 'zorder'], ax=ax)
    
    for i in passes_between.index:
        x = passes_between.loc[i, 'x']
        y = passes_between.loc[i, 'y']
        endX = passes_between.loc[i, 'x_end']
        endY = passes_between.loc[i, 'y_end']
        coordsA = "data"
        coordsB = "data"
        con = ConnectionPatch([endX, endY], [x, y],
                              coordsA, coordsB,
                              arrowstyle="simple", shrinkA=shrink, shrinkB=shrink,
                              mutation_scale=passes_between.loc[i, 'width']*max_line_width, color=passes_between.loc[i, 'alpha'])
        ax.add_artist(con)
    
    if len(filtered_pair_df) > 0:
        for i in filtered_pair_df.index:
            x = filtered_pair_df.loc[i, 'x']
            y = filtered_pair_df.loc[i, 'y']
            endX = filtered_pair_df.loc[i, 'x_end']
            endY = filtered_pair_df.loc[i, 'y_end']
            coordsA = "data"
            coordsB = "data"
            con = ConnectionPatch([endX, endY], [x, y],
                                  coordsA, coordsB,
                                  arrowstyle="<|-|>", shrinkA=shrink, shrinkB=shrink,
                                  mutation_scale=dh_arrow_width, lw=filtered_pair_df.loc[i, 'width']*max_line_width/5, 
                                  color=filtered_pair_df.loc[i, 'alpha'])
            ax.add_artist(con)
    
    for i in average_locs_and_count.index:
        pitch.annotate(i, xy=(average_locs_and_count.loc[i, 'x'], average_locs_and_count.loc[i, 'y']), 
                       family='DejaVu Sans', c='white', 
                       va='center', ha='center', zorder=average_locs_and_count.loc[i, 'zorder'], size=kit_no_size, weight='bold', ax=ax)
   # ax.text(50, 104, "{} (Mins 1-{})".format(team, sub_minute).upper(), size=10, fontweight='bold', ha='center',
        #   va='center')
    ax.text(2, 3, '{}'.format(formation), size=9, c='grey')

    
    






def getTeamSuccessfulBoxPasses(match_data, events_df, team, pitch_color, cmap):
    """
    Parameters
    ----------
    events_df : DataFrame of all events.
    
    teamId : ID of the team, the passes of which are required.
    
    team : Name of the team, the passes of which are required.
    
    pitch_color : color of the pitch.
    
    cmap : color design of the pass lines. 
           You can select more cmaps here: 
               https://matplotlib.org/3.1.0/tutorials/colors/colormaps.html

    Returns
    -------
    Pitch Plot.

    """
    # getting team id and venue
    if match_data['home']['name'] == team:
        teamId = match_data['home']['teamId']
        venue = 'home'
    else:
        teamId = match_data['away']['teamId']
        venue = 'away'
    # Get Total Passes
    passes_df = events_df.loc[events_df['type']=='Pass'].reset_index(drop=True)
    
    # Get Team Passes
    team_passes = passes_df.loc[passes_df['teamId'] == teamId]
        
    # Extracting Box Passes from Total Passes
    box_passes = team_passes.copy()
    for i,pas in box_passes.iterrows():
        X = pas["x"]/100*120
        Xend = pas["endX"]/100*120
        Y = pas["y"]/100*80
        Yend = pas["endY"]/100*80
        if Xend >= 102 and Yend >= 18 and Yend <= 62:
            if X >=102 and Y >= 18 and Y <= 62:
                box_passes = box_passes.drop([i])
            else:
                pass
        else:
            box_passes = box_passes.drop([i])
            
    
    successful_box_passes = box_passes.loc[box_passes['outcomeType']=='Successful'].reset_index(drop=True)
    
        
    # orientation='vertical'
    fig, ax = plt.subplots(figsize=(16, 11))
    pitch = VerticalPitch(pitch_type='statsbomb', pitch_color=pitch_color, line_color='#c7d5cc',
                          half=True, pad_top=2)
    fig, ax = pitch.draw(figsize=(16, 11), constrained_layout=True, tight_layout=False)
    
    # Plot the completed passes
    pitch.lines(successful_box_passes.x/100*120, 80-successful_box_passes.y/100*80,
                successful_box_passes.endX/100*120, 80-successful_box_passes.endY/100*80,
                lw=3, cmap=cmap, comet=True, transparent=True,
                label='Successful Passes', ax=ax)
    
    pitch.scatter(successful_box_passes.x/100*120, 80-successful_box_passes.y/100*80,
                  edgecolors='white', c='white', s=30, zorder=2,
                  ax=ax)
    
    # Set the title
   # fig.suptitle(f'Completed Box Passes - {team}', y=.95, fontsize=15)
    
    # Set the subtitle
    #ax.set_title('Data : Whoscored/Opta', fontsize=8, loc='right', fontstyle='italic', fontweight='bold')
    
    # set legend
    #ax.legend(facecolor='#22312b', edgecolor='None', fontsize=8, loc='lower center', handlelength=4)
    
    # Set the figure facecolor
    fig.set_facecolor(pitch_color)
    plt.tight_layout()
    return fig

    






def getTeamTotalPasses(events_df, teamId, team, opponent, pitch_color):
    """
    

    Parameters
    ----------
    events_df : DataFrame of all events.
    
    teamId : ID of the team, the passes of which are required.
    
    team : Name of the team, the passes of which are required.
    
    opponent : Name of opponent team.
    
    pitch_color : color of the pitch.


    Returns
    -------
    Pitch Plot.
    """
    
    # Get Total Passes
    passes_df = events_df.loc[events_df['type']=='Pass'].reset_index(drop=True)
    
    # Get Team Passes
    team_passes = passes_df.loc[passes_df['teamId'] == teamId]
        
    successful_passes = team_passes.loc[team_passes['outcomeType']=='Successful'].reset_index(drop=True)
    unsuccessful_passes = team_passes.loc[team_passes['outcomeType']=='Unsuccessful'].reset_index(drop=True)
            
    # Setup the pitch
    pitch = Pitch(pitch_type='opta', pitch_color=pitch_color, line_color='#c7d5cc')
    fig, ax = pitch.draw(figsize=(16, 11),constrained_layout=True, tight_layout=False)
    
    # Plot the completed passes
    pitch.arrows(successful_passes.x, successful_passes.y,
                 successful_passes.endX, successful_passes.endY, width=1,
                 headwidth=10, headlength=10, color='green', ax=ax, label='Completed')
    
    # Plot the other passes
    pitch.arrows(unsuccessful_passes.x, unsuccessful_passes.y,
                 unsuccessful_passes.endX, unsuccessful_passes.endY, width=1,
                 headwidth=6, headlength=5, headaxislength=12, color='#ba4f45', ax=ax, label='Blocked')
    
    # setup the legend
    ax.legend(facecolor=pitch_color, handlelength=5, edgecolor='None', labelcolor='white',fontsize=15, loc='upper left', shadow=True)
    
    # Set the title
    #fig.suptitle(f'{team} Passes vs {opponent}', y=1, fontsize=15, color='white')
    
    
    # Set the subtitle
   # ax.set_title('Data : Whoscored/Opta', fontsize=8, loc='right', fontstyle='italic', fontweight='bold')
    
    
    # Set the figure facecolor
    
    fig.set_facecolor(pitch_color)
    
    
    
    
    

def normalize(values, bounds):
    return [bounds['desired']['lower'] + (x - bounds['actual']['lower']) * (bounds['desired']['upper'] 
            - bounds['desired']['lower']) / (bounds['actual']['upper'] - bounds['actual']['lower']) for x in values]




    
def createPVFormationMap(match_data, events_df, team, color_palette,
                        markerstyle, markersize, markeredgewidth, labelsize, labelcolor):
    
    # getting team id and venue
    if match_data['home']['name'] == team:
        teamId = match_data['home']['teamId']
        venue = 'home'
    else:
        teamId = match_data['away']['teamId']
        venue = 'away'


    # getting opponent   
    if venue == 'home':
        opponent = match_data['away']['name']
    else:
        opponent = match_data['home']['name']


    # getting player dictionary
    team_players_dict = {}
    for player in match_data[venue]['players']:
        team_players_dict[player['playerId']] = player['name']


    # getting minute of first substitution
    for i,row in events_df.iterrows():
        if row['type'] == 'SubstitutionOn' and row['teamId'] == teamId:
            sub_minute = str(row['minute'])
            break


    # getting players dataframe
    match_players_df = pd.DataFrame()
    player_names = []
    player_ids = []
    player_pos = []
    player_kit_number = []

    for player in match_data[venue]['players']:
        player_names.append(player['name'])
        player_ids.append(player['playerId'])
        player_pos.append(player['position'])
        player_kit_number.append(player['shirtNo'])

    match_players_df['playerId'] = player_ids
    match_players_df['playerName'] = player_names
    match_players_df['playerPos'] = player_pos
    match_players_df['playerKitNumber'] = player_kit_number


    # extracting passes
    passes_df = events_df.loc[events_df['teamId'] == teamId].reset_index().drop('index', axis=1)
    passes_df['playerId'] = passes_df['playerId'].astype('float').astype('Int64')
    if 'playerName' in passes_df.columns:
        passes_df = passes_df.drop(columns='playerName')
    passes_df.dropna(subset=["playerId"], inplace=True)
    passes_df.insert(27, column='playerName', value=[team_players_dict[i] for i in list(passes_df['playerId'])])
    if 'passRecipientId' in passes_df.columns:
        passes_df = passes_df.drop(columns='passRecipientId')
        passes_df = passes_df.drop(columns='passRecipientName')
    passes_df.insert(28, column='passRecipientId', value=passes_df['playerId'].shift(-1))  
    passes_df.insert(29, column='passRecipientName', value=passes_df['playerName'].shift(-1))  
    passes_df.dropna(subset=["passRecipientName"], inplace=True)
    # passes_df = passes_df.loc[events_df['type'] == 'Pass', :].reset_index(drop=True)
    # passes_df = passes_df.loc[events_df['outcomeType'] == 'Successful', :].reset_index(drop=True)
    passes_df = passes_df.loc[passes_df['type'] == 'Pass'].reset_index(drop=True)
    passes_df = passes_df.loc[passes_df['outcomeType'] == 'Successful'].reset_index(drop=True)

    index_names = passes_df.loc[passes_df['playerName']==passes_df['passRecipientName']].index
    passes_df.drop(index_names, inplace=True)
    passes_df = passes_df.merge(match_players_df, on=['playerId', 'playerName'], how='left', validate='m:1')
    passes_df = passes_df.merge(match_players_df.rename({'playerId': 'passRecipientId', 'playerName':'passRecipientName'},
                                                        axis='columns'), on=['passRecipientId', 'passRecipientName'],
                                                        how='left', validate='m:1', suffixes=['', 'Receipt'])
    # passes_df = passes_df[passes_df['playerPos'] != 'Sub']
    
    
    # Getting net possesion value for passes
    netPVPassed = passes_df.groupby(['playerId', 'playerName'])['EPV'].sum().reset_index()
    netPVReceived = passes_df.groupby(['passRecipientId', 'passRecipientName'])['EPV'].sum().reset_index()
    

    
    # Getting formation and player ids for first 11
    formation = match_data[venue]['formations'][0]['formationName']
    formation_positions = match_data[venue]['formations'][0]['formationPositions']
    playerIds = match_data[venue]['formations'][0]['playerIds'][:11]

    
    # Getting all data in a dataframe
    formation_data = []
    for playerId, pos in zip(playerIds, formation_positions):
        pl_dict = {'playerId': playerId}
        pl_dict.update(pos)
        formation_data.append(pl_dict)
    formation_data = pd.DataFrame(formation_data)
    formation_data['vertical'] = normalize(formation_data['vertical'], 
                                           {'actual': {'lower': 0, 'upper': 10}, 'desired': {'lower': 10, 'upper': 110}})
    formation_data['horizontal'] = normalize(formation_data['horizontal'],
                                             {'actual': {'lower': 0, 'upper': 10}, 'desired': {'lower': 80, 'upper': 0}})
    formation_data = netPVPassed.join(formation_data.set_index('playerId'), on='playerId', how='inner').reset_index(drop=True)
    formation_data = formation_data.rename(columns={"EPV": "PV"})


    # Plotting
    fig, ax = plt.subplots(figsize=(16, 11))
    pitch = Pitch(pitch_type='statsbomb', pitch_color='#171717', line_color='#5c5c5c',
                  goal_type='box')
    pitch.draw(ax=ax, constrained_layout=True, tight_layout=True)
    
    sns.scatterplot(x='vertical', y='horizontal', data=formation_data, hue='PV', s=markersize, marker=markerstyle, legend=False, 
                    palette=color_palette, linewidth=markeredgewidth, ax=ax)
    
    ax.text(2, 78, '{}'.format('-'.join(formation)), size=20, c='grey')
    
    for index, row in formation_data.iterrows():
        pitch.annotate(str(round(row.PV*100,2))+'%', xy=(row.vertical, row.horizontal), c=labelcolor, va='center',
                       ha='center', size=labelsize, zorder=2, weight='bold', ax=ax)
        pitch.annotate(row.playerName, xy=(row.vertical, row.horizontal+6), c=labelcolor, va='center',
                       ha='center', size=labelsize+2, zorder=2, weight='bold', ax=ax)


    plt.tight_layout()
    return fig


def createPVFormationMaprec(match_data, events_df, team, color_palette,
                         markerstyle, markersize, markeredgewidth, labelsize, labelcolor):
    # getting team id and venue
    if match_data['home']['name'] == team:
        teamId = match_data['home']['teamId']
        venue = 'home'
    else:
        teamId = match_data['away']['teamId']
        venue = 'away'

    # getting opponent
    if venue == 'home':
        opponent = match_data['away']['name']
    else:
        opponent = match_data['home']['name']

    # getting player dictionary
    team_players_dict = {}
    for player in match_data[venue]['players']:
        team_players_dict[player['playerId']] = player['name']

    # getting minute of first substitution
    for i, row in events_df.iterrows():
        if row['type'] == 'SubstitutionOn' and row['teamId'] == teamId:
            sub_minute = str(row['minute'])
            break

    # getting players dataframe
    match_players_df = pd.DataFrame()
    player_names = []
    player_ids = []
    player_pos = []
    player_kit_number = []

    for player in match_data[venue]['players']:
        player_names.append(player['name'])
        player_ids.append(player['playerId'])
        player_pos.append(player['position'])
        player_kit_number.append(player['shirtNo'])

    match_players_df['playerId'] = player_ids
    match_players_df['playerName'] = player_names
    match_players_df['playerPos'] = player_pos
    match_players_df['playerKitNumber'] = player_kit_number

    # extracting passes
    passes_df = events_df.loc[events_df['teamId'] == teamId].reset_index().drop('index', axis=1)
    passes_df['playerId'] = passes_df['playerId'].astype('float').astype('Int64')
    if 'playerName' in passes_df.columns:
        passes_df = passes_df.drop(columns='playerName')
    passes_df.dropna(subset=["playerId"], inplace=True)
    passes_df.insert(27, column='playerName', value=[team_players_dict[i] for i in list(passes_df['playerId'])])
    if 'passRecipientId' in passes_df.columns:
        passes_df = passes_df.drop(columns='passRecipientId')
        passes_df = passes_df.drop(columns='passRecipientName')
    passes_df.insert(28, column='passRecipientId', value=passes_df['playerId'].shift(-1))
    passes_df.insert(29, column='passRecipientName', value=passes_df['playerName'].shift(-1))
    passes_df.dropna(subset=["passRecipientName"], inplace=True)
    # passes_df = passes_df.loc[events_df['type'] == 'Pass', :].reset_index(drop=True)
    # passes_df = passes_df.loc[events_df['outcomeType'] == 'Successful', :].reset_index(drop=True)
    passes_df = passes_df.loc[passes_df['type'] == 'Pass'].reset_index(drop=True)
    passes_df = passes_df.loc[passes_df['outcomeType'] == 'Successful'].reset_index(drop=True)

    index_names = passes_df.loc[passes_df['playerName'] == passes_df['passRecipientName']].index
    passes_df.drop(index_names, inplace=True)
    passes_df = passes_df.merge(match_players_df, on=['playerId', 'playerName'], how='left', validate='m:1')
    passes_df = passes_df.merge(
        match_players_df.rename({'playerId': 'passRecipientId', 'playerName': 'passRecipientName'},
                                axis='columns'), on=['passRecipientId', 'passRecipientName'],
        how='left', validate='m:1', suffixes=['', 'Receipt'])
    # passes_df = passes_df[passes_df['playerPos'] != 'Sub']

    # Getting net possesion value for passes
    netPVPassed = passes_df.groupby(['playerId', 'playerName'])['EPV'].sum().reset_index()
    netPVReceived = passes_df.groupby(['passRecipientId', 'passRecipientName'])['EPV'].sum().reset_index()

    # Getting formation and player ids for first 11
    formation = match_data[venue]['formations'][0]['formationName']
    formation_positions = match_data[venue]['formations'][0]['formationPositions']
    passRecipientIds = match_data[venue]['formations'][0]['playerIds'][:11]

    # Getting all data in a dataframe
    formation_data = []
    for playerId, pos in zip(passRecipientIds, formation_positions):
        pl_dict = {'passRecipientId': playerId}
        pl_dict.update(pos)
        formation_data.append(pl_dict)
    formation_data = pd.DataFrame(formation_data)
    formation_data['vertical'] = normalize(formation_data['vertical'],
                                           {'actual': {'lower': 0, 'upper': 10},
                                            'desired': {'lower': 10, 'upper': 110}})
    formation_data['horizontal'] = normalize(formation_data['horizontal'],
                                             {'actual': {'lower': 0, 'upper': 10},
                                              'desired': {'lower': 80, 'upper': 0}})
    formation_data = netPVReceived.join(formation_data.set_index('passRecipientId'), on= 'passRecipientId', how='inner').reset_index(
        drop=True)
    formation_data = formation_data.rename(columns={"EPV": "PV"})

    # Plotting
    fig, ax = plt.subplots(figsize=(16, 11))
    pitch = Pitch(pitch_type='statsbomb', pitch_color='#171717', line_color='#5c5c5c',
                  goal_type='box')
    pitch.draw(ax=ax, constrained_layout=True, tight_layout=True)

    sns.scatterplot(x='vertical', y='horizontal', data=formation_data, hue='PV', s=markersize, marker=markerstyle,
                    legend=False,
                    palette=color_palette, linewidth=markeredgewidth, ax=ax)

    ax.text(2, 78, '{}'.format('-'.join(formation)), size=20, c='grey')

    for index, row in formation_data.iterrows():
        pitch.annotate(str(round(row.PV * 100, 2)) + '%', xy=(row.vertical, row.horizontal), c=labelcolor, va='center',
                       ha='center', size=labelsize, zorder=2, weight='bold', ax=ax)
        pitch.annotate(row.passRecipientName, xy=(row.vertical, row.horizontal + 6), c=labelcolor, va='center',
                       ha='center', size=labelsize+2, zorder=2, weight='bold', ax=ax)

    plt.tight_layout()
    return fig

def clusters(Df,teamid):
    from sklearn.cluster import KMeans
    df = Df.copy()
    df = df.loc[(df.type=='Pass') & (df.outcomeType=='Successful') & (df.teamId==teamid)]
    df = df.reset_index()
    df['y'] = 80 - (0.8* df['y'])
    df['endY'] = 80 - (0.8*df['endY'])
    df['x'] = df['x']* 1.2
    df['endX'] = df['endX'] * 1.2
    X = np.array(df[['x', 'y', 'endX', 'endY']])
    kmeans = KMeans(n_clusters=5, random_state=100)
    kmeans.fit(X)
    df['cluster'] = kmeans.predict(X)
    df.cluster.value_counts()
    fig, ax = plt.subplots(figsize=(16, 9))
    fig.set_facecolor('#38383b')
    ax.patch.set_facecolor('#38383b')

    pitch = Pitch(pitch_type='statsbomb',
                  pitch_color='#171717', line_color='white')

    pitch.draw(ax=ax, figsize=(16, 9),
               constrained_layout=False, tight_layout=True)

    for x in df.index:

        if df['cluster'][x] == 0:
            pitch.lines(xstart=df['x'][x], ystart=df['y'][x], xend=df['endX'][x], yend=df['endY'][x],
                        color='#74c69d', lw=3, zorder=3, comet=True, ax=ax)

    return fig


def defline(events_df,teamId,playername):
    intercept_df = events_df.loc[events_df['type']=='Interception'].reset_index(drop=True)
    ballrecovery_df=events_df.loc[events_df['type']=='BallRecovery'].reset_index(drop=True)
    blockedpass_df=events_df.loc[events_df['type']=='BlockedPass'].reset_index(drop=True)
    challenge_df=events_df.loc[events_df['type']=='BlockedPass'].reset_index(drop=True)
    clearance_df=events_df.loc[events_df['type']=='Clearance'].reset_index(drop=True)
    tackle_df=events_df.loc[events_df['type']=='Tackle'].reset_index(drop=True)
    aerial_df = events_df.loc[events_df['type']=='Aerial'].reset_index(drop=True)
    defactions_df=pd.concat([intercept_df,ballrecovery_df, ballrecovery_df, blockedpass_df, challenge_df,
                             clearance_df, tackle_df, aerial_df])
    defaction_df=defactions_df.loc[defactions_df['teamId'] == teamId].reset_index(drop=True)
    succ_def=defactions_df.loc[defactions_df['outcomeType']=='Successful'].reset_index(drop=True)
    succ_def = succ_def.loc[succ_def['teamId'] == teamId].reset_index(drop=True)
    succ_def =succ_def[succ_def['playerName']==playername]
    #plot it
    pitch = VerticalPitch(pitch_type='opta',
                      pitch_color='#171717', line_color='grey')


    fig, ax = pitch.draw(figsize=(16, 11),
                      constrained_layout=True, tight_layout=False)
    #pitch.scatter(merged_df.x, merged_df.y,  ax=ax)

    #positions = ['full', 'horizontal', 'vertical']
    #for i, pos in enumerate(positions):
    bin_statistic = pitch.bin_statistic_positional(succ_def.x, succ_def.y, statistic='count')
    #pitch.heatmap_positional(bin_statistic, ax=ax, cmap='coolwarm', edgecolors='#22312b')
    pitch.scatter(succ_def.x, succ_def.y, c='white', s=10, ax=ax)
    #total = np.array([bs['statistic'].sum() for bs in bin_statistic]).sum()
        # replace raw counts with percentages and add percentage
        # sign (note immutable named tuple so used _replace)
    #for bs in bin_statistic:
        #bs['statistic'] = (pd.DataFrame(bs['statistic'] / total)
                               #.applymap(lambda x: '{:.0%}'.format(x))
                             #  .values)
    defeline = succ_def.x.mean()
    defeline= round(defeline,2)
    #print(succ_def.x.mean())
    plt.axhline(succ_def.x.mean())
    ax.text(-0.5, 78, f'{defeline}', size=20, c='grey')
    fig.set_facecolor('#171717')

    plt.tight_layout()
    return fig
