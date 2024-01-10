# Imports
from shiny import render, ui, App, reactive
import pandas as pd
import shinyswatch

# Load in all players
all_players = pd.read_csv("https://raw.githubusercontent.com/austinbarish/basketball-statistics/main/data/per-game-stats.csv")

# Create a dict of player-name:player-name
player_names = {name:name for name in all_players['PLAYER_NAME'].unique()}

# Add a starting guess
player_names["Type Your Guess Here"] = "Type Your Guess Here"

# Get all Teams
all_teams = all_players['TEAM_ABBREVIATION'].unique()

# Add a starting guess
all_teams = ["All"] + list(all_teams)

# Remove NaN Team
all_teams = [team for team in all_teams if str(team) != "nan"]

# App UI
app_ui = ui.page_fluid(
    shinyswatch.theme.superhero(),
    ui.panel_title("Guess the NBA Player", window_title="Guess the NBA Player"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_slider("minimum_year", "Earliest Year Player Could be in the NBA", min=1946, max=2023, value=2000, sep=""),
            ui.input_slider("minimum_ppg", "Minimum Peak PPG of Player", 0, 50, 20),
            ui.input_select(id="team", label="Teams", choices=all_teams, selectize=False, selected="All"),
            ui.input_action_button(id="refresh", label="New Player", class_="btn-success"),
        ),
    ui.output_data_frame("player_stats_table"),
    ui.input_select(id="guess", label="Select Player", choices=player_names, selectize=True, selected="Type Your Guess Here"),
    ui.output_text_verbatim("guess"),
    ui.input_switch("answer", "Reveal Player", False),
    ui.panel_conditional(
        "input.answer", ui.output_text_verbatim("answer")
        )
))

def random_player(all_players, earliest_season=1946, min_points=0.0, team="All"):
    # Add a Year column for easier filtering
    seasons = all_players['Season']
    all_players["Year"] = [int(s.split('-')[0]) for s in seasons]

    # Filter out players not on the team
    if team != "All":
        all_player_options = all_players[all_players['Team'] == team]
    else:
        all_player_options = all_players

    # Filter out seasons before earliest_season
    all_player_options = all_player_options[all_player_options['Year'] >= earliest_season]

    # Filter out players with less than min_points per game
    all_player_options = all_player_options[all_player_options['PTS'] >= min_points]

    # Return a better error message if there are no players that meet the criteria
    if len(all_player_options) == 0:
        return "No Players Meet the Criteria", pd.DataFrame({"No Players Meet the Criteria": ["You can try changing the minimum year, minimum PPG, or team."]})

    # Get a random player
    player_id = all_player_options['ID'].sample()

    # Get all his stats
    player_stats = all_players[all_players['ID'] == player_id.values[0]]

    # Get his name
    player_name = player_stats['Name'].values[0]

    # Drop the ID, Year, and Name columns
    player_stats = player_stats.drop(['ID', 'Year', 'Name'], axis=1)
    player_stats.reset_index(inplace=True, drop=True)

    # Return the player's stats and name
    return player_name, player_stats

def server(input, output, session):
    @output
    @render.text
    def input_txt():
        return f"Minimum Year: {input.minimum_year()}, Minimum PPG: {input.minimum_ppg()}, Team(s): {input.team()}"
    
    @output
    @render.data_frame
    @reactive.event(input.refresh, ignore_none=False)
    def player_stats_table():
        all_players = pd.read_csv("https://raw.githubusercontent.com/austinbarish/basketball-statistics/main/data/per-game-stats.csv")
        # Keep only the columns we want
        # Player_id, name, season, Team, age, GP, GS, MP, FG, FGA, 3P, 3PA, 2P, 2PA, FT, FTA, ORB, DRB, TRB, AST, STL, BLK, TOV, PF, PTS
        all_players = all_players[['PLAYER_ID', 'PLAYER_NAME', 'SEASON_ID', 'TEAM_ABBREVIATION', 'PLAYER_AGE', 'GP', 'GS', 'MIN', 'FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS']]

        # Rename Key Columns
        all_players.rename({"PLAYER_ID": "ID", "PLAYER_NAME":"Name", "SEASON_ID":"Season", "TEAM_ABBREVIATION":"Team", "PLAYER_AGE":"Age", "FG3M":"3PM", "FG3A":"3PA"}, axis=1, inplace=True)

        # Order Columns to be ID, Name, Season, Team, Age, GP, GS, MIN, PTS, REB, AST, STL, BLK, TOV, 3PM, 3PA, FGM, FGA, FTM, FTA, OREB, DREB, PF
        all_players = all_players[['ID', 'Name', 'Season', 'Team', 'Age', 'GP', 'GS', 'MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', '3PM', '3PA', 'FGM', 'FGA', 'FTM', 'FTA', 'PF']]
        
        # Divide all stats by GP to get per game stats
        all_players['GP'] = all_players['GP'].astype(float)
        all_players['MIN'] = round(all_players['MIN'] / all_players['GP'], 1)
        all_players['PTS'] = round(all_players['PTS'] / all_players['GP'], 1)
        all_players['REB'] = round(all_players['REB'] / all_players['GP'], 1)
        all_players['AST'] = round(all_players['AST'] / all_players['GP'], 1)
        all_players['STL'] = round(all_players['STL'] / all_players['GP'], 1)
        all_players['BLK'] = round(all_players['BLK'] / all_players['GP'], 1)
        all_players['TOV'] = round(all_players['TOV'] / all_players['GP'], 1)
        all_players['3PM'] = round(all_players['3PM'] / all_players['GP'], 1)
        all_players['3PA'] = round(all_players['3PA'] / all_players['GP'], 1)
        all_players['FGM'] = round(all_players['FGM'] / all_players['GP'], 1)
        all_players['FGA'] = round(all_players['FGA'] / all_players['GP'], 1)
        all_players['FTM'] = round(all_players['FTM'] / all_players['GP'], 1)
        all_players['FTA'] = round(all_players['FTA'] / all_players['GP'], 1)
        all_players['PF'] = round(all_players['PF'] / all_players['GP'], 1)

        # Replace All NaN values with "Untracked"
        all_players.fillna("Untracked", inplace=True)

        # Get player name and stats
        player_name, player_stats = random_player(all_players, earliest_season=input.minimum_year(), min_points=input.minimum_ppg(), team=input.team())

        # Save player_name outside the function
        server.player_name = player_name

        @render.text
        def answer():
            # If real player name is selected, return the correct player
            if player_name != "No Players Meet the Criteria":
                return f"The Correct Player was: " + player_name + "."
            
            # If no players meet the criteria, return a message
            else:
                return f"No Players Meet the Criteria. Try changing the minimum year, minimum PPG, or team."

        # Return table
        return render.DataGrid(player_stats, height="400px", width="90%")
    
    @render.text  # Change to render.html
    def guess():
        if input.guess() == "Type Your Guess Here":
            return 'Please Select a Player'
        elif server.player_name == input.guess():
            return f'CORRECT! The player was {server.player_name}.'
        else:
            return f'Incorrect. You guessed {input.guess()}.'


# Create the app
app = App(app_ui, server)