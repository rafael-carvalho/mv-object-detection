from detect import detect_objects
import configparser
import shutil
import requests
from datetime import datetime
import meraki as mera

config = configparser.ConfigParser()

config.read("config.ini")
api_key = config.get('meraki', 'api_key')
network_id = config.get('meraki', 'network')

meraki = mera.DashboardAPI(api_key, output_log=False)

def get_cameras(serials=None):
    devices = meraki.devices.getNetworkDevices(network_id)
    cameras = [x for x in devices if x['model'].startswith('MV')]
    return cameras

# Download file from URL and write to local tmp storage
def __download_file(file_name, file_url):
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
    cams = get_cameras()
    for cam in cams:
        snapshot_output = meraki.cameras.generateNetworkCameraSnapshot(network_id, cam['serial'])
        snapshot_url = snapshot_output['url']
        saved_image_path = __download_file(f'snapshots/{cam["name"]}.png', snapshot_url)
        if saved_image_path:
            detections, classes, output_path = detect_objects(saved_image_path, show_window=False)
            if detections > 0:
                print(f'{cam["name"]} --> {detections} object of {len(set(classes))} different classes = {str(classes)}')
            else:
                print(f"{cam['name']} No objects were detected :'()")
        else:
            print(f'{cam["name"]} Error downloading the snapshot')
