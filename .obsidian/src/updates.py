#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import json
import os

plugins_dir = "plugins"
readme_file = "README.md"


def create_if_not_exists(readme_file):
    try:
        with open(readme_file, "x") as f:
            f.write("# My Project\n\n")
    except FileExistsError:
        readme_file = os.path.join(os.getcwd(), readme_file)


def update_plugins(readme_file: str, plugins_dir: str) -> None:
    """Update a Markdown file with a table of integrated plugins.

    Args:
        readme_file (str): Path to the Markdown file to update.
        plugins_dir (str): Path to the directory containing plugin directories with "manifest.json" files.

    Returns:
        None
    """
    with open(readme_file, "a") as f:
        f.write("\n## Integrated Plugins\n\n")
        f.write("| Plugin Name | Version | Author |\n")
        f.write("| --- | --- | --- |\n")
        for plugin_name in os.listdir(plugins_dir):
            manifest_path = os.path.join(plugins_dir, plugin_name, "manifest.json")
            with open(manifest_path, "r") as manifest_file:
                manifest = json.load(manifest_file)
                name = manifest.get("name")
                version = manifest.get("version")
                author = manifest.get("author")
                author_url = manifest.get("authorUrl")
                f.write(f"| {name} | {version} | [{author}]({author_url}) |\n")


def update_readme(readme_file: str, plugins_dir: str) -> None:
    """Update a Markdown file with a table of integrated plugins from a directory.

    Args:
        readme_file (str): Path to the Markdown file to update. If the file does not exist, it will be created.
        plugins_dir (str): Path to the directory containing plugin directories with "manifest.json" files.

    Returns:
        None
    """
    create_if_not_exists(readme_file)
    update_plugins(readme_file, plugins_dir)


def main():
    update_readme()
