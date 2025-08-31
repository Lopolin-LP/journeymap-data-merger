# Journey Map Data Merger
Merge Map and Waypoints, effortlessly!

## Usage
1. Install [Python](https://www.python.org/) - [MS Store](https://apps.microsoft.com/detail/9ncvdn91xzqp?hl=en-US&gl=US)
2. Install [ImageMagick](https://imagemagick.org/) - No MS Store
3. Open up a terminal of your choice (cmd/powershell)
4. Install required Modules and pray there isn't some weird issue:
   ```powershell
   pip install amulet-nbt==5.0.1a1 tqdm wand
   ```
5. Grab the project files, just download source code using the download button. I ain't compiling anything here.
6. After download and extraction, open another terminal in that folder
7. `py ./JourneyMapMerger.py "<Output Path>" "<Input Path>" "<Input Path...>"` (as many inputs as you need)
8. Press enter and wait
9.  Where you specified the output the data is now
10. Either zip up the contents of that folder or just manually move them into the JourneyMap installation

## More Help
### Finding JourneyMap folders

#### Option 1: Exporting the data (easy)
1. Go to the Minecraft Server/World and log in
2. Go to the JourneyMap settings, for example via the fullscreen map
3. Press Import/Export at the bottom and export it somewhere you remember
4. Extract the ZIP archive because this script doesn't take care of that.

#### Option 2: Grabbing the folder directly
Wherever your minecraft profile is saved (I assume `.minecraft` for this), you also have your mods and other things saved. In there, alongside the `mods` folder, there is `journeymap`. The folder structure is something like this
- mp (multiplayer)
  - \<Server Name or other identifiers\>
    - overworld
    - the_end
    - the_nether
    - waypoints
      - backup
        - WaypointData.dat
      - WaypointData.dat
- sg (singleplayer)
  - \<world name or other identifiers\>
    - \<exact same structure as in mp\>

The folder with an identifier is what we need. This is the "Root" of the Map and Waypoint data. And the input paths point to exactly these roots.

So for a Multiplayer Server with the name `My server` and your friend calling it `absolute cinema` you both have that servers data saved in `.minecraft/journeymap/data/mp/My~server/` and `.minecraft/journeymap/data/mp/absolute~cinema/` respectively.

### Replacing JourneyMap folders

#### Option 1: Importing the data (easy)
1. First 3 steps of exporting the data, except you now select import instead of export. Please note that this replaces the whole data though

#### Option 2: Replacing the folder directly
You remember where the folders were from before? You have to move the result there again, under the same name (so rename the old data to something else).

## ToDo
- [ ] Image Gallery
- [ ] Video Tutorial
- [ ] Better Error Handling if things don't go perfectly as expected
  - [ ] Map
  - [ ] Waypoints
- [ ] Zip handling
  - [ ] Extraction
  - [ ] Archiving
- [ ] CLI
  - [ ] Support for manually specifiying waypoint files

## FAQ
### There are Invalid Directories I didn't write! Please help!
Read the error message and follow instructions. Turn `.\Desktop\new Best world\` into `.\Desktop\\new Best world` (double \\ infront of n because \\n translates to new line)

### I can't overwrite my JourneyMap data directory with the new data!
Because you shouldn't. Simple as that. Just rename the folders so they fit.

### Why is there blatant AI usage in the source code
Programming is IMO not art. It is utility. Guess why Kevin MacLeod started using AI for music, he saw it as utility.

Anyways that's besides the point. I was programming this sometimes only half awake and at some point I just didn't want to write the annoying parts and relearn some module only for basic things to work. AI was only really helpful in first setting up argparse and somehow getting PNGJ to accept the files created with ImageMagick. I don't think I really used it for something else.