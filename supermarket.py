import cv2
import time
from datetime import datetime
import traceback
import requests


def add_text_annotation_to_video(frame, frame_counter, contextual_annotations):
    prepended_annotations = list()
    #prepended_annotations.append(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    prepended_annotations.append(f'Current frame: {frame_counter}')
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


def process_rtsp_stream_with_file_annotation(link, txt_url="https://us-central1-ise-mailer-analyzer-206320.cloudfunctions.net/cashier", fps_throttle=16, width=640, height=320):
    frame_counter = 0
    error_counter = 0
    error_threshold = 10
    annotations = None
    print(f'Initiating Stream to {link}')
    try:
        cap = cv2.VideoCapture(link)
        print('Stream established')
        while True:
            # Capture frame-by-frame
            ret, frame = cap.read()
            if frame is None:
                error_counter += 1
                print(f'Subsequent frames lost {error_counter}')
                time.sleep(1)
                if error_counter == error_threshold:
                    raise Exception(f'Stream not available. Please check {link}')
            else:

                if frame_counter % fps_throttle == 0:
                    if not annotations:
                        annotations = []

                    if width and height:
                        width = int(width)
                        height = int(height)
                        frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

                    add_text_annotation_to_video(frame, frame_counter, annotations)
                    print(f'Annotating over frame {frame_counter}')
                    cv2.imshow(link, frame)
                    error_counter = 0
                elif frame_counter % fps_throttle == 1:
                    annotations = fetch_annotations(txt_url)


            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            frame_counter += 1

    except:
        traceback.print_exc()
        print('Error')

    finally:
        # When everything done, release the capture and destroy the window
        print('Releasing resources')
        cap.release()
        cv2.destroyAllWindows()


def fetch_annotations(txt_url):
    annotations = list()
    right_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response = requests.get(txt_url + '?cache='+right_now)
    if response.status_code == 200:
        filename = 'output.txt'
        with open(filename, 'wb') as input_file:
            input_file.write(response.content)
            input_file.close()
            with open(filename, 'r') as items:
                annotations = list(items)
               # print(annotations)
                items.close()
    else:
        annotations.append('Error')
    return annotations


if __name__ == '__main__':
    link = 'rtsp://192.168.100.5:9000/live'
    txt_url = "https://us-central1-ise-mailer-analyzer-206320.cloudfunctions.net/cashier"

    process_rtsp_stream_with_file_annotation(link, txt_url)