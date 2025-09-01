# This file contains the actual JourneyMap-specific merging functions, such as map merging but also Waypoint Merging
import argparse, re, os, sys, datetime
from pathlib import Path, PurePath
import CompareFolders as cf
import multiprocessing as multipr
from tqdm import tqdm

# Requires extra packages
import amulet.nbt as anbt
from IPython.lib.pretty import pprint as pp

# https://docs.wand-py.org/en/0.6.12/guide/draw.html#composite
from wand.image import Image, COMPOSITE_OPERATORS
from wand.drawing import Drawing

# Sry i couldn't be bothered writing this myself so it's chatgpt

# Initialize the argument parser
parser = argparse.ArgumentParser(description="Merging of two or more JourneyMap data points. If the Map would be an art canvas, there would be a base layer, and every layer would paint on top of it, overwriting what's underneath. The layers in this case are ordered by the last edited timestamp of each individual file.")

parser.add_argument("OUT", type=str, help="The folder to output the merged data to.")
parser.add_argument("LAYER", type=str, help="The first JM Data Folder.")
parser.add_argument("LAYERS", nargs='+', type=str, help="Any additional JM Data Folders you want to merge with the base.")

parser.add_argument(
    "--manual", 
    action="store_true", 
    help="Instead of ordering all files from all folders by timestamp and merging them that way, the timestamp will be disregarded and the folders will be \"layered\" on top of each other in the order that they're specified."
)
parser.add_argument(
    "-w", "--waypoints", 
    action="store_true",
    help="Only Process Waypoints"
)
parser.add_argument(
    "-m", "--map", 
    action="store_true",
    help="Only Process Map"
)
parser.add_argument(
    "-d", "--debug", 
    action="store_true",
    help="Enable Debug Logs for specific scenarios (Currently only ImageMagick Child Processes)"
)
parser.add_argument(
    "-y", "--yes", 
    action="store_true",
    help="Do not ask for confirmation before merging. Highly discouraged to be used by non-developers."
)

# Parse the command-line arguments
args = parser.parse_args()


# Coloring
class tcol:
    # <nothing> Foreground
    # B Background
    # FB Background and Foreground set, foreground for better contrast
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    FBGREEN = '\033[30;102m'

###############
# MAP MERGING #
###############

def layer_images_and_save(outPath: Path, *inPaths: Path):
    """
    Does what it says, takes multiple images and layers them over each other. No fancy effects, just what we need.
    """
    os.makedirs(str(outPath.parent), exist_ok=True)
    newFile = open(outPath, mode='+wb')
    images: list[Image] = list()
    for filePath in inPaths:
        # Get File data
        file = open(filePath, 'rb')
        data = file.read()
        file.close()
        # Open image into ImageMagick 
        images.append(Image(blob=data))
    with Drawing() as draw:
        # Remove the first image, that will be our bottom most image
        first = images.pop(0)
        first.alpha_channel = True
        for image in images:
            draw.composite('over', 0, 0, image.width, image.height, image)
        # Draw the composite effects on the base image and save it
        draw(first)

        # The library used by journeymap for png writing and reading (PNGJ) is very brittle, so we need to change more parameters to make it not throw up and error out with "all rows have not been written" https://github.com/leonbloy/pngj/blob/fd2a2ea75a517b9d21d97a3b9280df3cc33572d6/src/main/java/ar/com/hjg/pngj/PngWriter.java#L283
        # TI figured out like half of the parameters, but Gemini and ChatGPT kinda forced me to apply EVERYTHING at once which is why it now properly works
        # NOTE: Theoretically, the map works without any of these parameters! It only becomes a problem once you try to export the map.
        # NOTE: I feel like only one or two of these are needed, but I'm too lazy too test so imma just keep it as-is. And it doesn't cost performance either way.
        first.strip()
        first.compression = 'zip'
        first.interlace_scheme = 'no'
        first.artifacts['png:color-type'] = '6'
        first.artifacts['png:bit-depth'] = '8'
        first.artifacts['PNG:compression-filter'] = '0'
        first.artifacts['PNG:format'] = 'png32'
        first.artifacts['PNG:compression-filter'] = '0'
        first.artifacts['PNG:compression-level'] = '9'
        first.artifacts['PNG:compression-strategy'] = '0'
        first.artifacts['png:exclude-chunk'] = 'all'
        first.save(newFile)
    newFile.close()

def get_all_image_files(*roots: Path):
    """
    Gets all PNGs
    """
    files = dict()
    if args.manual:
        files = cf.compare(*roots)
    else:
        files = cf.merge(*roots)
    compiled = re.compile('\\.png$')
    filesList = {key: contents for key, contents in tqdm(files.items(), desc='Getting Image Paths') if compiled.search(str(key))}
    print(f'Total Images: {len(filesList)} ({round(len(filesList)/len(files)*100, 1)}%)')
    return filesList

def _helper_merge_images_and_save(x):
    if x.pop(0):
        sys.stdout = open(f'./debug_log/' + str(os.getpid()) + ".log", "w")
    return layer_images_and_save(*x)

