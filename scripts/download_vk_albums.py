#!/usr/bin/env python3

'''
This file is part of 2trvl/dotfiles
Personal repository with scripts and configs
Which is released under MIT License
Copyright (c) 2022 Andrew Shteren
---------------------------------------------
             Vk Album Downloader             
---------------------------------------------
Downloads albums of the specified person or
group in VK. Saves photos at the best
resolution and writes a description 
to the metadata

'''
import argparse
import math
import os
import sys
from urllib.parse import urlparse
from urllib.request import urlretrieve

import pyexiv2
import vk_api

from core.common import charsForbidden
from core.widgets import show_menu

parser = argparse.ArgumentParser(description="Vk Album Downloader")
parser.add_argument(
    "-a",
    "--albums",
    nargs="*",
    type=int,
    help=(
        "albums id to download. if empty all will be downloaded. "
        "if this parameter is not specified, this will create a menu "
        "where you be able to choose which albums to download"
    )
)
parser.add_argument(
    "--download-path",
    help="where to download albums. current directory by default"
)

requiredGroup = parser.add_argument_group("required arguments")
requiredGroup.add_argument(
    "-l",
    "--login",
    required=True,
    help="vk account login"
)
requiredGroup.add_argument(
    "-p",
    "--password",
    required=True,
    help="vk account password"
)
requiredGroup.add_argument(
    "-o",
    "--owner",
    required=True,
    help="albums owner id or username"
)

args = parser.parse_args()
#  Named variables for simplicity
ownerID = args.owner
albumsID = args.albums


vkSession = vk_api.VkApi(args.login, args.password)
vkSession.auth()

vk = vkSession.get_api()

#  Username to id
if not ownerID.replace("-", "", 1).isnumeric():
    ownerID = vk.utils.resolveScreenName(
        screen_name=ownerID
    )
    ownerID["object_id"] = str(ownerID["object_id"])
    #  Group id must must be indicated with the sign "-"
    if ownerID["type"] == "group":
        ownerID["object_id"] = f"-{ownerID['object_id']}"
    ownerID = ownerID["object_id"]

try:
    albums = vk.photos.getAlbums(
        owner_id=ownerID,
        albums_id=albumsID,
        need_system=1
    )
except vk_api.exceptions.ApiError as ApiError:
    print(ApiError)
    sys.exit(0)

#  Albums selection mode
if albumsID is None:
    albumsID = []
    for index in show_menu(
        "Enter album numbers to download",
        [ album["title"] for album in albums["items"] ]
    ):
        albumsID.append(albums["items"][index]["id"])

if albumsID:
    album = 0
    while album < albums["count"]:
        if albums["items"][album]["id"] not in albumsID:
            albums["items"].pop(album)
            albums["count"] -= 1
        else:
            album += 1

albums = albums["items"]

if args.download_path:
    os.chdir(args.download_path)

if ownerID.startswith("-"):
    ownerName = vk.groups.getById(
        group_id=ownerID[1:]
    )[0]["name"]
else:
    ownerName = vk.users.get(
        user_ids=ownerID
    )[0]
    ownerName = f"{ownerName['first_name']} {ownerName['last_name']}"

ownerName = f"{ownerID} {ownerName}"
os.makedirs(ownerName, exist_ok=True)
os.chdir(ownerName)

for album in albums:
    print(f"Downloading \"{album['title']}\" {album['size']} photos")
    
    album["title"] = album["title"].translate(charsForbidden)
    os.makedirs(album["title"], exist_ok=True)
    os.chdir(album["title"])
    
    #  Maximum number of photos returned by photos.get is 1000
    for chunk in range(math.ceil(album["size"] / 1000)):
        photos = vk.photos.get(
            owner_id=ownerID,
            album_id=album["id"],
            photo_sizes=1,
            count=1000,
            offset=chunk*1000
        )["items"]

        for photo in photos:
            #  Find photo with maximum resolution
            originalPhoto = {"width": 0, "url": ""}
            
            for size in photo["sizes"]:
                if size["width"] > originalPhoto["width"]:
                    originalPhoto["width"] = size["width"]
                    originalPhoto["url"] = size["url"]
            
            filename = urlparse(originalPhoto["url"])
            filename = filename.path.rsplit("/", 1)[1]
            filename = f"{photo['album_id']}_{filename}"
            
            urlretrieve(originalPhoto["url"], filename)
            
            #  Write description to image
            with pyexiv2.Image(filename) as image:
                image.modify_iptc({ "Iptc.Application2.Caption": photo["text"] })

            print(filename)

    os.chdir("..")
