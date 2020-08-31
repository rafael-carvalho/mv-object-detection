import configparser
import requests
import pathlib
import meraki
import gdrive_downloader
import os
import traceback
import glob

######### FOLDER STRUCTURE
YOLO_CFG_FOLDER = 'yolo-cfg'
YOLO_CLASSES_FOLDER = 'yolo-classes'
YOLO_WEIGHTS_FOLDER = 'yolo-weights'

######## YOLO CONFIGS
YOLO_CONFIG = f'{YOLO_CFG_FOLDER}/yolov3-coco.cfg'
YOLO_CLASSES = f'{YOLO_CLASSES_FOLDER}/yolov3-coco.txt'
YOLO_WEIGHTS = f'{YOLO_WEIGHTS_FOLDER}/yolov3-coco.weights'

#### PROJECT FOLDERS
FOLDER_SNAPSHOTS = 'snapshots'
FOLDER_OUTPUT = 'output'

# Environment keys
API_KEY = None
ORGANIZATION_ID = None
NETWORK_ID = None
TARGET_CAMERAS = None
RTSP = None

CONFIG_FILE_PATH = 'config.ini'

def load_config_variables():
    """
    Sets up the environment with the API Key and the Network ID of your Meraki environment.
    If you don't want all cameras on your network to be scanned, you can create a string that contains a series
    of Serial Numbers separated by ;
    :return: api key (string); network_id (string); target_cameras (list of string serials)
    """
    api_key = None
    network_id = None
    organization_id = None
    target_cameras = None
    rtsp = None

    if API_KEY and NETWORK_ID:
        api_key = API_KEY
        network_id = NETWORK_ID
        organization_id = ORGANIZATION_ID
        target_cameras = TARGET_CAMERAS
        rtsp = RTSP

    elif os.path.exists(CONFIG_FILE_PATH):
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE_PATH)

        if config.has_option('meraki', 'API_KEY'):
            api_key = config.get('meraki', 'API_KEY')
        if config.has_option('meraki', 'NETWORK_ID'):
            network_id = config.get('meraki', 'NETWORK_ID')
        if config.has_option('meraki', 'ORGANIZATION_ID'):
            organization_id = config.get('meraki', 'ORGANIZATION_ID')
        if config.has_option('meraki', 'CAMERAS'):
            target_cameras = config.get('meraki', 'CAMERAS')
        if config.has_option('meraki', 'RTSP'):
            rtsp = config.get('meraki', 'RTSP')

    else:
        api_key = os.getenv('API_KEY')
        network_id = os.getenv('NETWORK_ID')
        target_cameras = os.getenv('CAMERAS')
        rtsp = os.getenv('RTSP')
        organization_id = os.getenv('ORGANIZATION_ID')

    if target_cameras:
        target_cameras = target_cameras.split(';')

    return api_key, organization_id, network_id, target_cameras, rtsp


def create_directories():
    """
    Creates the directories needed by the script: /snapshots and /output.
    The /yolo-weights directory will be created by detect.py
    """
    if not os.path.exists(FOLDER_SNAPSHOTS):
        path = pathlib.Path(FOLDER_SNAPSHOTS)
        print(f'Snapshots folder does not exist... creating: {path}')
        path.mkdir(parents=True, exist_ok=True)

    if not os.path.exists(FOLDER_OUTPUT):
        path = pathlib.Path(FOLDER_OUTPUT)
        print(f'Output folder does not exist... creating: {path}')
        path.mkdir(parents=True, exist_ok=True)


def establish_meraki_connection(api_key):
    """
    Uses the Meraki SDK to create the Dashboard object
    :param api_key: key assigned to a Meraki network with cameras
    :return: DashboardAPI object
    """
    return meraki.DashboardAPI(api_key, output_log=False, print_console=False)


def get_cameras(dashboard, network_id, target_cameras=None):
    """
    Retrieves the camera objects from Meraki's dashboard.

    Parameters
    dashboard : DashboardAPI
        Object instantiated with admin's API key
    network_id : str
        Meraki network id that has cameras
    target_cameras : list
        Optional list of camera serial numbers
    :return: list of cameras that will have snapshots taken
    """
    devices = dashboard.networks.getNetworkDevices(network_id)
    cameras = [x for x in devices if x['model'].startswith('MV')]
    if target_cameras:
        cameras = [x for x in devices if x['serial'] in target_cameras]
    return cameras



def check_existing_weights():
    '''
       Checks to see if the weights file has its respective classes file and the respective cfg file.
    '''
    weights = [f for f in glob.glob(f"{YOLO_WEIGHTS_FOLDER}/*.weights")]
    cfgs_names = [f.split('/')[-1].replace('.cfg', '') for f in glob.glob(f"{YOLO_CFG_FOLDER}/*.cfg")]
    classes_names = [f.split('/')[-1].replace('.txt', '') for f in glob.glob(f"{YOLO_CLASSES_FOLDER}/*.txt")]

    valid_weights = []
    for w in weights:
        name = w.split('/')[-1].replace('.weights', '')
        if name in cfgs_names and name in classes_names:
            valid_weights.append(w)

    return valid_weights


def get_classes_for_weights(weights):
    '''
        Returns the list of classes that are assigned to the weights. For every .weights there must be a .txt with the same name for this to work.
    '''
    name = weights.split('/')[-1].replace('.weights', '')
    classes_filename = f'{YOLO_CLASSES_FOLDER}/{name}.txt'
    output = []
    if os.path.exists(classes_filename):
        with open(classes_filename, 'r') as f:
            output = [line.strip() for line in f.readlines()]
    return output


def download_weights():
    return gdrive_downloader.download_yolov3_weights()

def download_file(file_name, file_url):
    """
    Downloads an image into a file. We'll try 30 times before we give up.
    Parameters
    ----------
    file_name : str
        Relative / full path of the destination filename
    file_url : str
        URL of the snapshot.
    """
    attempts = 1
    while attempts <= 30:
        r = requests.get(file_url, stream=True)
        if r.ok:
            with open(file_name, 'wb') as f:
                for chunk in r:
                    f.write(chunk)
            return file_name
        else:
            attempts += 1
    print(f'Unsuccessful in 30 attempts retrieving {file_url}')
    return None