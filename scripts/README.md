See header of the script file for information.

| Script                                           | Short description                                    | Windows | Linux | macOS |
| :---                                             | :---                                                 |  :---:  | :---: | :---: |
| [`start.bat`](start.bat)                         | Run python script in venv with environment variables |    ✓    |   ✓   |       |
| [`common.py *`](common.py)                       | Scripts common parts                                 |    ✓    |   ✓   |   ✓   |
| [`archiver.py`](archiver.py)                     | Work with zip archives                               |    ✓    |   ✓   |       |
| [`clearmyram.sh`](clearmyram.sh)                 | Clear swap and file system cache                     |         |   ✓   |       |
| [`compare_backups.py`](compare_backups.py)       | Compare the contents of folders                      |    ✓    |   ✓   |       |
| [`download_vk_albums.py`](download_vk_albums.py) | Download photo albums from VK                        |    ✓    |   ✓   |   ✓   |
| [`stream_recorder.py`](stream_recorder.py)       | Download livestreams                                 |    ✓    |   ✓   |   ✓   |
| [`video_downloader.py`](video_downloader.py)     | Download videos                                      |    ✓    |   ✓   |   ✓   |

*\* - not executable*

For arguments and more information call:
```
start.bat script.py --help
```

Or just run to select script from menu:
```
start.bat
```

If you suddenly start getting errors, script dependencies may be out of date. You can update them with command:
```
start.bat --upgrade
```
