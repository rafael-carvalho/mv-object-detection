# Adapted from https://www.arunponnusamy.com/yolo-object-detection-opencv-python.html
# RTSP feed adapted from https://github.com/zishor/yolo-python-rtsp
#############################################
# Object detection - YOLO - OpenCV
# Author : Arun Ponnusamy   (July 16, 2018)
# Website : http://www.arunponnusamy.com
############################################

import cv2
import numpy as np
import os
import pathlib
import utils
from datetime import datetime
import time

######### HYPERPARAMETERS (DEFAULT VALUES)
### You don't have to change these for the adventure lab!! ##############
NMS_THRESHOLD = 0.4
CONF_THRESHOLD = 0.5
#### Don't change these unless you know what you are doing ;) ##############

global COLORS
COLORS = None


def detect_objects(input_path=None, output_path=None, show_window=False, input_array=None, conf_threshold=CONF_THRESHOLD, nms_threshold=NMS_THRESHOLD, yolo_weights=None):
    """
    Takes a locally stored image as the input and runs the model to detect objects within a specific class set.

    :param input_path: filepath to image that will be processed
    :param output_path: where the processed image will be saved
    :param show_window: if set to True, a window will pop-up with the image. If False, the image will only be saved.
    :param conf_threshold: double between 0 and 1 that represents the minimum confidence of the detection to be
    considered a detection
    :param input_array: numpy array with the representation of the image
    :param nms_threshold: double between 0 and 1 - Non-maximum Suppression threshold.
    :param yolo_weights: str filepath to the model that has been trained (weights)
    :param yolo_cfg: str filepath to YOLO configuration file
    :param yolo_classes: str filepath to a list of classes that can be detected
    :return: tuple with 3 values:
        number of (detections),
        their (classes);
        where the output image was stored (output_path)
    """
    root = os.getcwd()

    # Creates the folder for the output images
    if not output_path and input_array is None:
        file_name = input_path.split('/')[-1]
        output_path = f'{root}/output/{file_name}'

    # Downloads the weights file (pre-trained) model if it does not exist already
    if not yolo_weights:
        yolo_weights = utils.YOLO_WEIGHTS

    if not os.path.exists(yolo_weights):
        print(f'Weights file not found. Will download into {utils.YOLO_WEIGHTS}')
        path = pathlib.Path(utils.YOLO_WEIGHTS)
        path.parent.mkdir(parents=True, exist_ok=True)
        utils.download_weights()

    weights_name = yolo_weights.split('/')[-1].split('.weights')[0]
    yolo_cfg = f'{utils.YOLO_CFG_FOLDER}/{weights_name}.cfg'
    yolo_classes = f'{utils.YOLO_CLASSES_FOLDER}/{weights_name}.txt'

    if not os.path.exists(yolo_cfg):
        raise Exception('Yolo config file could not be found')

    if not os.path.exists(yolo_classes):
        raise Exception('Yolo classes file could not be found')

    if input_path:
        # Reads the image file into an OpenCV matrix
        image = cv2.imread(input_path)
    else:
        # Already have an input array provided from the video stream
        image = input_array

    # Sets some image attributes
    Width = image.shape[1]
    Height = image.shape[0]
    scale = 0.00392

    #print(f"{Width} x {Height}")

    # Reads the text file with a list of all the categories of objects that have been trained on the model.
    classes = None

    with open(yolo_classes, 'r') as f:
        classes = [line.strip() for line in f.readlines()]

    global COLORS
    if COLORS is None:
        COLORS = np.random.uniform(0, 255, size=(len(classes), 3))

    # Loads the Neural Network from the file, based on the config that has been passed.
    net = cv2.dnn.readNet(yolo_weights, yolo_cfg)

    # Transforms the image into a Blob to make sure every image always has the same aspect ratio.
    blob = cv2.dnn.blobFromImage(image, scale, (416, 416), (0, 0, 0), True, crop=False)

    # Initializes the Neural Network with the input
    net.setInput(blob)

    # Forward propagates the input with the pre-trained weights and saves the outputs.
    # This is where the 'magic happens' and the detections are made from the model
    outs = net.forward(get_output_layers(net))

    class_ids = []
    confidences = []
    boxes = []

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > conf_threshold:
                center_x = int(detection[0] * Width)
                center_y = int(detection[1] * Height)
                w = int(detection[2] * Width)
                h = int(detection[3] * Height)
                x = center_x - w / 2
                y = center_y - h / 2
                class_ids.append(class_id)
                confidences.append(float(confidence))
                boxes.append([x, y, w, h])

    # Draws the boxes around the object as well as the confidence level.
    # Every class gets the same bounding box color.
    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

    for i in indices:
        i = i[0]
        box = boxes[i]
        x = box[0]
        y = box[1]
        w = box[2]
        h = box[3]
        draw_prediction(image, class_ids[i], confidences[i], round(x), round(y), round(x + w), round(y + h), classes, COLORS)

    # If the show_window parameter is set to True, then it shows a pop-up window.
    # If the user presses the letter 'q', the pop-up window goes away
    if show_window:
        cv2.imshow("object detection", image)
        while True:
            if cv2.waitKey(0) & 0xFF == ord('q'):
                break
        # Remove the pop-up window
        cv2.destroyAllWindows()

    # Lists of the detected classes
    output_classes = list()
    for id in class_ids:
        output_classes.append(classes[id])

    output_classes = set(output_classes)

    if output_path:
        # Writes the image from the memory to a local file
        cv2.imwrite(output_path, image)
        return len(indices), list(output_classes), output_path
    else:
        return len(indices), list(output_classes), image


def get_output_layers(net):
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
    return output_layers


def draw_prediction(img, class_id, confidence, x, y, x_plus_w, y_plus_h, classes, colors):
    '''
    Draws the rectangle around the object with the class name and the confidence level perceived by the model
    '''
    label = str(classes[class_id])
    color = colors[class_id]
    cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), color, 2)
    cv2.putText(img, f'{label} (' + '%.2g' % confidence + ')', (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


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

    cv2.rectangle(frame, (0, 0), (250, (len(annotations) + 1) * padding), (0, 0, 0), -1)

    counter = 1
    for annotation in annotations:
        if annotation:
            x = padding
            y = counter * padding
            text_coordinates = (x, y)
            cv2.putText(frame, annotation, text_coordinates, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            counter += 1

    return frame


def process_rtsp_stream(link, show_window, camera_info=None, weights=None, conf_threshold=0.6, fps_throttle=30, width=960, height=480):
    if not weights:
        weights = utils.YOLO_WEIGHTS

    print(f'Establishing direct stream to {link}')
    print(f'Using {weights}')
    print(f'Confidence Threshold: {conf_threshold}')
    print(f'FPS Throttle: {fps_throttle}')

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
                                                                              conf_threshold=conf_threshold,
                                                                              yolo_weights=f'{utils.YOLO_WEIGHTS_FOLDER}/{weights}'
                                                                              )
                annotations.append(f'Using {weights}')
                annotations.append(f'{qnt_objects} objects detected')
                annotations.append(f'{output_classes}')

                frame_out = annotated_image
                print(f'{qnt_objects} objects detected')

            # encode OpenCV raw frame to jpg and displaying it
            add_text_annotation_to_video(frame, frame_counter, camera_info, annotations)
            if show_window:
                cv2.imshow(link, frame_out)
            else:
                ret, jpeg = cv2.imencode('.jpg', frame_out)
                yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
            #cv2.imshow(link, frame_out)

        frame_counter += 1

    cap.release()