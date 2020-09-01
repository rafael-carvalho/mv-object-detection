#Adapted from https://github.com/nsadawi/Download-Large-File-From-Google-Drive-Using-Python
from tqdm import tqdm
import requests

'''
These are the Google Drive ID's for 
'''
HOSTED_FILES = [
    {
        'description': 'Coco Weights for YoloV3',
        'filename': 'yolo-weights/yolov3-coco.weights',
        'file_id': '1pkjwtV-kRoQLpgzaBurriwwcwd0t9Q5x'
    },
    {
        'description': 'YoloV3 trained to detect mask / no-mask trained by Francisco',
        'filename': 'yolo-weights/yolov3-mask.weights',
        'file_id': '1stbsUnWeZaqSQjGfcwQp0kQ0njcBqRUj'
    },
]


def download_file_from_google_drive(id, destination):
    url = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(url, params={'id':id}, stream=True)
    token = get_confirm_token(response)

    if token:
        params = { 'id' : id, 'confirm' : token }
        response = session.get(url, params=params, stream=True)

    save_response_content(response, destination)


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None


def save_response_content(response, destination):
    chunk_size = 32768
    total_size = int(response.headers.get('content-length', 0))
    if not total_size:
        total_size = 238000000 # Hard coding the size of the weights file. If you change the file, change this!

    t = tqdm(total=total_size, unit='iB', unit_scale=True, desc='Downloading weights')
    with open(destination, "wb") as f:
        for chunk in response.iter_content(chunk_size):
            if chunk: # filter out keep-alive new chunks
                t.update(len(chunk))
                f.write(chunk)



def download_yolov3_weights():
    '''
    Downloads all files listed on the HOSTED_FILES variable above
    '''
    for file_dict in HOSTED_FILES:
        download_file_from_google_drive(file_dict['file_id'], file_dict['filename'])
    return True