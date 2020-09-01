################################################################
# Author : Rafa Carvalho   (June 16th, 2020)                    #
# E-mail : rafacarv@cisco.com                                  #
# Code: https://github.com/rafael-carvalho/mv-object-detection #
################################################################

'''
This class taps into the RTSP stream of an MV camera and detects objects seen by the camera. This is is an alternative
version to the webserver class. This has proven to have better performance on updating the screen, even when you
keep higher image dimensions. We believe this is due to the fact that you remove the web client <-> web server
communication overhead.

You don't need to use this file for the Adventures Lab
'''


from datetime import datetime
import cv2
import time
import utils
from detect import detect_objects

FOLDER_SNAPSHOTS = 'snapshots'
FOLDER_OUTPUT = 'output'

# Environment keys
API_KEY = None
NETWORK_ID = None
TARGET_CAMERAS = None


def add_text_annotation_to_video(frame, frame_counter, camera_info, contextual_annotations):
    '''
    Quick way to add text to an image. We paint a rectangle and overlay some text in white over it.
    '''
    prepended_annotations = list()
    prepended_annotations.append(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    prepended_annotations.append(f'Current frame: {frame_counter}')
    if camera_info:
        prepended_annotations.append(f"{camera_info['serial']} - {camera_info['model']}")

    annotations = prepended_annotations

    padding = 15
    for context in contextual_annotations:
        if context:
            annotations.append(context)

    cv2.rectangle(frame, (0, 0), (400, (len(annotations) + 1) * padding), (0, 0, 0), -1)
    counter = 1
    for annotation in annotations:
        if annotation:
            x = padding
            y = counter * padding
            text_coordinates = (x, y)
            cv2.putText(frame, annotation, text_coordinates, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            counter += 1

    return frame


def process_rtsp_stream(rtsp_link, yolo_weights, conf_threshold=0.6, fps_throttle=10, camera_info=None):
    '''
    Infinite loop that captures the RTSP stream of the camera and detects objects based on teh
    '''
    cap = cv2.VideoCapture(rtsp_link)
    frame_counter = 0
    error_counter = 0
    error_threshold = 10
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if frame is None:
            error_counter += 1
            print(f'Consecutive frames lost {error_counter}')
            time.sleep(1)
            if error_counter == error_threshold:
                raise Exception(f'Stream not available. Please check {rtsp_link}')

        elif frame_counter % fps_throttle == 0:
            error_counter = 0
            detect = True
            annotations = list()
            if not detect:
                print(f'Raw frame {frame_counter}')
                frame_out = frame

            else:
                print(f'Detecting objects in frame {frame_counter}')
                qnt_objects, output_classes, annotated_image = detect_objects(input_array=frame,
                                                                              conf_threshold=conf_threshold,
                                                                              yolo_weights=yolo_weights,
                                                                              )
                annotations.append(f'{qnt_objects} objects detected')
                annotations.append(f'{output_classes}')

                frame_out = annotated_image
                print(f'{qnt_objects} objects detected')

            add_text_annotation_to_video(frame_out, frame_counter, camera_info, annotations)

            cv2.imshow(rtsp_link, frame_out)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        frame_counter += 1

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    '''
    This is an optional why of interacting with your MV RTSP stream. The webserver version is more feature rich and 
    more user friendly. This is a more hands-on option where you can hard code more data.
    
    '''

    '''
    If you have set up environment variables (see utils.py), we'll load it from there.
    '''
    camera_info = None
    rtsp_link = None

    api_key, organization_id, network_id, target_cameras, rtsp_serial = utils.load_config_variables()
    dashboard = utils.establish_meraki_connection(api_key)

    camera_info = dashboard.devices.getDevice(rtsp_serial)
    #cams = get_cameras(dashboard, network_id, target_cameras)
    print(f'Will work with camera {rtsp_serial}')

    '''
    You can also opt to hard-code the RTSP address, which can be found on your Meraki Dashboard.
    Just uncomment the line below and change the value of the string.
    More info: https://documentation.meraki.com/MV/Advanced_Configuration/External_RTSP
    '''

    # rtsp_link = "rtsp://192.168.100.6:9000/live"
    if not rtsp_link:
        print(f'Checking RTSP Status')
        response = dashboard.camera.getDeviceCameraVideoSettings(rtsp_serial)
        if response['externalRtspEnabled']:
            rtsp_link = response["rtspUrl"]
            print(f'RTSP Enabled: {rtsp_link}')
        else:
            print(f'Enabling RTSP...')
            response = dashboard.camera.updateDeviceCameraVideoSettings(rtsp_serial, externalRtspEnabled=True)
            if response['externalRtspEnabled']:
                rtsp_link = response["rtspUrl"]
                print(f'RTSP Enabled: {rtsp_link}')
            else:
                raise Exception(f'Error while enabling RTSP on camera {rtsp_serial}')

    '''
    Setup the variables used for the object annotation. 
    Yolo Weights: path to where you keep the weights.
    conf_threshold: 
    '''
    yolo_weights = 'yolo-weights/yolov3-mask.weights'
    conf_threshold = 0.3
    fps_throttle = 10

    print(f'Establishing direct stream to {rtsp_link}')
    print(f'Using {yolo_weights}')
    print(f'Confidence Threshold: {conf_threshold}')
    print(f'FPS Throttle: {fps_throttle}')

    '''
    It will start an infinite loop. Press q on your keyboard if you want to quit
    '''
    process_rtsp_stream(rtsp_link, yolo_weights, conf_threshold, fps_throttle, camera_info)