def merge_images_and_save(outRoot: Path, images: dict[PurePath, list[Path]]):
    """
    Takes a root output path, and a dict of Paths in said root with their associated existing images. Runs this in parallel for higher performance.
    """
    # multipr help: https://stackoverflow.com/a/9786225
    # progressbar help: https://stackoverflow.com/a/56041325
    
    # Setup images for execution
    imagesList = images.items()
    imagesList = list(map(lambda x : [args.debug, outRoot / x[0], *x[1]], imagesList))
    # Create Pool for multiprocessing
    pool = multipr.Pool()
    data = pool.imap_unordered(_helper_merge_images_and_save, imagesList) # Note: You need to ask for the result of this, otherwise it won't process
    # Create a loading bar and "ask" for the results
    results = tqdm(data, total=len(imagesList), desc='Fusing Maps')
    list(results) # here is the asking for results command

    print(f'{tcol.GREEN}Finished processing!{tcol.RESET}')

def image_get_merge_save(outRoot: Path, inRoots: list[Path]):
    print('')
    print(f'{tcol.YELLOW}-----------')
    print('MAP MERGING')
    print(f'-----------{tcol.RESET}')
    print('')
    images = get_all_image_files(*inRoots)
    merge_images_and_save(outRoot, images)

####################
# WAYPOINT MERGING #
####################
type nbtDataStoreStuff = anbt.CompoundTag[anbt.CompoundTag]

def get_waypoints(*inputRoots: Path):
    if args.manual:
        # By time
        inputRootsDict: dict[Path, float] = dict()
        for root in inputRoots:
            nbtPath = root / 'waypoints' / 'WaypointData.dat'
            if nbtPath.is_file():
                inputRootsDict[os.path.getmtime(str(nbtPath))] = nbtPath
        inputRootsDict = dict(sorted(inputRootsDict.items()))
        inputFiles: list[Path] = list(map(lambda x : x[0], inputRootsDict))
    else:
        # By manual order
        inputFiles: list[Path] = list()
        for root in inputRoots:
            nbtPath = root / 'waypoints' / 'WaypointData.dat'
            if nbtPath.is_file():
                inputFiles.append(nbtPath)
    return inputFiles

def merge_waypoint_data_and_save(outFilePath: Path | list[Path], *inputFiles: Path):
    """
    Takes the WaypointData.dat files from the given Roots, merges them and writes the output.
    """
    # Read Data
    print('(1) Reading WaypointData.dat files')
    nbtDataList: list[anbt.NamedTag[nbtDataStoreStuff]] = list()
    for file in tqdm(inputFiles):
        nbtDataList.append(anbt.read_nbt(filepath_or_buffer=file.read_bytes(), preset=anbt.java_encoding))

    # Merge Data, overwrite existing stuff
    nbtBase = nbtDataList.pop(0)
    nbtBaseWaypoints: nbtDataStoreStuff = nbtBase[1]['waypoints'] # NOTE: These should be pointers. If you notice the output NBT to be the same as the oldest/first Waypoint file, then this is not a pointer for some reason.
    print('(2) Merging Data')
    nbtBaseGroups: nbtDataStoreStuff = nbtBase[1]['groups']
    for nbtData in tqdm(nbtDataList, leave=True, position=0):
        nbtDataWaypoints: nbtDataStoreStuff = nbtData[1]['waypoints']
        nbtDataGroups: nbtDataStoreStuff = nbtData[1]['groups']

        # Waypoint Merging
        for key, value in tqdm(nbtDataWaypoints.items(), desc='Waypoints', leave=False, position=1): # Does not provide value for some reason?
            nbtBaseWaypoints[key] = value

        # Waypoint Group Merging
        for key, value in tqdm(nbtDataGroups.items(), desc='Groups', leave=False, position=1):
            nbtBaseGroups[key] = value

    # Save data in new directory
    print('(3) Saving Data')
    final = nbtBase.to_nbt(compressed=False, little_endian=False, string_encoding=anbt.mutf8_encoding) # NOTE: Saving compressed makes JourneyMap label it "corrupted"
    if outFilePath.__class__ == Path:
        outFilePath = [outFilePath]
    outFilePathList: list[Path] = outFilePath

    for location in outFilePathList:
        os.makedirs(str(location.parent), exist_ok=True)
        file = open(location, '+bw')
        file.write(final)
        file.close()
    print(f'{tcol.GREEN}Saving Done!{tcol.RESET}')

def waypoint_get_merge_save(outRoot: Path, inRoots: list[Path]):
    print('')
    print(f'{tcol.CYAN}---------------------')
    print('MERGING WAYPOINT DATA')
    print(f'---------------------{tcol.RESET}')
    print('')
    outs = [
        outRoot / 'waypoints' / 'WaypointData.dat',
        outRoot / 'waypoints' / 'backup' / 'WaypointData.dat'
    ]
    ins = get_waypoints(*inRoots)
    merge_waypoint_data_and_save(outs, *ins)

