from detect import detect_objects

if __name__ == '__main__':
    # Determine the path to the image
    image_path = '/Users/rafael.carvalho/Downloads/airport-3511342_1920.jpg'

    # Trigger the detection algorithm
    detections, classes, output_path = detect_objects(image_path, show_window=True, conf_threshold=.3, nms_threshold=0.1)

    # Print results
    if detections > 0:
        print(f'{detections} object of {len(set(classes))} different classes = {str(classes)}')
    else:
        print(f"No objects were detected :'()")