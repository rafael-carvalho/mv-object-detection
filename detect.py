#############################################
# Object detection - YOLO - OpenCV
# Author : Arun Ponnusamy   (July 16, 2018)
# Website : http://www.arunponnusamy.com
############################################

import cv2
import numpy as np
import os
import pathlib
from download_weights import download_weights

######### FOLDER STRUCTURE
YOLO_CFG_FOLDER = 'yolo-cfg'
YOLO_CLASSES_FOLDER = 'yolo-classes'
YOLO_WEIGHTS_FOLDER = 'yolo-weights'

######## YOLO CONFIGS
YOLO_CONFIG = f'{YOLO_CFG_FOLDER}/yolov3.cfg'
YOLO_CLASSES = f'{YOLO_CLASSES_FOLDER}/yolov3.txt'
YOLO_WEIGHTS = f'{YOLO_WEIGHTS_FOLDER}/yolov3.weights'


######### HYPERPARAMETERS
NMS_THRESHOLD = 0.4
CONF_THRESHOLD = 0.5


def detect_objects(input_path, output_path=None, show_window=False, conf_threshold=CONF_THRESHOLD, nms_threshold=NMS_THRESHOLD, yolo_weights=YOLO_WEIGHTS, yolo_cfg=YOLO_CONFIG, yolo_classes=YOLO_CLASSES):
    root = os.getcwd()

    if not output_path:
        file_name = input_path.split('/')[-1]
        output_path = f'{root}/output/{file_name}'

    if not os.path.exists(yolo_weights):
        print(f'Weights file not found. Will download into {yolo_weights}')
        path = pathlib.Path(yolo_weights)
        path.parent.mkdir(parents=True, exist_ok=True)
        download_weights(filename=yolo_weights)



    image = cv2.imread(input_path)

    Width = image.shape[1]
    Height = image.shape[0]
    scale = 0.00392

    classes = None

    with open(yolo_classes, 'r') as f:
        classes = [line.strip() for line in f.readlines()]

    colors = np.random.uniform(0, 255, size=(len(classes), 3))

    net = cv2.dnn.readNet(yolo_weights, yolo_cfg)

    blob = cv2.dnn.blobFromImage(image, scale, (416, 416), (0, 0, 0), True, crop=False)

    net.setInput(blob)

    outs = net.forward(get_output_layers(net))

    class_ids = []
    confidences = []
    boxes = []

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x = int(detection[0] * Width)
                center_y = int(detection[1] * Height)
                w = int(detection[2] * Width)
                h = int(detection[3] * Height)
                x = center_x - w / 2
                y = center_y - h / 2
                class_ids.append(class_id)
                confidences.append(float(confidence))
                boxes.append([x, y, w, h])

    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

    for i in indices:
        i = i[0]
        box = boxes[i]
        x = box[0]
        y = box[1]
        w = box[2]
        h = box[3]
        draw_prediction(image, class_ids[i], confidences[i], round(x), round(y), round(x + w), round(y + h), classes, colors)

    if show_window:
        cv2.imshow("object detection", image)
        while True:
            if cv2.waitKey(0) & 0xFF == ord('q'):
                break

    cv2.imwrite(output_path, image)
    cv2.destroyAllWindows()

    output_classes = list()
    for id in class_ids:
        output_classes.append(classes[id])

    output_classes = set(output_classes)
    return len(indices), output_classes, output_path


def get_output_layers(net):
    layer_names = net.getLayerNames()

    output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

    return output_layers


def draw_prediction(img, class_id, confidence, x, y, x_plus_w, y_plus_h, classes, colors):
    label = str(classes[class_id])

    color = colors[class_id]

    cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), color, 2)

    cv2.putText(img, f'{label} (' + '%.2g' % confidence + ')', (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


