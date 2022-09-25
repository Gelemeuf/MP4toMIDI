"""
# SPDX-License-Identifier: GPL-3.0-or-later

# By Thomas LEFRANC

# A python program to transform a barrel organ cardboard MP4 video into a MIDI file
"""

import os
import cv2
import numpy as np
import imageio

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd

from PIL import ImageTk, Image

import mido

#Récupérer le dossier du programme
ProgDir = ""
ProgDir = os.getcwd()

#-------------------------
#Variables globales
#-------------------------

#Dimension de la fenêtre fixe en px
fwidth = 1200
fheight = 600

#Dimension du canva de visualisation en px
fvwidth = 900
fvheight = 500

#Dimension de la vidéo en px
vwidth = 0
vheight = 0

#Variables globales
M = [] #Matrice initiale à partir de la vidéo [Nframe][colonne][ligne][rgb]
aM = [] #Matrice de l'image actuellement affiché

N = 1 #Numéro de l'image actuellement affiché

pos = [] #Liste de la position des notes sur la matrice à taille réelle
line = [] #Liste des identifiants des lignes dessinées sur le canva
lineoffsetG = None
lineoffsetD = None
linepxim1 = None
linepxim2 = None

Nt = [] #Fichier de l'état des notes

r = "" #Chemin du fichier vidéo initial afin de mettre le fichier midi final au même endroit

    
    # Pour un orgue de 29 les notes sont : Do2 - Ré2 - Fa2 - Sol2 - La2 - Do3 - 
    #Ré3 - Mi3 - Fa3 - Fa#3 - Sol3 - Sol#3 - La3 - La#3 - Si3 - Do4 - Do#4 -
    #Ré4 - Ré#4 - Mi4 - Fa4 - Fa#4 - Sol4 - Sol#4 - La4 - La#4 - Si4 - Do5 - Ré5.
    
    # Les fréquences correspondantes sont : 48, 50, 53, 55 ,57, 60, 62, 64, 65, 66, 
    # 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 86

Nn = 0
notes = []

#Listes
liste_config_notes = []
liste_config_general = []

#-------------------------
#Fonctions
#-------------------------

#Permet de convertir un fichier mp4 en matrice
def MP4toMatrixVideo(file):
    cap = cv2.VideoCapture(file)
    frameCount = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frameWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frameHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    global fps
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    global vwidth
    vwidth = frameWidth
    global vheight
    vheight = frameHeight
    
    print("Video Selected :")    
    print("number of frame :", frameCount, "| Width :",frameWidth, ", Height :", frameHeight)
    print("Conversion in progress...")
    
    global M
    M = np.empty((frameCount, frameHeight, frameWidth, 3), np.dtype('uint8'))  
    fc = 0
    frame = []
    ret = True
    while (fc < frameCount and ret):
        ret, frame = cap.read()       
        M[fc] = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        fc += 1
        
    cap.release()
    
    print("Convert video to matrix completed")
    
    cursorA11.set(1)
    cursorA12.set(frameCount-1)
    sA11.config(to=frameCount-2)
    sA12.config(to=frameCount-1)
    slider.config(from_=1)
    slider.config(to=frameCount-1)

def ColorLimit(color,inv,Rmin,Rmax,Gmin,Gmax,Bmin,Bmax):
    if(inv):
        if(int(Rmax)>=int(color[0])>=int(Rmin)):
            if(int(Gmax)>=int(color[1])>=int(Gmin)):
                if(int(Bmax)>=int(color[2])>=int(Bmin)):
                    return 1
                else:
                    return 0
            else:
                return 0
        else:
            return 0
    else:    
        if(int(Rmax)<=int(color[0])<=int(Rmin)):
            if(int(Gmax)<=int(color[1])<=int(Gmin)):
                if(int(Bmax)<=int(color[2])<=int(Bmin)):
                    return 1
                else:
                    return 0
            else:
                return 0
        else:
            return 0

#Permet de convertir une image RGB en une image noir et blanc contraster
def MatrixImageToMatrixContrastedImage():
    global aM
    Mc = []
    Rmin = cursorA311.get()
    Rmax = cursorA312.get()
    Gmin = cursorA321.get()
    Gmax = cursorA322.get()
    Bmin = cursorA331.get()
    Bmax = cursorA332.get()    
    global inverse_contrasted
    
    if(inverse_contrasted.get()):
        for i in aM:
            COL = []
            for y in i:
                if(int(Rmax)>=int(y[0])>=int(Rmin)):
                    if(int(Gmax)>=int(y[1])>=int(Gmin)):
                        if(int(Bmax)>=int(y[2])>=int(Bmin)):
                            COL.append([255,255,255])
                        else:
                            COL.append([0,0,0]) 
                    else:
                        COL.append([0,0,0])
                else:
                    COL.append([0,0,0])       
            Mc.append(COL)
        return np.array(Mc,np.dtype('uint8'))
    else:
        for i in aM:
            COL = []
            for y in i:
                if((int(Rmax)<=int(y[0])<=int(Rmin))==0):
                    if((int(Gmax)<=int(y[1])<=int(Gmin))==0):
                        if((int(Bmax)<=int(y[2])<=int(Bmin))==0):
                            COL.append([255,255,255])
                        else:
                            COL.append([0,0,0]) 
                    else:
                        COL.append([0,0,0])
                else:
                    COL.append([0,0,0])       
            Mc.append(COL)
        return np.array(Mc,np.dtype('uint8'))

