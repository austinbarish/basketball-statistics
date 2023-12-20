"""
Basketball statistics application adapted from https://github.com/neuml/txtai/blob/master/examples/baseball.py
Code is heavily adapted from David Mezzetti

Using txtai and Streamlit

Install txtai and streamlit (>= 1.23) to run:
  pip install txtai streamlit
"""

print("STARTING IMPORTS...")
import datetime
import math
import os
import random

print("DONE WITH DEFAULTS")

import altair as alt

print("Alt")
import numpy as np
import pandas as pd

print("pd,np")
import streamlit as st

print("Streamlit DONE")

from txtai.embeddings import Embeddings

print("DONE WITH IMPORTS")


class Stats:
    """
    Base stats class. Contains methods for loading, indexing and searching stats.
    """

    def __init__(self):
        """
        Creates a new Stats instance.
        """

        # Load columns
        self.columns = self.loadcolumns()

        # Load stats data
        self.stats = self.load()

        # Load names
        self.names = self.loadnames()

        # Build index
        self.vectors, self.data, self.embeddings = self.index()

    def loadcolumns(self):
        """
        Returns a list of data columns.

        Returns:
            list of columns
        """

        columns = self.columns
        return columns

        raise NotImplementedError

    def load(self):
        """
        Loads and returns raw stats.

        Returns:
            stats
        """

        raise NotImplementedError

    def metric(self):
        """
        Primary metric column.

        Returns:
            metric column name
        """
        return "PTS"
        raise NotImplementedError

    def vector(self, row):
        """
        Build a vector for input row.

        Args:
            row: input row

        Returns:
            row vector
        """

        raise NotImplementedError

    def loadnames(self):
        """
        Loads a name - player id dictionary.

        Returns:
            {player name: player id}
        """

        # Get unique names
        names = {}
        rows = (
            self.stats.sort_values(by=self.metric(), ascending=False)[
                ["PLAYER_ID", "PLAYER_NAME"]
            ]
            .drop_duplicates()
            .reset_index()
        )
        for x, row in rows.iterrows():
            # Name key
            key = f'{row["PLAYER_NAME"]}'
            key += f" ({row['PLAYER_ID']})" if key in names else ""

            if key not in names:
                # Scale scores of top n players
                exponent = 2 if ((len(rows) - x) / len(rows)) >= 0.95 else 1

                # score = num seasons ^ exponent
                score = math.pow(
                    len(self.stats[self.stats["PLAYER_ID"] == row["PLAYER_ID"]]),
                    exponent,
                )

                # Save name key - values pair
                names[key] = (row["PLAYER_ID"], score)

        return names

    def index(self):
        """
        Builds an embeddings index to stats data. Returns vectors, input data and embeddings index.

        Returns:
            vectors, data, embeddings
        """

        # Build data dictionary
        vectors = {
            f'{row["SEASON_ID"]}{row["PLAYER_ID"]}': self.transform(row)
            for _, row in self.stats.iterrows()
        }
        data = {
            f'{row["SEASON_ID"]}{row["PLAYER_ID"]}': dict(row)
            for _, row in self.stats.iterrows()
        }

        embeddings = Embeddings(
            {
                "transform": self.transform,
            }
        )

        embeddings.index((uid, vectors[uid], None) for uid in vectors)

        return vectors, data, embeddings

    def metrics(self, name):
        """
        Looks up a player's active years, best statistical year and key metrics.

        Args:
            name: player name

        Returns:
            active, best, metrics
        """

        if name in self.names:
            # Get player stats
            stats = self.stats[self.stats["PLAYER_ID"] == self.names[name][0]]

            # Build key metrics
            metrics = stats[["SEASON_ID", self.metric()]]

            # Get best year, sort by primary metric
            best = int(
                stats.sort_values(by=self.metric(), ascending=False)["SEASON_ID"].iloc[
                    0
                ]
            )

            # Get years active, best year, along with metric trends
            return metrics["SEASON_ID"].tolist(), best, metrics

        return range(1871, datetime.datetime.today().year), 1950, None

    def search(self, name=None, year=None, row=None, limit=10):
        """
        Runs an embeddings search. This method takes either a player-year or stats row as input.

        Args:
            name: player name to search
            year: year to search
            row: row of stats to search
            limit: max results to return

        Returns:
            list of results
        """

        if row:
            query = self.vector(row)
        else:
            # Lookup player key and build vector id
            name = self.names.get(name)
            query = f"{year}{name[0] if name else name}"
            query = self.vectors.get(query)

        results, ids = [], set()
        if query is not None:
            for uid, _ in self.embeddings.search(query, limit * 5):
                # Only add unique players
                if uid[4:] not in ids:
                    result = self.data[uid].copy()
                    result[
                        "link"
                    ] = f'https://www.nba.com/stats/player/{result["PLAYER_ID"]}?PerMode=Totals'
                    results.append(result)
                    ids.add(uid[4:])

                    if len(ids) >= limit:
                        break

        return results

    def transform(self, row):
        """
        Transforms a stats row into a vector.

        Args:
            row: stats row

        Returns:
            vector
        """

        if isinstance(row, np.ndarray):
            return row

        return np.array(
            [
                0.0 if pd.isna(row[x]) or np.isnan(row[x]) else row[x]
                for x in self.columns
            ]
        )


