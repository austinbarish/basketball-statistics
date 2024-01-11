# Imports
from shiny import render, ui, App, reactive
from shiny.types import ImgData
import pandas as pd
import shinyswatch
import urllib.request
from pathlib import Path

# Load in all players
all_players = pd.read_csv(
    "https://raw.githubusercontent.com/austinbarish/basketball-statistics/main/data/per-game-stats.csv"
)

# Create a dict of player-name:player-name
player_names = {name: name for name in all_players["PLAYER_NAME"].unique()}

# Add a starting guess
player_names["Type Your Guess Here"] = "Type Your Guess Here"

# Get all Teams
all_teams = all_players["TEAM_ABBREVIATION"].unique()

# Add a starting guess
all_teams = ["All"] + list(all_teams)

# Remove NaN Team
all_teams = [team for team in all_teams if str(team) != "nan"]

# App UI
app_ui = ui.page_fluid(
    shinyswatch.theme.superhero(),
    ui.tags.head(
        ui.HTML(
            "<script async src='https://www.googletagmanager.com/gtag/js?id=G-V3S3ZEBK44'></script><script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date()); gtag('config', 'G-V3S3ZEBK44');</script>"
        )
    ),
    ui.panel_title("Guess the NBA Player", window_title="NBA Guesser"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_slider(
                "year_range",
                "Years Player could be in the NBA",
                min=1946,
                max=2023,
                value=[2000, 2023],
                sep="",
            ),
            ui.input_slider("minimum_ppg", "Minimum Peak PPG of Player", 0, 50, 20),
            ui.input_select(
                id="team",
                label="Teams",
                choices=all_teams,
                selectize=False,
                selected="All",
            ),
            ui.input_switch("teams_only", "Teams Only", False),
            ui.input_action_button(
                id="refresh", label="New Player", class_="btn-success"
            ),
            ui.output_text("instructions"),
        ),
        ui.output_data_frame("player_stats_table"),
        ui.input_select(
            id="guess",
            label="Select Player",
            choices=player_names,
            selectize=True,
            selected="Type Your Guess Here",
        ),
        ui.output_image("answer_headshot", inline=True),
        ui.output_text_verbatim("guess"),
        ui.input_switch("answer", "Reveal Player", False),
        ui.panel_conditional(
            "input.answer",
            ui.output_image("headshot", inline=True),
            ui.output_text_verbatim("answer"),
        ),
    ),
    ui.panel_well(
        "Created by Austin Barish. Check out the code on ",
        ui.a(
            "Github",
            href="https://github.com/austinbarish/basketball-statistics/tree/main/shiny-app",
            target="_blank",
        ),
    ),
)


# Function to get a random player given the filters
def random_player(all_players, season_range=[1946, 2023], min_points=0.0, team="All"):
    # Add a Year column for easier filtering
    seasons = all_players["Season"]
    all_players["Year"] = [int(s.split("-")[0]) for s in seasons]

    # Filter out players not on the team
    if team != "All":
        all_player_options = all_players[all_players["Team"] == team]
    else:
        all_player_options = all_players

    # Filter out seasons before earliest_season
    all_player_options = all_player_options[
        all_player_options["Year"] >= season_range[0]
    ]

    # Filter out seasons after latest_season
    all_player_options = all_player_options[
        all_player_options["Year"] <= season_range[1]
    ]

    # Filter out players with less than min_points per game
    all_player_options = all_player_options[all_player_options["PTS"] >= min_points]

    # Return a better error message if there are no players that meet the criteria
    if len(all_player_options) == 0:
        return (
            1,
            "No Players Meet the Criteria",
            pd.DataFrame(
                {
                    "No Players Meet the Criteria": [
                        "You can try changing the minimum year, minimum PPG, or team."
                    ]
                }
            ),
        )

    # Get a random player
    player_id = all_player_options["ID"].sample()
    player_id = player_id.values[0]

    # Get all his stats
    player_stats = all_players[all_players["ID"] == player_id]

    # Get his name
    player_name = player_stats["Name"].values[0]

    # Drop the ID, Year, and Name columns
    player_stats = player_stats.drop(["ID", "Year", "Name"], axis=1)
    player_stats.reset_index(inplace=True, drop=True)

    # Return the player's stats and name
    return player_id, player_name, player_stats


