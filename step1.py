################################################################
# Author : Rafa Carvalho   (May 16th, 2020)                    #
# E-mail : rafacarv@cisco.com                                  #
# Code: https://github.com/rafael-carvalho/mv-object-detection #
################################################################

from detect import detect_objects

if __name__ == '__main__':
    # Determine the path to the image
    image_path = 'sample_images/baseball.jpg'

    # Trigger the detection algorithm
    detections, classes, output_path = detect_objects(image_path, show_window=True, conf_threshold=.3)

    # Print results
    if detections > 0:
        print(f'{detections} object of {len(set(classes))} different classes = {str(classes)}')
        print(f'{output_path}')
    else:
        print(f"No objects were detected :(")