#Permet de convertir une matrice vidéo d'un carton défilent en une image
def MatrixVideoToMatrix(buf,nframe,Width,Height,firstframe,lastframe):
    Mv = [] #Matrice de l'image finale
    #On parcours les images en récupérant à chaque fois la première colonnes
    for i in range(nframe):
        col = []
        for z in range(Height-1,0,-1):
            col.append(buf[i][z][0])
        for m in range(6):
            Mv.append(col)
    #On parcours la dernière image pour récuperer les dernières colonnes
    for y in range(1,Width):
        col = []
        for z in range(Height-1,0,-1):
            col.append(buf[i][z][y])
        for m in range(6):  #6,4 px en réalité et non 6 
            Mv.append(col)
    return Mv
                    
def MatrixContrasted_to_NoteTab():
    
    #Le tableau final
    global Nt
    Nt = []
    
    #Les paramètres utiles pour la conversion
    offsetGbutton = caseA13.get()
    offsetDbutton = caseA14.get()
    offsetGvalue = int(cursorA13.get()/fwidth*fvwidth)
    offsetDvalue = int(cursorA14.get()/fwidth*fvwidth)
    Rmin = cursorA311.get()
    Rmax = cursorA312.get()
    Gmin = cursorA321.get()
    Gmax = cursorA322.get()
    Bmin = cursorA331.get()
    Bmax = cursorA332.get()    
    
    pxbetweentwoimagebutton = caseA15.get()
    pxim1 = cursorA161.get() #On récupère la position de la ligne vertical 1
    pxim2 = cursorA162.get() #On récupère la position de la ligne vertical 2
    
    #Définition du nombre de pixel à lire sur chaques images
    global pxpi
    pxpi = 1
    if(pxbetweentwoimagebutton == 1):
        pxpi = pxim2 - pxim1
        if(pxpi < 0): #Dans le cas ou les curseurs seraient inverser
            pxpi = pxpi * -1
        pxpi = pxpi/fwidth*fvwidth #On applique un rapport du à la modification de l'image sur le canva
        pxpi = int(pxpi)
     
    #Lecture du début de fichier en prennant en compte l'offset   
    nimgG = 0
    if(offsetGbutton):
        moveG = offsetGvalue%pxpi #Nombre de pixels à lire avant de décaler d'images
        nimgG = int(offsetGvalue/pxpi) #Nombre d'image à décaler
        
        if(inverse_contrasted.get()): #Si les couleurs sont inclusive
            for i in range(moveG):
                I = M[cursorA11.get()+nimgG-1]
                X= [] #Colonne contenant les notes post constrast
                for y in pos:
                    Y = int(y*vheight/fvheight) #Pour en prendre en compte le changement de dimension sur la fenetre d'affichage
                    if(int(Rmax)>=int(I[Y][nimgG*pxpi+i][0])>=int(Rmin)):
                        if(int(Gmax)>=int(I[Y][nimgG*pxpi+i][1])>=int(Gmin)):
                            if(int(Bmax)>=int(I[Y][nimgG*pxpi+i][2])>=int(Bmin)):
                                X.append(1)
                            else:
                                X.append(0)
                        else:
                            X.append(0)
                    else:
                        X.append(0)
                Nt.append(X) 
        else:
            for i in range(moveG):
                I = M[cursorA11.get()+nimgG-1]
                X= [] #Colonne contenant les notes post constrast
                for y in pos:
                    Y = int(y*vheight/fvheight) #Pour en prendre en compte le changement de dimension sur la fenetre d'affichage
                    if(int(Rmax)<=int(I[Y][nimgG*pxpi+i][0])<=int(Rmin)):
                        if(int(Gmax)<=int(I[Y][nimgG*pxpi+i][1])<=int(Gmin)):
                            if(int(Bmax)<=int(I[Y][nimgG*pxpi+i][2])<=int(Bmin)):
                                X.append(1)
                            else:
                                X.append(0)
                        else:
                            X.append(0)
                    else:
                        X.append(0)
                Nt.append(X)
    
    #La conversion prennant en compte le contraste et l'inversion
    if(inverse_contrasted.get()): #Si les couleurs sont inclusive
        for i in range(cursorA11.get()+nimgG,cursorA12.get()+1):
            for dpx in range(pxpi):
                I = M[i] #image i de la vidéo
                X= [] #Colonne contenant les notes post constrast
                for y in pos:
                    Y = int(y*vheight/fvheight) #Pour en prendre en compte le changement de dimension sur la fenetre d'affichage
                    if(int(Rmax)>=int(I[Y][dpx][0])>=int(Rmin)):
                        if(int(Gmax)>=int(I[Y][dpx][1])>=int(Gmin)):
                            if(int(Bmax)>=int(I[Y][dpx][2])>=int(Bmin)):
                                X.append(1)
                            else:
                                X.append(0)
                        else:
                            X.append(0)
                    else:
                        X.append(0)
                Nt.append(X)           
    else: #Si les couleurs sont exclusives
        for i in range(cursorA11.get()+nimgG,cursorA12.get()+1):
            for dpx in range(pxpi):
                I = M[i] #image i de la vidéo
                X= [] #Colonne contenant les notes post constrast
                for y in pos:
                    Y = int(y*vheight/fvheight) #Pour en prendre en compte le changement de dimension sur la fenetre d'affichage
                    if(int(Rmax)<=int(I[Y][dpx][0])<=int(Rmin)):
                        if(int(Gmax)<=int(I[Y][dpx][1])<=int(Gmin)):
                            if(int(Bmax)<=int(I[Y][dpx][2])<=int(Bmin)):
                                X.append(1)
                            else:
                                X.append(0)
                        else:
                            X.append(0)
                    else:
                        X.append(0)
                Nt.append(X)
                
    #Lecture de la fin du fichier en prennant en compte l'offset  
    if(offsetDbutton):
        I = M[cursorA12.get()]
        if(inverse_contrasted.get()): #Si les couleurs sont inclusive
            for z in range(pxpi,offsetDvalue):
                X= [] #Colonne contenant les notes post constrast
                for y in pos:
                    Y = int(y*vheight/fvheight) #Pour en prendre en compte le changement de dimension sur la fenetre d'affichage
                    if(int(Rmax)<=int(I[Y][z][0])<=int(Rmin)):
                        if(int(Gmax)<=int(I[Y][z][1])<=int(Gmin)):
                            if(int(Bmax)<=int(I[Y][z][2])<=int(Bmin)):
                                X.append(1)
                            else:
                                X.append(0)
                        else:
                            X.append(0)
                    else:
                        X.append(0)
                Nt.append(X)
        else: #Si les couleurs sont exclusives
            for z in range(pxpi,offsetDvalue):
                X= [] #Colonne contenant les notes post constrast
                for y in pos:
                    Y = int(y*vheight/fvheight) #Pour en prendre en compte le changement de dimension sur la fenetre d'affichage
                    if(int(Rmax)<=int(I[Y][z][0])<=int(Rmin)):
                        if(int(Gmax)<=int(I[Y][z][1])<=int(Gmin)):
                            if(int(Bmax)<=int(I[Y][z][2])<=int(Bmin)):
                                 X.append(1)
                            else:
                                X.append(0)
                        else:
                            X.append(0)
                    else:
                        X.append(0)
                Nt.append(X)
            
    NoteTab_to_MidiFile()

