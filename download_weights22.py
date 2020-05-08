'''
MIT License

Copyright (c) 2017 Andrea Palazzi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

from google_drive_downloader import GoogleDriveDownloader as gdd

HOSTED_FILE = '1pkjwtV-kRoQLpgzaBurriwwcwd0t9Q5x'

def download_weights(destination_filename, file_id=HOSTED_FILE, unzip=True):
    gdd.download_file_from_google_drive(file_id=file_id, dest_path=destination_filename, unzip=unzip)


if __name__ == '__main__':
    download_weights(destination_filename='/Users/rafael.carvalho/workspace/devnet-create-2020/yolo-weights/yolov3-2.weights')