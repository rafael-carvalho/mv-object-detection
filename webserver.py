from flask import Flask, render_template, Response, request, make_response
from detect import detect_objects
import cv2
import time
from datetime import datetime
from step2 import *
import json
import traceback
import detect

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


@app.route('/form', methods=['POST'])
def process_form():
    '''
    Processes each step of the form.
    '''
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


@app.route('/video_feed/weights/<weights>/confidence/<confidence>/link/<path:link>/')
def video_feed(link, weights, confidence):
    '''
    Yields the RTSP stream with annotations.
    '''
    return Response(detect.process_rtsp_stream(link=link, weights=weights, conf_threshold=float(confidence), show_window=False),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/classes/<weights>')
def get_classes(weights):
    '''
    Returns the list of classes that are assigned to the weights. For every .weights there must be a .txt with the same name for this to work.
    '''
    status_code = 500
    output = {}

    try:
        classes = utils.get_classes_for_weights(weights)
        output = {
            'classes': sorted(classes)
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
    print('Running webserver')
    app.run(host='0.0.0.0',port='5000', debug=True)