def NoteTab_to_MidiFile():
    
    tracklist = [] #Indexation des pistes
        
    outfile = mido.MidiFile(type=1)
    
    #On créer chaques pistes qu'on ajoute au pattern
    for i in range(Nn):
        track = mido.MidiTrack()
        outfile.tracks.append(track)
        tracklist.append(track)
    
    global notes
    ticks_per_expr = 7
    
    for y in range(Nn): #On parcours les notes:
        delta = 0 #Temporalité du dernier changement
        for i in range(len(Nt)): #On parcours la liste de l'état des notes                       
            if(((Nt[i][y]) == 1) & ((Nt[i-1][y]) == 0)):#Si la note commence
                tracklist[y].append(mido.Message('note_off', note=notes[y], velocity=100, time=i*ticks_per_expr-delta)) #On écrit que la note précédente a fini et sa durée jusque ici
                delta = i*ticks_per_expr
            elif(((Nt[i][y]) == 0) & ((Nt[i-1][y]) == 1)):#Si la note se termine
                tracklist[y].append(mido.Message('note_on', note=notes[y], velocity=100, time=i*ticks_per_expr-delta)) #On écrit que la note  précédente à commencé et sa durée jusque ici
                delta = i*ticks_per_expr
        tracklist[y].append(mido.Message('note_off',note=notes[y], velocity=100,time = i*ticks_per_expr-delta))
        
    #On créer le fichier midi à la même adresse que le fichier mp4 chargé
    global r
    outfile.save(r+'.mid')
    print("The midi file have been created at : "+ r+'.mid')

#Permet de convertir un tableau numpy en une image
def Array_to_png(name,buf):
    imageio.imwrite(name, np.array(buf),format="JPEG-PIL")
    
