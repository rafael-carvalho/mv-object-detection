################################################################
# Author : Rafa Carvalho   (May 16th, 2020)                    #
# E-mail : rafacarv@cisco.com                                  #
# Code: https://github.com/rafael-carvalho/mv-object-detection #
################################################################

from detect import detect_objects
import utils
import meraki

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
    utils.create_directories()
    api_key, organization_id, network_id, target_cameras, rtsp = utils.load_config_variables()
    if not api_key or not network_id:
        raise Exception('Meraki API Key and Meraki Network Id are mandatory params. You can hard code them above, '
                        'use a config.ini file or set them as environment variables. Camera serials should be a string '
                        'separated by ;. Camera serials are optional')

    dashboard = utils.establish_meraki_connection(api_key)
    cams = utils.get_cameras(dashboard, network_id, target_cameras)
    print(f'Will process snapshots of {len(cams)} MV cameras')
    if not cams:
        raise Exception(f'The network ({network_id}) used does not contain cameras or the cameras you selected are '
                        'not on the selected network.')
    else:
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
                saved_image_path = utils.download_file(f'{utils.FOLDER_SNAPSHOTS}/{serial_number}.png', snapshot_url)
                detections, classes, output_path = detect_objects(saved_image_path, show_window=False)
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
