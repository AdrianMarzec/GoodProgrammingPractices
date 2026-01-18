#detector_yolo.py
import os
import uuid
import cv2 as cv
import numpy as np
from urllib.request import urlopen #pobieranie obrazów z URL

#Wczytuje obraz z URL, dekoduje, obrabia by model yolo wykrył ludzi, zwraca ilość zliczonych ludzi
def detect_people(path_or_url, save_img=False, save_path=''):
    net = cv.dnn.readNet("yolov3.weights", "yolov3.cfg") #wczytanie modelu

    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        req = urlopen(path_or_url)
        arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
        img = cv.imdecode(arr, -1) #dekodowanie obrazu do numpy array
    else:
        img = cv.imread(path_or_url) #nie url, zwykła ścieżka

    (height, width) = img.shape[:2] #wymiary

    blob = cv.dnn.blobFromImage(img, 1 / 255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    output_layer_name = net.getUnconnectedOutLayersNames()
    output_layers = net.forward(output_layer_name)

    people = [] #lista wykrytych ludzi (zaznaczone prostokąty) w formacie (x, y, w, h)
    confidences = [] #lista pewności wykrycia

    #iteracja po wszystkich predykcjach
    for output in output_layers:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            if class_id == 0 and confidence > 0.5: #tylko osoby powyżej 0.5 pewności
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)

                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                people.append((x, y, w, h))
                confidences.append(float(confidence))

    #non-max suppression (NMS), usuwa nakładające się prostokąty
    boxes = [(x, y, w, h) for (x, y, w, h) in people]
    indices = cv.dnn.NMSBoxes(
        boxes,
        confidences,
        score_threshold=0.5,
        nms_threshold=0.4
    )

    #zaznaczenie ludzi na obrazie (prostokąty)
    for i in indices:
        (x, y, w, h) = boxes[i]
        label = f"Person: {confidences[i]:.2f}"
        cv.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 1)
        cv.putText(img,
                   label,
                   (x, y - 8),
                   cv.FONT_HERSHEY_SIMPLEX,
                   0.4,
                   (0, 255, 0),
                   1)

    '''cv.imshow("Image", img)
    cv.waitKey(0)
    cv.destroyAllWindows()'''

    #Zapis jeśli zaznaczone
    if save_img:
        unique_file_name = f"{uuid.uuid4()}.jpg"

        full_path = os.path.join(save_path, unique_file_name)
        cv.imwrite(full_path, img)
        print(f"Saving image to: {full_path}")
        '''#print(f"Saving image to: {full_path}")
        success = cv.imwrite(full_path, img)
        #print(success)'''

    return len(indices) #liczba ludzi