def aff_image():
    global select_contrasted
    global N
    global M
    global aM
    global line
    global pos
    global lineoffsetD
    global lineoffsetG
    global linepxim1
    global linepxim2

    offsetGbutton = caseA13.get()
    offsetDbutton = caseA14.get()
    offsetGvalue = cursorA13.get()
    offsetDvalue = cursorA14.get()
    pxbetweentwoimagebutton = caseA15.get()
    pxim1 = cursorA161.get() #On récupère la position de la ligne vertical 1
    pxim2 = cursorA162.get() #On récupère la position de la ligne vertical 2
    
    if(len(M) != 0):
        aM = M[N]
        #Choix de l'affichage en mode normal ou contrasté
        if(not select_contrasted.get()):        
            Array_to_png("actual_image.jpg",aM)
        else:
            Array_to_png("actual_image.jpg",MatrixImageToMatrixContrastedImage())
        img = Image.open("actual_image.jpg")
        img = img.resize((fvwidth, fvheight), Image.ANTIALIAS)
        img = ImageTk.PhotoImage(img)
        viewer.itemconfig(image_visualisation,image=img)
        viewer.imgref = img
        
        #Permet de créer ou détruite la ligne de l'offset à gauche de la première du canva
        if(lineoffsetG != None):
            viewer.delete(lineoffsetG)
        if(cursorA11.get()==N):
            if(offsetGbutton == 1):
                lineoffsetG = viewer.create_line(offsetGvalue,0,offsetGvalue,fvheight,fill="green",width=2)
            else:
                viewer.delete(lineoffsetG)
        
        #Permet de créer ou détruite la ligne de l'offset à droite de la première du canva
        if(lineoffsetD != None):
            viewer.delete(lineoffsetD)
        if(cursorA12.get()==N):
            if(offsetDbutton == 1):
                lineoffsetD = viewer.create_line(offsetDvalue,0,offsetDvalue,fvheight,fill="green",width=2)
            else:
                viewer.delete(lineoffsetD)

        #Affichage ou non du premier et du deuxième pointeur permettant de mesurer le nombre de pixel défilent entre chaques images                
        if(linepxim1 != None):
            viewer.delete(linepxim1)
        if(linepxim2 != None):
            viewer.delete(linepxim2)
        if(pxbetweentwoimagebutton == 1):
            linepxim1 = viewer.create_line(pxim1,0,pxim1,fvheight,fill="blue",width=2)
            linepxim2 = viewer.create_line(pxim2,0,pxim2,fvheight,fill="blue",width=2)
        else:
            viewer.delete(linepxim1)
            viewer.delete(linepxim2)
        
        #Affichage des curseurs
        if(case_cursor.get() == 1): #On affiche tout les curseurs
        
            pos = []
            for i in line: #On supprime tout les curseurs
                viewer.delete(i)
            line = []
            
            global Nn
            Fp = cursorA22.get() #On récupère la position de la première note
            Lp = cursorA23.get() #On récupère la position de la dernière note
            step = (Lp-Fp)/Nn
            H = step/2 + Fp    
            
            for i in range(Nn): 
                pos.append(H)
                line.append(viewer.create_line(0,H,fwidth,H,fill="red",width=1)) # Dessine une ligne
                H = H + step
        else:
            for i in line: #On supprime tout les curseurs
                viewer.delete(i)
            line = []
            
#Partie sélection du fichier mp4 via l'interface graphique     
def select_file():
    filetypes = (('mp4 files', '*.mp4'),('All files', '*.*'))
    filename = fd.askopenfilename(title='Open a file',initialdir='/',filetypes=filetypes)   
    
    global r
    
    r,ext = os.path.splitext(filename)
    
    if(ext == ".mp4"):
        print(filename)
        MP4toMatrixVideo(filename)
        
