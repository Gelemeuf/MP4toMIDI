"""
# SPDX-License-Identifier: GPL-3.0-or-later

# By Thomas LEFRANC

# A program python to transform a video of a barrel organ into a MIDI file
"""
import cv2
import numpy as np

# Permet de faire une liste de toutes les couleurs présentent dans l'image
"""def present_color(buf, width, height, frame_start, frame_end):
    tab = []
    for i in range(frame_start, frame_end+1):
        for y in range(width):
            for z in range(height):
                if(tab == []):
                    tab.append(buf[i][y][z])  
                for k in tab:
                    if(buf[i][y][z] != k):
                        tab.append(buf[i][y][z])     
    return tab"""
    
# buf[IMAGE][COLONNE][LIGNE][RGB]
def pixel(buf, image, ligne, colonne,):
    return buf[image][ligne][colonne]

def printMATRIX(buf, frame):
    cv2.namedWindow('frame 10')
    cv2.imshow('frame 10', buf[2000])

    cv2.waitKey(0)


def MP4toMATRIX(frame_start, frame_end):
    cap = cv2.VideoCapture('test.mp4')
    frameCount = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frameWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frameHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print("number of frame :", frameCount, "| Width :",
          frameWidth, ", Height :", frameHeight)

    buf = np.empty((frameCount, frameHeight, frameWidth, 3), np.dtype('uint8'))

    fc = 0
    ret = True

    while (fc < frameCount and ret):
        ret, buf[fc] = cap.read()
        fc += 1

    cap.release()
    
    """ tab = present_color(buf,frameWidth,frameHeight,frame_start,frame_end)
    print(tab)"""