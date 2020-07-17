################################################################
# Author : Rafa Carvalho   (May 16th, 2020)                    #
# E-mail : rafacarv@cisco.com                                  #
# Code: https://github.com/rafael-carvalho/mv-object-detection #
################################################################

from detect import detect_objects
import configparser
import requests
import meraki
import os
import pathlib
import traceback

FOLDER_SNAPSHOTS = 'snapshots'
FOLDER_OUTPUT = 'output'

# Environment keys
API_KEY = None
NETWORK_ID = None
TARGET_CAMERAS = None

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
    target_cameras = None
    rtsp = None

    if API_KEY and NETWORK_ID:
        api_key = API_KEY
        network_id = NETWORK_ID
        target_cameras = TARGET_CAMERAS

    elif os.path.exists(CONFIG_FILE_PATH):
        config = configparser.ConfigParser()
        config.read("config.ini")
        api_key = config.get('meraki', 'API_KEY')
        network_id = config.get('meraki', 'NETWORK_ID')
        if config.has_option('meraki', 'CAMERAS'):
            target_cameras = config.get('meraki', 'CAMERAS')
        if config.has_option('meraki', 'RTSP'):
            rtsp = config.get('meraki', 'RTSP')

    else:
        api_key = os.getenv('API_KEY')
        network_id = os.getenv('NETWORK_ID')
        target_cameras = os.getenv('CAMERAS')
        rtsp = os.getenv('RTSP')

    if not api_key or not network_id:
        raise Exception('Meraki API Key and Meraki Network Id are mandatory params. You can hard code them above, '
                        'use a config.ini file or set them as environment variables. Camera serials should be a string '
                        'separated by ;. Camera serials are optional')

    if target_cameras:
        target_cameras = target_cameras.split(';')

    return api_key, network_id, target_cameras, rtsp


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


def __download_file(file_name, file_url):
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


if __name__ == '__main__':
    """
    Steps:
        1) Create necessary directories;
        2) Connect to Meraki;
        3) Get a list of Meraki Cameras;
        4) For each camera:
            4.1) Downloads a snapshot of the current field of view of the camera;
            4.2) Runs the YOLOv3 model trained on the COCO dataset and stores the image locally.
    """
    create_directories()
    api_key, network_id, target_cameras = load_config_variables()
    dashboard = establish_meraki_connection(api_key)
    cams = get_cameras(dashboard, network_id, target_cameras)
    print(f'Will process snapshots of {len(cams)} MV cameras')
    for cam in cams:
        serial_number = cam['serial']
        model = cam['model']
        print('---------')
        print(f'{serial_number} ({model})')
        try:
            print('    Generating snapshot')
            snapshot_output = dashboard.camera.generateDeviceCameraSnapshot(serial_number)
            print('    Downloaded snapshot')
            snapshot_url = snapshot_output['url']
            print('    Processing objects')
            saved_image_path = __download_file(f'{FOLDER_SNAPSHOTS}/{serial_number}.png', snapshot_url)
            detections, classes, output_path = detect_objects(saved_image_path, show_window=False, conf_threshold=0.3)
            if detections > 0:
                print(f'    {detections} object of {len(set(classes))} '
                      f'different classes = {str(classes)}.')

            else:
                print(f"    No objects were detected.")

            print(f'    {output_path}')

        except meraki.exceptions.APIError:
            print(f"    Error downloading the snapshot. Is the camera online?")

        except:
            print(f"    An unknown error happened when processing camera {serial_number}."
                  f"Uncomment line below for more details")
            # traceback.print_exc()