def save_global_config():
    global Save_file_name
    global cursorA11
    global cursorA12
    global cursorA13
    global cursorA14
    global caseA13
    global caseA14
    global caseA15
    global cursorA161
    global cursorA162
    global text_choose_notes
    global case_cursor
    global cursorA22
    global cursorA23
    global select_contrasted
    global inverse_contrasted
    global cursorA311
    global cursorA312
    global cursorA321
    global cursorA322
    global cursorA331
    global cursorA332
    fichier = open(ProgDir+"\\save_global\\"+Save_file_name.get()+".globalmp4tomidi", "w")
    fichier.write(Save_file_name.get()+"\n")
    fichier.write(str(cursorA11.get())+"\n")
    fichier.write(str(cursorA12.get())+"\n")
    fichier.write(str(cursorA13.get())+"\n")
    fichier.write(str(cursorA14.get())+"\n")
    fichier.write(str(caseA13.get())+"\n")
    fichier.write(str(caseA14.get())+"\n")
    fichier.write(str(caseA15.get())+"\n")
    fichier.write(str(cursorA161.get())+"\n")
    fichier.write(str(cursorA162.get())+"\n")
    fichier.write(text_choose_notes.get()+"\n")
    fichier.write(str(case_cursor.get())+"\n")
    fichier.write(str(cursorA22.get())+"\n")
    fichier.write(str(cursorA23.get())+"\n")
    fichier.write(str(select_contrasted.get())+"\n")
    fichier.write(str(inverse_contrasted.get())+"\n")
    fichier.write(str(cursorA311.get())+"\n")
    fichier.write(str(cursorA312.get())+"\n")
    fichier.write(str(cursorA321.get())+"\n")
    fichier.write(str(cursorA322.get())+"\n")
    fichier.write(str(cursorA331.get())+"\n")
    fichier.write(str(cursorA332.get())+"\n")
    fichier.close()
    print("global file " + Save_file_name.get() + " successfully saved in :")
    print(ProgDir+"\\save_global\\"+Save_file_name.get()+".globalmp4tomidi")
    global liste_config_general
    liste_config_general = []
    liste_config_general.append("None")
    extend_list_global()
    global opt2
    opt2.destroy()
    opt2 = tk.OptionMenu(ZoneChoose, text_choose_general, *liste_config_general,command = select_global_setup)
    opt2.pack(side="right")
    Save_file_name.set("")
    
def select_global_setup(x):
    global text_choose_general
    global cursorA11
    global cursorA12
    global cursorA13
    global cursorA14
    global caseA13
    global caseA14
    global caseA15
    global cursorA161
    global cursorA162
    global text_choose_notes
    global case_cursor
    global cursorA22
    global cursorA23
    global select_contrasted
    global inverse_contrasted
    global cursorA311
    global cursorA312
    global cursorA321
    global cursorA322
    global cursorA331
    global cursorA332
    if(text_choose_general.get() == "None"):
        return 0
    else:
        print("loading global file : "+text_choose_general.get()+"...")
        fichier = open(ProgDir+"\\save_global\\"+text_choose_general.get()+".globalmp4tomidi", "r")
        fichier.readline()
        cursorA11.set(int(fichier.readline()[:-1]))
        cursorA12.set(int(fichier.readline()[:-1]))
        cursorA13.set(int(fichier.readline()[:-1]))
        cursorA14.set(int(fichier.readline()[:-1]))
        caseA13.set(int(fichier.readline()[:-1]))
        caseA14.set(int(fichier.readline()[:-1]))
        caseA15.set(int(fichier.readline()[:-1]))
        cursorA161.set(int(fichier.readline()[:-1]))
        cursorA162.set(int(fichier.readline()[:-1]))
        text_choose_notes.set(fichier.readline()[:-1])
        case_cursor.set(int(fichier.readline()[:-1]))
        cursorA22.set(int(fichier.readline()[:-1]))
        cursorA23.set(int(fichier.readline()[:-1]))
        select_contrasted.set(int(fichier.readline()[:-1]))
        inverse_contrasted.set(int(fichier.readline()[:-1]))
        cursorA311.set(int(fichier.readline()[:-1]))
        cursorA312.set(int(fichier.readline()[:-1]))
        cursorA321.set(int(fichier.readline()[:-1]))
        cursorA322.set(int(fichier.readline()[:-1]))
        cursorA331.set(int(fichier.readline()[:-1]))
        cursorA332.set(int(fichier.readline()[:-1]))
        select_notes_setup(0)
        print("global file successfully loaded")
    aff_image()
        
def select_notes_setup(x):
    global text_choose_notes
    global Nn
    global notes
    if(text_choose_notes.get() == "None"):
        return 0
    else:
        print("loading note file : "+text_choose_notes.get()+"...")
        fichier = open(ProgDir+"\\save_note\\"+text_choose_notes.get()+".notesmp4tomidi", "r")
        Nn = int(fichier.readline())
        #print(Nn)
        notes = []
        for y in range(Nn):
            notes.append(int(fichier.readline()))
        #print(notes)
        print("note file successfully loaded")   
    aff_image()
        
def extend_list_notes():
    global liste_config_notes
    liste_config_notes.append("None")
    for filename in os.listdir(ProgDir+"\\save_note"):
        filenamesplitted = filename.split(".")
        if((len(filenamesplitted) == 2) & (filenamesplitted[1] == "notesmp4tomidi")):
            liste_config_notes.append(filenamesplitted[0])


def extend_list_global():
    global liste_config_general
    liste_config_general.append("None")
    for filename in os.listdir(ProgDir+"\\save_global"):
        filenamesplitted = filename.split(".")
        if((len(filenamesplitted) == 2) & (filenamesplitted[1] == "globalmp4tomidi")):
            liste_config_general.append(filenamesplitted[0])

def cursor_change1():
    global N
    N = cursorA11.get()
    sliderval.set(N)
    aff_image()
    