def getUserYesNo():
    while True:
        answer = input('type "yes" to continue, "no" to cancel. Then press enter/return.\n')
        match answer.lower():
            case 'y':
                return True
            case 'yes':
                return True
            case 'confirm':
                return True
            case 'n':
                return False
            case 'no':
                return False
            case 'nope':
                return False
            case 'not':
                return False
            case _:
                print('Try again.')

if __name__ == '__main__':
    outPath = Path(args.OUT)
    inputPaths = [Path(args.LAYER), *map(lambda x : Path(x), args.LAYERS)]
    processedFlag = False

    safeToContinue = True

    print('')

    # Check if given paths are valid directories
    for uwu in inputPaths:
        if not uwu.is_dir():
            safeToContinue = False
            if not uwu.exists():
                # Doesn't even exist
                print(f'{tcol.RED}Directory does not exist: {str(uwu)}{tcol.RESET}')
            else:
                # Is not a directory
                print(f'{tcol.RED}Is not a directory: {str(uwu)}{tcol.RESET}')

    if not safeToContinue:
        print('')
        print('Possible issues could be:')
        print('- Accidental Escaping. Backslash (\\) is used for escaping characters, and Windows Paths include those. Escaping means a quote like " or \' looses it\'s meaning as "End of text". Even the Python provided sys.argv cannot deal with them. To prevent escaping, replace \\ with \\\\, as this escapes the escape. You should also remove the trailing \\ at the end of paths')
        exit(1)

    if outPath.is_file():
        safeToContinue = True
        print(f'{tcol.RED}Output path is a file.{tcol.RESET} Use a different path or delete it first.')
        exit(1)

    # Check if given paths are only ever given ONCE.
    allPaths = [outPath, *inputPaths]
    duplicatePaths = set()
    for toTest in allPaths:
        if allPaths.count(toTest) > 1:
            safeToContinue = False
            duplicatePaths.add(str(toTest))
    
    if not safeToContinue:
        print(f'{tcol.RED}Duplicate Paths found, do not use the same path twice.{tcol.RESET} Even in manual mode this is completely counter-productive.')
        for i in duplicatePaths:
            print(i)
        exit(2)

    # Let's ask the user some questions first

    if not args.yes:
        # Confirm Paths
        print(f'Output Path: {str(outPath)}')
        stringedInputPaths = list(map(lambda x : str(x.absolute()), inputPaths))
        print(f'Input Paths: \n- {'\n- '.join(stringedInputPaths)}')
        print('')
        print('Do you confirm these paths?')
        if not getUserYesNo():
            print('Cancelling!')
            exit(0)

        # Confirm output folder has files
        if bool(list(outPath.iterdir())):
            print('')
            print(f'The output folder already has files! Are you sure you want to {tcol.RED}overwrite and permanently delete the files?{tcol.RESET}')
            if not getUserYesNo():
                print('Cancelling!')
                exit(0)

        # We will merge these things btw
        print('')
        print('We will merge the following:')
        if args.map:
            print('- World Map')
        if args.waypoints:
            print('- Waypoints (including Groups)')
        if (args.map == False and args.waypoints == False):
            print('- World Map')
            print('- Waypoints (including Groups)')
        
        print('')
        print(f'This is your {tcol.YELLOW}last confirmation{tcol.RESET} that everything you specified is correct. After that the script will run as expected.')
        if not getUserYesNo():
            print('Cancelling!')
            exit(0)

    # All good? Let's go with the rest of the maps

    print('All good, starting the merging process... (spam Ctrl-C to cancel)')
    os.makedirs(str(outPath.parent), exist_ok=True)
    if args.debug:
        os.makedirs(f'./debug_log/', exist_ok=True)

    # Go through flags
    if args.map:
        processedFlag = True
        image_get_merge_save(outPath, inputPaths)
    if args.waypoints:
        processedFlag = True
        waypoint_get_merge_save(outPath, inputPaths)

    # If none of the flags were set, nothing would have been processed, so here comes the default behaviour
    if not processedFlag:
        image_get_merge_save(outPath, inputPaths)
        waypoint_get_merge_save(outPath, inputPaths)
    
    print('')
    print(f"{tcol.FBGREEN}================{tcol.RESET}")
    print(f"{tcol.FBGREEN}Merge completed!{tcol.RESET}")
    print(f"{tcol.FBGREEN}================{tcol.RESET}")
    print('')
    # https://stackoverflow.com/a/33206814
    print(f'{tcol.RED}LEGAL DISCLAIMER{tcol.RESET}')
    print("If it was actually successful is something you have to check yourself. This script did what we told it to do, so now it's your due diligence to check it did everything as you want it to be done.")
    print("ALWAYS KEEP BACKUPS. ALWAYS.")
    print("WE HAVE NO LIABILITY IF IT WASN'T ABLE TO MERGE. But if it did fail, please open an issue on GitHub with all relevant details, thanks!")
    print('')