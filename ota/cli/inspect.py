#!/bin/python3

import click
import pandas as pd

from ota.tools.rpc import OdooRpc, DEFAULT_MODELS
from ota.core.console import console
from ota.core.tools import dataframe_to_table

LOCAL_URL = "http://0.0.0.0:8080"


@click.command()
@click.argument("database")
@click.option("--host", "-h", default=None, type=str, help="Odoo Host")
@click.option("--user", "-u", default=None, type=str, help="User")
@click.option("--password", "-p", default=None, type=str, help="Password")
@click.option(
    "--local",
    "-l",
    is_flag=True,
    default=False,
    type=bool,
    help="Use local database with default credentials",
)
def inspect(database, host, user, password, local):
    """Inspect Database"""

    if local:
        host = "http://localhost:8069"
        user = "admin"
        password = "admin"

    database = OdooRpc(host, database, user, password)

    if not database.is_connected:
        console.log(f"Connection to {database} database failed.")
        exit(1)

    with console.status("Working..."):
        # time.sleep(2)
        apps, count = database.get_applications()

        options = {
            "name": {"style": "magenta", "no_wrap": True},
            "shortdesc": {"justify": "left", "style": "green"},
        }

        console.print(
            dataframe_to_table(
                apps,
                f"Applications ({count})",
                ["name", "shortdesc"],
                column_options=options,
            )
        )

        modules, count = database.get_modules()

        options = {
            "author": {"justify": "right", "style": "cyan", "no_wrap": True},
            "name": {"style": "magenta", "no_wrap": True},
            "shortdesc": {"justify": "center", "style": "green"},
        }

        console.print(
            dataframe_to_table(
                modules,
                f"Modules ({count})",
                ["name", "shortdesc", "author"],
                column_options=options,
            )
        )

    applications = list(
        set(modules["name"]).intersection(set(list(DEFAULT_MODELS.keys())))
    )
    models = [v for k, v in DEFAULT_MODELS.items() if k in applications]
    data = {}

    for model in models:
        stats = database.get_stats(model)
        console.print(f"Model {model}: {stats['total']} record(s)")

        data[model] = {
            k: v
            for k, v in stats.items()
            if k in ["total", "this_month", "this_week", "yesterday"]
        }

        # console.print(tabulate(stats["by_day"], headers="keys"))

        df = stats["top_creators"]
        df = df.astype(str)
        df.rename(columns={"create_uid": "name"}, inplace=True)

        console.print(
            dataframe_to_table(
                df,
                "Creators",
                ["name", "count"],
                # column_options=options,
            )
        )

    df = pd.DataFrame(data)
    df = df.transpose()
    df.reset_index(inplace=True)
    df.rename(columns={"index": "name"}, inplace=True)
    df = df.astype(str)

    col = {"justify": "center", "style": "green"}
    options = {
        "name": {"style": "magenta", "no_wrap": True},
        "yesterday": col,
        "this_week": col,
        "this_month": col,
        "total": col,
    }

    console.print(
        dataframe_to_table(
            df,
            "Records",
            ["name", "yesterday", "this_week", "this_month", "total"],
            column_options=options,
        )
    )


@click.command()
@click.argument("path")
@click.argument("name")
@click.option("--save", "-s", is_flag=True, default=False, type=bool, help="Save")
@click.option("--output", "-o", default="report.json", help="Create blank project")
@click.option("--exclude", "-e", default=None, type=str, help="Exclude")
def analyze(path, name, save, exclude, output):
    """Analyze modules on path"""

    options = {}

    if exclude and isinstance(exclude, str):
        exclude = list(map(str.strip, exclude.split(",")))
        options["exclude"] = exclude

    analysis = Analyze(path=path, name=name, **options)
    analysis.run()

    if save and output:
        analysis.save(output)