def cursor_change2():
    global N
    N = cursorA12.get()
    sliderval.set(N)
    aff_image()
    
def slider_change(val):
    global N
    N = sliderval.get()
    aff_image()
    
def motion(event):
    x, y = event.x, event.y
    R = 0
    G = 0
    B = 0
    global aM
    global vwidth
    global vheight
    global fvwidth
    global fvheight
    
    if(len(aM) != 0): #On vérifie si le tableau contient des données
        coeffy = vheight/fvheight
        coeffx = vwidth/fvwidth
        ry=int(y*coeffy)
        rx=int(x*coeffx)
        if((0<y<fvheight)&(0<x<fvwidth)):
            R = aM[ry][rx][0]
            G = aM[ry][rx][1]
            B = aM[ry][rx][2]
    
    global text_coord
    text_coord.set("X = "+ str(x) +"| Y = "+ str(y) +"| R = "+ str(R) +"| G = "+ str(G) +"| B = "+ str(B) +"")
   
def aff_error(event):
    print("error")

def Enterevent(event):
    aff_image()
    
#-------------------------
#Définition de la fenetre principale
#-------------------------

root = tk.Tk()#création de la fenêtre
root.title("MP4 to MIDI file")#définition du titre de la fenêtre
root.resizable(False, False)
root.geometry(str(fwidth)+"x"+str(fheight))#définition de la taille de la fenêtre 
root.minsize(fwidth,fheight)#définition de la taille minimale de la fenêtre   
root.maxsize(fwidth,fheight)#définition de la taille maximale de la fenêtre 
root.iconbitmap("ico.ico")#définition de l'icone
  
root.bind('<Return>', Enterevent)

#-------------------------
#Fenetre des paramètres
#-------------------------
    
   #--------------
   #Définition de la fenètre des paramètres
   #--------------
        
ZoneA = tk.LabelFrame(root, text="Setup", padx=1, pady=1)
ZoneA.pack(fill="both", expand="yes",side="left")
   
#Définition du bouton pour ouvrir le fichier mp4
open_button_open = ttk.Button(ZoneA,text='Open mp4 file',command=select_file)
open_button_open.pack(side="top",padx=1, pady=1)
    
   #--------------
   #Frame du selection de la première et dernière image
   #--------------

ZoneA1 = tk.LabelFrame(ZoneA, text="File definition")
ZoneA1.pack(padx=1, pady=1,fill = "x") 
    
#Définition de la zone 1
ZoneA11 = tk.Frame(ZoneA1)
ZoneA11.pack(padx=0, pady=0,fill = "x")
#Texte du selectionneur
label = tk.Label(ZoneA11, text="First image : ")
label.pack(side="left")
#Selectionneur
cursorA11 = tk.IntVar()    
sA11 = tk.Spinbox(ZoneA11, from_=0, to=0,textvariable=cursorA11, command=cursor_change1)
sA11.pack(side="right")
  
ZoneA13 = tk.Frame(ZoneA1)
ZoneA13.pack(padx=0, pady=0,fill = "x") 
#Case cochable
caseA13 = tk.IntVar()
C13 = tk.Checkbutton(ZoneA13, variable = caseA13, onvalue = 1, offvalue = 0,command = aff_image)
C13.pack(side="left")
#Texte du selectionneur
label = tk.Label(ZoneA13, text="Left offset :")
label.pack(side="left")
#Selectionneur
cursorA13 = tk.IntVar()    
sA13 = tk.Spinbox(ZoneA13, from_=0, to=fvwidth,textvariable=cursorA13, command=aff_image)
sA13.pack(side="right")
  
#Définition de la zone 2
ZoneA12 = tk.Frame(ZoneA1)
ZoneA12.pack(padx=0, pady=0,fill = "x")   
#Texte du selectionneur
label = tk.Label(ZoneA12, text="Last image : ")
label.pack(side="left")
#Selectionneur
cursorA12 = tk.IntVar()
sA12 = tk.Spinbox(ZoneA12, from_=0, to=0,textvariable=cursorA12, command=cursor_change2)
sA12.pack(side="right")  

ZoneA14 = tk.Frame(ZoneA1)
ZoneA14.pack(padx=0, pady=0,fill = "x") 
#Case cochable
caseA14 = tk.IntVar()
C14 = tk.Checkbutton(ZoneA14, variable = caseA14, onvalue = 1, offvalue = 0,command = aff_image)
C14.pack(side="left")
#Texte du selectionneur
label = tk.Label(ZoneA14, text="Right offset :")
label.pack(side="left")
#Selectionneur
cursorA14 = tk.IntVar()
cursorA14.set(fvwidth)
sA14 = tk.Spinbox(ZoneA14, from_=0, to=fvwidth,textvariable=cursorA14, command=aff_image)
sA14.pack(side="right")

