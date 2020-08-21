from flask import Flask, render_template, Response, request, make_response
from detect import detect_objects
import cv2
import time
from datetime import datetime
from step2 import *
import json
import traceback

app = Flask(__name__, template_folder='templates', static_folder='static')


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

    #cv2.rectangle(frame, (0, 0), (400, (len(annotations) + 1) * padding), (255, 255, 255), -1)
    counter = 1
    for annotation in annotations:
        if annotation:
            x = padding
            y = counter * padding
            text_coordinates = (x, y)
            cv2.putText(frame, annotation, text_coordinates, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            counter += 1

    return frame


def process_rtsp_stream(link, camera_info=None, weights=None, fps_throttle=30, width=640, height=320):
    cap = cv2.VideoCapture(link)
    if not weights:
        weights = 'yolo-weights/yolov3.weights'

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
            if width and height:
                width = int(width)
                height = int(height)
                frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

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
                                                                              yolo_weights=f'{utils.YOLO_WEIGHTS_FOLDER}/{weights}'
                                                                              )
                annotations.append(f'Using {weights}')
                annotations.append(f'{qnt_objects} objects detected')
                annotations.append(f'{output_classes}')

                frame_out = annotated_image
                print(f'{qnt_objects} objects detected')

                # encode OpenCV raw frame to jpg and displaying it
            add_text_annotation_to_video(frame, frame_counter, camera_info, annotations)
            ret, jpeg = cv2.imencode('.jpg', frame_out)

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
            #cv2.imshow(link, frame_out)

        frame_counter += 1

    cap.release()


@app.route('/form', methods=['POST'])
def process_form():
    output = None
    status_code = 500
    try:
        data = request.get_json()

        api_key = data['api_key']
        if 'organization_id' in data.keys() and data['organization_id'] != "":
            organization_id = data['organization_id']
        else:
            organization_id = None
        if 'network_id' in data.keys() and data['network_id'] != "":
            network_id = data['network_id']
        else:
            network_id = None

        if 'camera_serial' in data.keys() and data['camera_serial'] != "":
            camera_serial_number = data['camera_serial']
        else:
            camera_serial_number = None

        if api_key and not organization_id:
            dashboard = utils.establish_meraki_connection(api_key)
            data = dashboard.organizations.getOrganizations()

            options = list()
            for org in data:
                options.append({
                    'name': org['name'],
                    'id': org['id'],
                    'disabled': False
                })

            output = {
                'stage': 'organizations',
                'next': 'Get Networks',
                'options': options

            }
            status_code = 200
        elif api_key and organization_id and not network_id:
            dashboard = utils.establish_meraki_connection(api_key)
            data = dashboard.organizations.getOrganizationNetworks(organizationId=organization_id)
            options = list()
            for net in data:
                options.append({
                    'name': net['name'],
                    'id': net['id'],
                    'disabled': 'camera' not in net['productTypes']
                })

            output = {
                'stage': 'networks',
                'next': 'Get Cameras',
                'options': options
            }
            status_code = 200
        elif api_key and organization_id and network_id and not camera_serial_number:
            dashboard = utils.establish_meraki_connection(api_key)
            devices = dashboard.networks.getNetworkDevices(network_id)
            cameras = [x for x in devices if x['model'].startswith('MV')]
            print(cameras)
            options = list()
            for cam in cameras:
                offline = cam['lanIp'] is None
                if 'name' in cam.keys():
                    name = f'{cam["name"]} '
                    if offline:
                        name += ' (OFFLINE)'
                else:
                    name = ''

                options.append({
                    'name': f"{name} - ({cam['model']})",
                    'id': cam['serial'],
                    'disabled': offline
                })

            output = {
                'stage': 'cameras',
                'next': 'Enable RTSP and Run',
                'options': options
            }
            status_code = 200

        elif api_key and organization_id and network_id and camera_serial_number:
            dashboard = utils.establish_meraki_connection(api_key)

            rtsp_info = dashboard.camera.getDeviceCameraVideoSettings(camera_serial_number)

            if rtsp_info['externalRtspEnabled']:
                rtsp_link = rtsp_info["rtspUrl"]
            else:
                rtsp_link = False
                response = dashboard.camera.updateDeviceCameraVideoSettings(camera_serial_number, externalRtspEnabled=True)
                if response['externalRtspEnabled']:
                    rtsp_link = response["rtspUrl"]
                    print(f'RTSP Enabled: {rtsp_link}')
                else:
                    raise Exception(f'Error while enabling RTSP on camera {camera_serial_number}')

            output = {
                'stage': None,
                'next': None,
                'rtsp_link': rtsp_link
            }
            status_code = 200

    except:
        output = {
            'error_message': 'Something wrong happened',
            'error_traceback': traceback.format_exc(),
        }

        traceback.print_exc()

    finally:
        return make_response(json.dumps(output), status_code)


@app.route('/video_feed/weights/<weights>/link/<path:link>/')
def video_feed(link, weights):
    return Response(process_rtsp_stream(link=link, weights=weights),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/classes/<weights>')
def get_classes(weights):
    status_code = 500
    output = {}

    try:
        classes = utils.get_classes_for_weights(weights)
        output = {
            'classes': classes
        }
        print(classes)
        status_code = 200
    except:
        output = {
            'error_message': 'Something wrong happened',
            'error_traceback': traceback.format_exc(),
        }
        traceback.print_exc()
    finally:
        return make_response(json.dumps(output), status_code)


@app.route('/')
def index():
    print(utils.load_config_variables())
    api_key, organization_id, network_id, target_cameras, rtsp = utils.load_config_variables()
    weights = utils.check_existing_weights()
    print(weights)
    if not weights:
        utils.download_weights()

    return render_template('index.html', api_key=api_key, organization_id=organization_id, network_id=network_id, target_cameras=target_cameras, rtsp=rtsp, weights=weights)


if __name__ == '__main__':
    # defining server ip address and port
    app.run(host='0.0.0.0',port='5000', debug=True)
