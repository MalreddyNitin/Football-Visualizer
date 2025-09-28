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