ZoneA15 = tk.Frame(ZoneA1)
ZoneA15.pack(padx=0, pady=0,fill = "x") 
#Texte du selectionneur
label = tk.Label(ZoneA15, text="Number of pixels between two images")
label.pack(side="left")
#Case cochable
caseA15 = tk.IntVar()
C15 = tk.Checkbutton(ZoneA15, variable = caseA15, onvalue = 1, offvalue = 0,command = aff_image)
C15.pack(side="right")

ZoneA16 = tk.Frame(ZoneA1)
ZoneA16.pack(padx=0, pady=0,fill = "x") 

#Texte du selectionneur
label = tk.Label(ZoneA16, text="Position on 1 : ")
label.pack(side="left")
#Selectionneur
cursorA161 = tk.IntVar()
sA161 = tk.Spinbox(ZoneA16, from_=0, to=fvwidth, width = 8,textvariable=cursorA161, command=aff_image)
sA161.pack(side="left")
#Texte du selectionneur
label = tk.Label(ZoneA16, text=" 2 :")
label.pack(side="left")
#Selectionneur
cursorA162 = tk.IntVar()
sA162 = tk.Spinbox(ZoneA16, from_=0, to=fvwidth, width = 8,textvariable=cursorA162, command=aff_image)
sA162.pack(side="right")
    
   #--------------
   #Frame de positionnement du premier et dernier curseur
   #--------------    

#Définition de la zone 2
ZoneA2 = tk.LabelFrame(ZoneA, text="Positioning cursors")
ZoneA2.pack(padx=1, pady=1,fill = "x")

ZoneA21 = tk.Frame(ZoneA2)
ZoneA21.pack(padx=0, pady=0)  
#Texte du selectionneur
label = tk.Label(ZoneA21, text="Notes setup : ")
label.pack(side="left")
#Selectionneur
extend_list_notes()
text_choose_notes = tk.StringVar(ZoneA21)
text_choose_notes.set(liste_config_notes[0])
opt1 = tk.OptionMenu(ZoneA21, text_choose_notes, *liste_config_notes,command=select_notes_setup)
opt1.pack(side="right")

#Case cochable
case_cursor = tk.IntVar()
C = tk.Checkbutton(ZoneA2 ,text = "Show notes cursors", variable = case_cursor, onvalue = 1, offvalue = 0,command = aff_image)
C.pack()

ZoneA22 = tk.Frame(ZoneA2)
ZoneA22.pack(padx=0, pady=0,fill = "x")   
#Texte du selectionneur
label = tk.Label(ZoneA22, text="First cursor : ")
label.pack(side="left")
#Selectionneur
cursorA22 = tk.IntVar()
cursorA22.set(0)
sA22 = tk.Spinbox(ZoneA22, from_=0, to=500,textvariable=cursorA22, command=aff_image)
sA22.pack(side="right") 

ZoneA23 = tk.Frame(ZoneA2)
ZoneA23.pack(padx=0, pady=0,fill = "x")   
#Texte du selectionneur
label = tk.Label(ZoneA23, text="Last cursor : ")
label.pack(side="left")
#Selectionneur
cursorA23 = tk.IntVar()
cursorA23.set(500)
sA23 = tk.Spinbox(ZoneA23, from_=0, to=500,textvariable=cursorA23, command=aff_image)
sA23.pack(side="right")      

   #--------------
   #Frame de sélection du contraste
   #--------------

#Définition de la zone 3
ZoneA3 = tk.LabelFrame(ZoneA, text="Contrast definition")
ZoneA3.pack(padx=3, pady=3,fill = "x")

ZoneA30 = tk.Frame(ZoneA3)
ZoneA30.pack()

select_contrasted = tk.IntVar()
C1 = tk.Checkbutton(ZoneA30 ,text = "Show contrast", variable = select_contrasted, onvalue = 1, offvalue = 0,command = aff_image)
C1.pack(side="left")

inverse_contrasted = tk.IntVar()
C2 = tk.Checkbutton(ZoneA30 ,text = "Inverse", variable = inverse_contrasted, onvalue = 1, offvalue = 0,command = aff_image)
C2.pack(side="right")

ZoneA311 = tk.Frame(ZoneA3)
ZoneA311.pack(padx=1, pady=1,fill = "x")   
label = tk.Label(ZoneA311, text="Red min (0 à 255)")
label.pack(side="left")
#Selectionneur
cursorA311 = tk.IntVar()
sA311 = tk.Spinbox(ZoneA311, from_=0, to=255,textvariable=cursorA311, command=MatrixImageToMatrixContrastedImage)
sA311.pack(side="right")   

ZoneA312 = tk.Frame(ZoneA3)
ZoneA312.pack(padx=0, pady=0,fill = "x")   
label = tk.Label(ZoneA312, text="Red max (0 à 255)")
label.pack(side="left")
#Selectionneur
cursorA312 = tk.IntVar()
cursorA312.set(255)
sA312 = tk.Spinbox(ZoneA312, from_=0, to=255,textvariable=cursorA312, command=MatrixImageToMatrixContrastedImage)
sA312.pack(side="right")   