def server(input, output, session):
    # Text instructions
    @output
    @render.text
    def instructions():
        return f"Thank you for playing!"

    # Author Acknowledgement
    @output
    @render.text
    def author():
        return f"Created by Austin Barish. Check out the code on GitHub: https://github.com/austinbarish/basketball-statistics/tree/main/shiny-app"

    @output
    @render.data_frame
    @reactive.event(input.refresh, ignore_none=False)
    def player_stats_table():
        all_players = pd.read_csv(
            "https://raw.githubusercontent.com/austinbarish/basketball-statistics/main/data/per-game-stats.csv"
        )
        # Keep only the columns we want
        # Player_id, name, season, Team, age, GP, GS, MP, FG, FGA, 3P, 3PA, 2P, 2PA, FT, FTA, ORB, DRB, TRB, AST, STL, BLK, TOV, PF, PTS
        all_players = all_players[
            [
                "PLAYER_ID",
                "PLAYER_NAME",
                "SEASON_ID",
                "TEAM_ABBREVIATION",
                "PLAYER_AGE",
                "GP",
                "GS",
                "MIN",
                "FGM",
                "FGA",
                "FG3M",
                "FG3A",
                "FTM",
                "FTA",
                "OREB",
                "DREB",
                "REB",
                "AST",
                "STL",
                "BLK",
                "TOV",
                "PF",
                "PTS",
            ]
        ]

        # Rename Key Columns
        all_players.rename(
            {
                "PLAYER_ID": "ID",
                "PLAYER_NAME": "Name",
                "SEASON_ID": "Season",
                "TEAM_ABBREVIATION": "Team",
                "PLAYER_AGE": "Age",
                "FG3M": "3PM",
                "FG3A": "3PA",
            },
            axis=1,
            inplace=True,
        )

        # Order Columns to be ID, Name, Season, Team, Age, GP, GS, MIN, PTS, REB, AST, STL, BLK, TOV, 3PM, 3PA, FGM, FGA, FTM, FTA, OREB, DREB, PF
        all_players = all_players[
            [
                "ID",
                "Name",
                "Season",
                "Team",
                "Age",
                "GP",
                "GS",
                "MIN",
                "PTS",
                "REB",
                "AST",
                "STL",
                "BLK",
                "TOV",
                "3PM",
                "3PA",
                "FGM",
                "FGA",
                "FTM",
                "FTA",
                "PF",
            ]
        ]

        # Filter out the TOT team rows as those are for totals
        all_players = all_players[all_players["Team"] != "TOT"]

        # Divide all stats by GP to get per game stats
        all_players["GP"] = all_players["GP"].astype(float)
        all_players["MIN"] = round(all_players["MIN"] / all_players["GP"], 1)
        all_players["PTS"] = round(all_players["PTS"] / all_players["GP"], 1)
        all_players["REB"] = round(all_players["REB"] / all_players["GP"], 1)
        all_players["AST"] = round(all_players["AST"] / all_players["GP"], 1)
        all_players["STL"] = round(all_players["STL"] / all_players["GP"], 1)
        all_players["BLK"] = round(all_players["BLK"] / all_players["GP"], 1)
        all_players["TOV"] = round(all_players["TOV"] / all_players["GP"], 1)
        all_players["3PM"] = round(all_players["3PM"] / all_players["GP"], 1)
        all_players["3PA"] = round(all_players["3PA"] / all_players["GP"], 1)
        all_players["FGM"] = round(all_players["FGM"] / all_players["GP"], 1)
        all_players["FGA"] = round(all_players["FGA"] / all_players["GP"], 1)
        all_players["FTM"] = round(all_players["FTM"] / all_players["GP"], 1)
        all_players["FTA"] = round(all_players["FTA"] / all_players["GP"], 1)
        all_players["PF"] = round(all_players["PF"] / all_players["GP"], 1)

        # Replace All NaN values with "Untracked"
        all_players.fillna("Untracked", inplace=True)

        # Get player name and stats
        player_id, player_name, player_stats = random_player(
            all_players,
            season_range=input.year_range(),
            min_points=input.minimum_ppg(),
            team=input.team(),
        )

        # Save player_name outside the function
        server.player_name = player_name

        @render.text
        def answer():
            # If real player name is selected, return the correct player
            if player_name != "No Players Meet the Criteria":
                return f"The Correct Player was: " + player_name

            # If no players meet the criteria, return a message
            else:
                return f"No Players Meet the Criteria. Try changing the minimum year, minimum PPG, or team."

        @render.text
        def guess():
            # Get the player_id for the guess and answer to avoid any errors
            if (
                input.guess() in player_names
                and input.guess() != "Type Your Guess Here"
            ):
                guess_id = [
                    id for id in all_players[all_players["Name"] == input.guess()]["ID"]
                ].pop()
                answer_id = [
                    id
                    for id in all_players[all_players["Name"] == server.player_name][
                        "ID"
                    ]
                ].pop()

            # If guess is blank, return different IDs
            else:
                guess_id = 1
                answer_id = 2

            # If no player is selected, return a message
            if player_name == "No Players Meet the Criteria":
                # Show the NBA Logo while waiting on a Guess
                @render.image
                def answer_headshot():
                    # Get the current directory
                    current_dir = Path.cwd()

                    # Create the directory for the images if it doesn't exist
                    image_dir = current_dir / "images"
                    image_dir.mkdir(exist_ok=True)

                    # Create the path for the image
                    image_path = image_dir / f"nba.png"

                    urllib.request.urlretrieve(
                        "https://images.ctfassets.net/h8q6lxmb5akt/5qXnOINbPrHKXWa42m6NOa/421ab176b501f5bdae71290a8002545c/nba-logo_2x.png",
                        image_path,
                    )

                    # Create the image data
                    img: ImgData = {"src": image_path, "width": "100px"}
                    return img

                return f"N/A - No Players Meet the Criteria"

            elif input.guess() == "Type Your Guess Here":
                # Show the NBA Logo while waiting on a Guess
                @render.image
                def answer_headshot():
                    # Get the current directory
                    current_dir = Path.cwd()

                    # Create the directory for the images if it doesn't exist
                    image_dir = current_dir / "images"
                    image_dir.mkdir(exist_ok=True)

                    # Create the path for the image
                    image_path = image_dir / f"nba.png"

                    urllib.request.urlretrieve(
                        "https://images.ctfassets.net/h8q6lxmb5akt/5qXnOINbPrHKXWa42m6NOa/421ab176b501f5bdae71290a8002545c/nba-logo_2x.png",
                        image_path,
                    )

                    # Create the image data
                    img: ImgData = {"src": image_path, "width": "100px"}
                    return img

                return "Please Select a Player"

            # Compare IDs for safety
            elif answer_id == guess_id:
                # Show the Correct Player's Headshot for correct answers
                @render.image
                def answer_headshot():
                    # Create the url for the image
                    image_url = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{player_id}.png".format(
                        player_id=player_id
                    )

                    # Get the current directory
                    current_dir = Path.cwd()

                    # Create the directory for the images if it doesn't exist
                    image_dir = current_dir / "images"
                    image_dir.mkdir(exist_ok=True)

                    # Create the path for the image
                    image_path = image_dir / f"{player_name}.png"

                    # Try image
                    try:
                        urllib.request.urlretrieve(image_url, image_path)
                    except urllib.error.HTTPError:
                        urllib.request.urlretrieve(
                            "https://images.ctfassets.net/h8q6lxmb5akt/5qXnOINbPrHKXWa42m6NOa/421ab176b501f5bdae71290a8002545c/nba-logo_2x.png",
                            image_path,
                        )

                    # Create the image data
                    img: ImgData = {"src": image_path, "width": "100px"}
                    return img

                return f"CORRECT! The player was {server.player_name}."

            else:
                # Show the Incorrect Player's Headshot for incorrect answers
                @render.image
                def answer_headshot():
                    guess_name = input.guess()
                    # Get the player_id for the guess
                    guess_id = all_players[all_players["Name"] == guess_name]["ID"]

                    # If guess is blank, return mutumbo
                    if len(guess_id) == 0:
                        # Get the current directory
                        current_dir = Path.cwd()

                        # Create the directory for the images if it doesn't exist
                        image_dir = current_dir / "images"
                        image_dir.mkdir(exist_ok=True)

                        # Create Mutumbo path
                        image_path = image_dir / f"mutumbo.png"

                        urllib.request.urlretrieve(
                            "https://media.tenor.com/images/b144b620392ccd1cd9ccea5ca1088995/raw.png",
                            image_path,
                        )

                        # Create the image data
                        img: ImgData = {"src": image_path, "width": "100px"}
                        return img

                    guess_id = guess_id.values[0]

                    # Create the url for the image
                    image_url = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{guess_id}.png".format(
                        guess_id=guess_id
                    )
                    # Get the current directory
                    current_dir = Path.cwd()

                    # Create the directory for the images if it doesn't exist
                    image_dir = current_dir / "images"
                    image_dir.mkdir(exist_ok=True)

                    # Create the path for the image
                    image_path = image_dir / f"{guess_name}.png"

                    # Try image
                    try:
                        urllib.request.urlretrieve(image_url, image_path)

                    # Show the nba logo if the image doesn't exist
                    except urllib.error.HTTPError:
                        # Create NBA path
                        image_path = image_dir / f"nba.png"

                        urllib.request.urlretrieve(
                            "https://images.ctfassets.net/h8q6lxmb5akt/5qXnOINbPrHKXWa42m6NOa/421ab176b501f5bdae71290a8002545c/nba-logo_2x.png",
                            image_path,
                        )

                    # Create the image data
                    img: ImgData = {"src": image_path, "width": "100px"}
                    return img

                # If guess is not a player, tell them to select a player
                if input.guess() not in player_names:
                    return f"Please Select a Player"

                return f"Incorrect. You guessed {input.guess()}."

        @render.image
        def headshot():
            # Create the url for the image
            image_url = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{player_id}.png".format(
                player_id=player_id
            )

            # Get the current directory
            current_dir = Path.cwd()

            # Create the directory for the images if it doesn't exist
            image_dir = current_dir / "images"
            image_dir.mkdir(exist_ok=True)

            # Create the path for the image
            image_path = image_dir / f"{player_name}.png"

            # Try image
            try:
                urllib.request.urlretrieve(image_url, image_path)
            except urllib.error.HTTPError:
                urllib.request.urlretrieve(
                    "https://images.ctfassets.net/h8q6lxmb5akt/5qXnOINbPrHKXWa42m6NOa/421ab176b501f5bdae71290a8002545c/nba-logo_2x.png",
                    image_path,
                )

            # Create the image data
            img: ImgData = {"src": image_path, "width": "100px"}
            return img

        # If teams_only is selected, return a table of only the years and teams
        if input.teams_only():
            # Return table
            return render.DataGrid(
                player_stats[["Season", "Team"]], height="300px", width="100%"
            )

        # Return table
        return render.DataGrid(player_stats, height="300px", width="100%")


# Create the app
app = App(app_ui, server)