class Counting(Stats):
    """
    Counting Stats
    """

    def loadcolumns(self):
        return [
            "PLAYER_ID",
            "PLAYER_NAME",
            "SEASON_ID",
            "LEAGUE_ID",
            "TEAM_ID",
            "TEAM_ABBREVIATION",
            "PLAYER_AGE",
            "GP",
            "GS",
            "MIN",
            "FGM",
            "FGA",
            "FG_PCT",
            "FG3M",
            "FG3A",
            "FG3_PCT",
            "FTM",
            "FTA",
            "FT_PCT",
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

    def load(self):
        totals = pd.read_csv("../data/total-stats.csv")

        # Require player to have at least 40 Games
        totals = totals[totals["GP"] >= 40]

        return totals


class PerGame(Stats):
    """
    Per Game stats.
    """

    def loadcolumns(self):
        return [
            "PLAYER_ID",
            "PLAYER_NAME",
            "SEASON_ID",
            "LEAGUE_ID",
            "TEAM_ID",
            "TEAM_ABBREVIATION",
            "PLAYER_AGE",
            "GP",
            "GS",
            "MIN",
            "FGM",
            "FGA",
            "FG_PCT",
            "FG3M",
            "FG3A",
            "FG3_PCT",
            "FTM",
            "FTA",
            "FT_PCT",
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

    def load(self):
        # Retrieve raw data from GitHub
        per_game = pd.read_csv("../data/per-game-stats.csv")

        # Require player to have 20 games played
        per_game = per_game[per_game["GP"] >= 20]

        return per_game

    # def metric(self):
    #     return "WADJ"

    # def vector(self, row):
    #     row["WHIP"] = (
    #         (row["BB"] + row["H"]) / (row["IPouts"] / 3) if row["IPouts"] else None
    #     )
    #     row["WADJ"] = (
    #         (row["W"] + row["SV"]) / (row["ERA"] + row["WHIP"])
    #         if row["ERA"] and row["WHIP"]
    #         else None
    #     )

    #     return self.transform(row)


class Application:
    """
    Main application.
    """

    def __init__(self):
        """
        Creates a new application.
        """
        print("INITIALIZING")

        # Total stats
        self.total = Counting()

        # Pitching stats
        self.per_game = PerGame()

    def run(self):
        """
        Runs a Streamlit application.
        """
        print("RUNNING APPLICATIONS")
        st.title("🏀 Basketball Statistics")
        st.markdown(
            """
            This application finds the best matching historical players using vector search with [txtai](https://github.com/neuml/txtai).
            Raw data is from the [Baseball Databank](https://github.com/chadwickbureau/baseballdatabank) GitHub project. Read [this
            article](https://medium.com/neuml/explore-baseball-history-with-vector-search-5778d98d6846) for more details.
        """
        )

        player, search = st.tabs(["Player", "Search"])

        # Player tab
        with player:
            self.player()

        # Search
        with search:
            self.search()

    def player(self):
        """
        Player tab.
        """

        st.markdown(
            "Match by player-season. Each player search defaults to the best season sorted by OPS or Wins Adjusted."
        )

        # Get parameters
        params = self.params()

        # Category and stats
        category = self.category(params.get("category"), "category")
        stats = self.total if category == "Totals" else self.per_game

        # Player name
        name = self.name(stats.names, params.get("name"))

        # Player metrics
        active, best, metrics = stats.metrics(name)

        # Player season
        season = self.year(active, params.get("SEASON_ID"), best)

        # Display metrics chart
        if len(active) > 1:
            self.chart(category, metrics)

        # Run search
        results = stats.search(name, season)

        # Display results
        self.table(
            results,
            ["link", "PLAYER_NAME", "SEASON_ID", "TEAM_ABBREVIATION"]
            + stats.columns[1:],
        )

        # Save parameters
        st.experimental_set_query_params(category=category, name=name, season=season)

    def search(self):
        """
        Stats search tab.
        """

        st.markdown("Find players with similar statistics.")

        category = self.category("Totals", "searchcategory")
        with st.form("search"):
            if category == "Totals":
                stats, columns = self.total, self.total.columns[7:]
            elif category == "Per Game":
                stats, columns = self.per_game, self.per_game.columns[7:]

            # Enter stats with data editor
            inputs = st.data_editor(
                pd.DataFrame([dict((column, None) for column in columns)]),
                hide_index=True,
            ).astype(float)

            submitted = st.form_submit_button("Search")
            if submitted:
                # Run search
                results = stats.search(row=inputs.to_dict(orient="records")[0])

                # Display table
                self.table(
                    results,
                    ["link", "PLAYER_NAME", "SEASON_ID", "TEAM_ABBREVIATION"]
                    + stats.columns[1:],
                )

    def params(self):
        """
        Get application parameters. This method combines URL parameters with session parameters.

        Returns:
            parameters
        """

        # Get parameters
        params = st.experimental_get_query_params()
        params = {x: params[x][0] for x in params}

        # Sync parameters with session state
        if all(x in st.session_state for x in ["category", "name", "season"]):
            # Copy session year if category and name are unchanged
            params["season"] = (
                str(st.session_state["season"])
                if all(
                    params.get(x) == st.session_state[x] for x in ["category", "name"]
                )
                else None
            )

            # Copy category and name from session state
            params["category"] = st.session_state["category"]
            params["name"] = st.session_state["name"]

        return params

    def category(self, category, key):
        """
        Builds category input widget.

        Args:
            category: category parameter
            key: widget key

        Returns:
            category component
        """

        # List of stat categories
        categories = ["Totals", "Per Game"]

        # Get category parameter, default if not available or valid
        default = (
            categories.index(category) if category and category in categories else 0
        )

        # Radio box component
        return st.radio("Stat", categories, index=default, horizontal=True, key=key)

    def name(self, names, name):
        """
        Builds name input widget.

        Args:
            names: list of all allowable names

        Returns:
            name component
        """

        # Get name parameter, default to random weighted value if not valid
        name = (
            name
            if name and name in names
            else random.choices(
                list(names.keys()), weights=[names[x][1] for x in names]
            )[0]
        )

        # Sort names for display
        names = sorted(names)

        # Select box component
        return st.selectbox("Name", names, names.index(name), key="name")

    def year(self, years, year, best):
        """
        Builds year input widget.

        Args:
            years: active years for a player
            year: year parameter
            best: default to best year if year is invalid

        Returns:
            year component
        """

        # Get year parameter, default if not available or valid
        year = int(year) if year and year.isdigit() and int(year) in years else best

        # Slider component
        return int(
            st.select_slider("Year", years, year, key="year")
            if len(years) > 1
            else years[0]
        )

    def chart(self, category, metrics):
        """
        Displays a metric chart.

        Args:
            category: Batting or Pitching
            metrics: player metrics to plot
        """

        # Key metric
        metric = self.total.metric() if category == "Totals" else self.per_game.metric()

        # Cast year to string
        metrics["SEASON_ID"] = metrics["SEASON_ID"].astype(str)

        # Metric over years
        chart = (
            alt.Chart(metrics)
            .mark_line(
                interpolate="monotone", point=True, strokeWidth=2.5, opacity=0.75
            )
            .encode(
                x=alt.X("SEASON_ID", title=""),
                y=alt.Y(metric, scale=alt.Scale(zero=False)),
            )
        )

        # Create metric median rule line
        rule = (
            alt.Chart(metrics)
            .mark_rule(color="gray", strokeDash=[3, 5], opacity=0.5)
            .encode(y=f"median({metric})")
        )

        # Layered chart configuration
        chart = (
            (chart + rule)
            .encode(y=alt.Y(title=metric))
            .properties(height=200)
            .configure_axis(grid=False)
        )

        # Draw chart
        st.altair_chart(chart + rule, theme="streamlit", use_container_width=True)

    def table(self, results, columns):
        """
        Displays a list of results as a table.

        Args:
            results: list of results
            columns: column names
        """

        if results:
            st.dataframe(
                results,
                column_order=columns,
                column_config={
                    "link": st.column_config.LinkColumn("Link", width="small"),
                    "SEASON_ID": st.column_config.NumberColumn("Season"),
                    "PLAYER_NAME": "Name",
                    "TEAM_ABBREVIATION": "Team",
                    "PLAYER_AGE": "Age",
                },
            )
        else:
            st.write("Player-Year not found")


@st.cache_resource(show_spinner=False)
def create():
    """
    Creates and caches a Streamlit application.

    Returns:
        Application
    """

    return Application()


if __name__ == "__main__":
    print("STARTING")
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    print("CREATING APP...")
    # Create and run application
    app = create()

    print("RUNNING APP...")
    app.run()