ZoneA321 = tk.Frame(ZoneA3)
ZoneA321.pack(padx=1, pady=1,fill = "x")   
label = tk.Label(ZoneA321, text="Green min (0 à 255)")
label.pack(side="left")
#Selectionneur
cursorA321 = tk.IntVar()
sA321 = tk.Spinbox(ZoneA321, from_=0, to=255,textvariable=cursorA321, command=MatrixImageToMatrixContrastedImage)
sA321.pack(side="right")  

ZoneA322 = tk.Frame(ZoneA3)
ZoneA322.pack(padx=0, pady=0,fill = "x")   
label = tk.Label(ZoneA322, text="Green max (0 à 255)")
label.pack(side="left")
#Selectionneur
cursorA322 = tk.IntVar()
cursorA322.set(255)
sA322 = tk.Spinbox(ZoneA322, from_=0, to=255,textvariable=cursorA322, command=MatrixImageToMatrixContrastedImage)
sA322.pack(side="right")

ZoneA331 = tk.Frame(ZoneA3)
ZoneA331.pack(padx=1, pady=1,fill = "x")   
label = tk.Label(ZoneA331, text="Blue min (0 à 255)")
label.pack(side="left")
#Selectionneur
cursorA331 = tk.IntVar()
sA331 = tk.Spinbox(ZoneA331, from_=0, to=255,textvariable=cursorA331, command=MatrixImageToMatrixContrastedImage)
sA331.pack(side="right")

ZoneA332 = tk.Frame(ZoneA3)
ZoneA332.pack(padx=0, pady=0,fill = "x")   
label = tk.Label(ZoneA332, text="Blue max (0 à 255)")
label.pack(side="left")
#Selectionneur
cursorA332 = tk.IntVar()
cursorA332.set(255)
sA332 = tk.Spinbox(ZoneA332, from_=0, to=255,textvariable=cursorA332, command=MatrixImageToMatrixContrastedImage)
sA332.pack(side="right")

ZoneSave = tk.Frame(ZoneA)
ZoneSave.pack(padx=1, pady=1) 
save_button = ttk.Button(ZoneSave,text='Save config',command=save_global_config)
save_button.pack(side="right",padx=3, pady=1)
Save_file_name = tk.StringVar()
Save_file = tk.Entry(ZoneSave,textvariable=Save_file_name)
Save_file.pack(side="right",padx=3)
label = tk.Label(ZoneSave,text = "Name :")
label.pack(side="right")

ZoneChoose = tk.Frame(ZoneA)
ZoneChoose.pack(padx=0, pady=0)  
#Texte du selectionneur
label = tk.Label(ZoneChoose, text="General Setup :")
label.pack(side="left")
#Selectionneur
extend_list_global()
text_choose_general = tk.StringVar(ZoneChoose)
text_choose_general.set(liste_config_general[0])
opt2 = tk.OptionMenu(ZoneChoose, text_choose_general, *liste_config_general,command=select_global_setup)
opt2.pack(side="right")

 
#Définition du bouton pour ouvrir le fichier mp4
convert_button = ttk.Button(ZoneA,text='Convert into MIDI',command=MatrixContrasted_to_NoteTab)
convert_button.pack(side="bottom",padx=1, pady=1)
   
#-------------------------
#Fenetre de visualisation
#-------------------------

ZoneB = tk.LabelFrame(root, text="Visualisation", padx=10, pady=10)
ZoneB.pack(fill="both", expand="yes",side="left")

   #--------------
   #Zone d'affichage
   #--------------

viewer = tk.Canvas(ZoneB, width=900, height=500, background='#E0E0E0')    

start_screen = Image.open('start_screen.jpg')
start_screen = start_screen.resize((fvwidth, fvheight), Image.ANTIALIAS)
start_screen = ImageTk.PhotoImage(start_screen)

image_visualisation= viewer.create_image(0,0,anchor ="nw", image=start_screen)

viewer.pack() 

   #--------------
   #Affichage des coordonnées et de la couleur du canva associée
   #--------------

text_coord = tk.StringVar()
text_coord.set("X = ? | Y = ? | R = ? | G = ? | B = ?")
coordonnees = tk.Label(ZoneB, textvariable=text_coord)
coordonnees.pack()

   #--------------+
   #Choix de l'image à afficher
   #--------------
   
sliderval = tk.IntVar()  
slider = tk.Scale(ZoneB, from_=0, to=0, length=900, variable=sliderval, orient='horizontal',command=slider_change)
slider.pack(side="bottom")

#-------------------------
#Récupérer position du curseur de la souris sur le canva
#-------------------------

viewer.bind('<Motion>', motion)

#-------------------------
#Lancement de la l'interface
#-------------------------
    
root.mainloop()
