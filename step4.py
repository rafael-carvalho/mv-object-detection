import os

if __name__ == '__main__':

    cfg = 'yolo-cfg/yolov3.cfg'
    weights = 'yolo-weights/yolov3.weights'
    output = 'yolov3-coco.h5'
    cmd = f'python convert_darknet_to_keras.py {cfg} {weights} {output}'

    os.system(cmd)