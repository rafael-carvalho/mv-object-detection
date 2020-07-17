################################################################
# Author : Rafa Carvalho   (June 16th, 2020)                    #
# E-mail : rafacarv@cisco.com                                  #
# Code: https://github.com/rafael-carvalho/mv-object-detection #
################################################################

from datetime import datetime
import cv2
import time
import configparser
import requests
import meraki
import os
import pathlib
import traceback
from step2 import *

FOLDER_SNAPSHOTS = 'snapshots'
FOLDER_OUTPUT = 'output'

# Environment keys
API_KEY = None
NETWORK_ID = None
TARGET_CAMERAS = None

CONFIG_FILE_PATH = 'config.ini'

import tensorflow as tf


def __load_keras_model(file_path="keras-weigths/imagenet_inception_resnet_v2_feature_vector_4"):
    model = tf.keras.models.load_model(file_path)
    model.build([None, 299, 299, 3])# Batch input shape.

    print(model.summary())


def add_text_annotation_to_video(frame, frame_counter, camera_info, contextual_annotations):
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


def process_rtsp_stream_keras(link, camera_info=None, fps_throttle=10):
    cap = cv2.VideoCapture(link)
    frame_counter = 0
    error_counter = 0
    error_threshold = 10
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if frame is None:
            error_counter += 1
            print(f'Subsequent frames lost {error_counter}')
            time.sleep(1)
            if error_counter == error_threshold:
                raise Exception(f'Stream not available. Please check {link}')

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
                                                                              conf_threshold=0.6,
                                                                              )
                annotations.append(f'{qnt_objects} objects detected')
                annotations.append(f'{output_classes}')

                frame_out = annotated_image
                print(f'{qnt_objects} objects detected')

            add_text_annotation_to_video(frame_out, frame_counter, camera_info, annotations)

            cv2.imshow(link, frame_out)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        frame_counter += 1

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()

    '''
    while True:
        #if frame_limit > 0 and frame_counter > frame_start + frame_limit:
        #    writer.close()
        #    break
        if frame_counter % fps_throttle == 0:
            ret, frame = cap.read()
            if ret and frame_counter >= frame_start:
                print('Detecting objects in frame ' + str(frame_counter))
                qnt_objects, output_classes, annotated_image = detect_objects(input_array=frame, show_window=False)
                print(f'{qnt_objects} objects detected')
                cv2.imshow('stream', annotated_image)
                if cv2.waitKey(1) == ord('q'):  # q to quit
                    raise StopIteration

                #cv2.imshow(annotated_image)
                #print(qnt_objects)
                #print(output_classes)
                #if frame_limit > 0:
                #    writer.send(annotated_image)
            else:
                print('Skipping frame ' + str(frame_counter))
        else:
            print('FPS throttling. Skipping frame ' + str(frame_counter))
        frame_counter += 1
    '''


if __name__ == '__main__':
    __load_keras_model()

    api_key, network_id, target_cameras, rtsp_serial = load_config_variables()
    dashboard = establish_meraki_connection(api_key)
    camera_info = None
    camera_info = dashboard.devices.getDevice(rtsp_serial)
    #cams = get_cameras(dashboard, network_id, target_cameras)
    print(f'Will work with camera {rtsp_serial}')




    #rtsp_link = "rtsp://192.168.100.6:9000/live"
    rtsp_link = None
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

    print(f'Establishing direct stream to {rtsp_link}')
    process_rtsp_stream_keras(rtsp_link, camera_info)
