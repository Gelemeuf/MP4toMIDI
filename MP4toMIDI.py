"""
# SPDX-License-Identifier: GPL-3.0-or-later

# By Thomas LEFRANC

# A program python to transform a video of a barrel organ into a MIDI file
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
import random

"""
A ajouter:
    -choix du nombre de colonnes de défilement entre deux images (augmentation de l'échantillonage)
    -sauvegarde notes d'un intrument
    -sauvegarde paramètre généraux
    -choix de la position de l'enregistrement
    -ajout sélection décalage début vidéo (si le fichier commence par directement à droite)
    -ajout sélection décalage fin de vidéo (si le fichier ne finit pas complétement à gauche)
    -choix à deux curseurs de l'exclusion pour le contraste
"""

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

Nt = [] #Fichier de l'état des notes
fps = 0

r = "" #Chemin du fichier vidéo initial afin de mettre le fichier midi final au même endroit

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
    print("Conversion ...")
    
    M = np.empty((frameCount, frameHeight, frameWidth, 3), np.dtype('uint8'))  
    fc = 0
    ret = True
    while (fc < frameCount and ret):
        ret, M[fc] = cap.read()
        fc += 1
        
    cap.release()
    
    print("Conversion de la video en matrice terminée")
    
    cursorA11.set(1)
    cursorA12.set(frameCount-1)
    sA11.config(to=frameCount-2)
    sA12.config(to=frameCount-1)
    
    return MatrixModif(M)

#Permet de modifier la matrice en inversant les lignes et les couleurs pour corriger l'erreur lors de la création
def MatrixModif(Mv):
    global M  
    Mm = Mv   
    M = Mm
    
    global N
    N = 1
    aff_image()    
    
    return Mm

#Permet de convertir une image RGB en une image noir et blanc contraster
def MatrixImageToMatrixContrastedImage():
    global aM
    Mc = []
    R = cursorA31.get()
    G = cursorA32.get()
    B = cursorA33.get()
    for i in aM:
        COL = []
        for y in i:
            if(int(y[0])>int(R)):
                if(int(y[1])>int(G)):
                    if(int(y[2])>int(B)):
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
    global Nt
    Nt = []
    global pos
    global M
    R = cursorA31.get()
    G = cursorA32.get()
    B = cursorA33.get()
    for i in range(cursorA11.get(),cursorA12.get()+1):
        I = M[i]
        X= []
        for y in pos:
            Y = int(y*vheight/fvheight) #Pour en prendre en compte le changement de dimension sur la fenetre d'affichage
            if(int(I[Y][0][0])>int(R)):
                if(int(I[Y][0][1])>int(G)):
                    if(int(I[Y][0][2])>int(B)):
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
    global Nt
    
    l = len(Nt[0]) #Nombre de pistes
    tracklist = [] #Indexation des pistes
    
    outfile = mido.MidiFile(type=1)
    
    #On créer chaques pistes qu'on ajoute au pattern
    for i in range(l):
        track = mido.MidiTrack()
        outfile.tracks.append(track)
        tracklist.append(track)
    
    # Pour un orgue de 29 les notes sont : Do2 - Ré2 - Fa2 - Sol2 - La2 - Do3 - 
    #Ré3 - Mi3 - Fa3 - Fa#3 - Sol3 - Sol#3 - La3 - La#3 - Si3 - Do4 - Do#4 -
    #Ré4 - Ré#4 - Mi4 - Fa4 - Fa#4 - Sol4 - Sol#4 - La4 - La#4 - Si4 - Do5 - Ré5.
    
    # Les fréquences correspondantes sont : 48, 50, 53, 55 ,57, 60, 62, 64, 65, 66, 
    # 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 86
    
    notes = [48, 50, 53, 55 ,57, 60, 62, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 86]
    ticks_per_expr = 50
    
    for y in range(l): #On parcours les notes:
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
    print("Le fichier midi a été crée : "+ r+'.mid')

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
        
        #Affichage des curseurs
        if(curseur.get() == 1): #On affiche tout les curseurs
        
            pos = []
            for i in line: #On supprime tout les curseurs
                viewer.delete(i)
            line = []
            
            Nn = cursorA21.get() #On récupère le nombre de notes
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
 
def cursor_change1():
    global N
    N = cursorA11.get()
    global M
    aff_image()
    
def cursor_change2():
    global N
    N = cursorA12.get()
    global M
    aff_image()
    
def print_note_cursor():
    return 0    
    
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

#-------------------------
#Fenetre des paramètres
#-------------------------
    
   #--------------
   #Définition de la fenètre des paramètres
   #--------------
        
ZoneA = tk.LabelFrame(root, text="Configuration", padx=3, pady=3)
ZoneA.pack(fill="both", expand="yes",side="left")
     
#Définition du bouton pour ouvrir le fichier mp4
open_button = ttk.Button(ZoneA,text='Ouvrir un fichier mp4',command=select_file)
open_button.pack(expand=False,padx=3, pady=3)
    
   #--------------
   #Frame du selection de la première et dernière image
   #--------------

ZoneA1 = tk.LabelFrame(ZoneA, text="Définition du fichier")
ZoneA1.pack(padx=3, pady=3) 
    
#Définition de la zone 1
ZoneA11 = tk.Frame(ZoneA1)
ZoneA11.pack(padx=3, pady=3)
#Texte du selectionneur
label = tk.Label(ZoneA11, text="Première image")
label.pack(side="left")
#Selectionneur
cursorA11 = tk.IntVar()    
sA11 = tk.Spinbox(ZoneA11, from_=0, to=0,textvariable=cursorA11, command=cursor_change1)
sA11.pack(side="right")
    
#Définition de la zone 2
ZoneA12 = tk.Frame(ZoneA1)
ZoneA12.pack(padx=3, pady=3)   
#Texte du selectionneur
label = tk.Label(ZoneA12, text="Dernière image")
label.pack(side="left")
#Selectionneur
cursorA12 = tk.IntVar()
sA12 = tk.Spinbox(ZoneA12, from_=0, to=0,textvariable=cursorA12, command=cursor_change2)
sA12.pack(side="right")  
    
   #--------------
   #Frame de positionnement du premier et dernier curseur
   #--------------    

#Définition de la zone 2
ZoneA2 = tk.LabelFrame(ZoneA, text="Positionnement curseurs")
ZoneA2.pack(padx=3, pady=3)

ZoneA21 = tk.Frame(ZoneA2)
ZoneA21.pack(padx=3, pady=3)   
#Texte du selectionneur
label = tk.Label(ZoneA21, text="Nombre de notes")
label.pack(side="left")
#Selectionneur
cursorA21 = tk.IntVar()
cursorA21.set(29)
sA21 = tk.Spinbox(ZoneA21, from_=0, to=100,textvariable=cursorA21, command=print_note_cursor)
sA21.pack(side="right") 

curseur = tk.IntVar()
C = tk.Checkbutton(ZoneA2 ,text = "Afficher les curseurs", variable = curseur, onvalue = 1, offvalue = 0)
C.pack()

ZoneA22 = tk.Frame(ZoneA2)
ZoneA22.pack(padx=3, pady=3)   
#Texte du selectionneur
label = tk.Label(ZoneA22, text="Premier curseur")
label.pack(side="left")
#Selectionneur
cursorA22 = tk.IntVar()
cursorA22.set(0)
sA22 = tk.Spinbox(ZoneA22, from_=0, to=500,textvariable=cursorA22, command=print_note_cursor)
sA22.pack(side="right") 

ZoneA23 = tk.Frame(ZoneA2)
ZoneA23.pack(padx=3, pady=3)   
#Texte du selectionneur
label = tk.Label(ZoneA23, text="Dernier curseur")
label.pack(side="left")
#Selectionneur
cursorA23 = tk.IntVar()
cursorA23.set(500)
sA23 = tk.Spinbox(ZoneA23, from_=0, to=500,textvariable=cursorA23, command=print_note_cursor)
sA23.pack(side="right")      

   #--------------
   #Frame de sélection du contraste
   #--------------

#Définition de la zone 3
ZoneA3 = tk.LabelFrame(ZoneA, text="Définition du contraste")
ZoneA3.pack(padx=3, pady=3)

select_contrasted = tk.IntVar()
C = tk.Checkbutton(ZoneA3 ,text = "Afficher le contraste", variable = select_contrasted, onvalue = 1, offvalue = 0)
C.pack()

ZoneA31 = tk.Frame(ZoneA3)
ZoneA31.pack(padx=3, pady=3)   
label = tk.Label(ZoneA31, text="Rouge (0 à 255)")
label.pack(side="left")
#Selectionneur
cursorA31 = tk.IntVar()
sA31 = tk.Spinbox(ZoneA31, from_=0, to=255,textvariable=cursorA31, command=MatrixImageToMatrixContrastedImage)
sA31.pack(side="right")   

ZoneA32 = tk.Frame(ZoneA3)
ZoneA32.pack(padx=3, pady=3)   
label = tk.Label(ZoneA32, text="Vert (0 à 255)")
label.pack(side="left")
#Selectionneur
cursorA32 = tk.IntVar()
sA32 = tk.Spinbox(ZoneA32, from_=0, to=255,textvariable=cursorA32, command=MatrixImageToMatrixContrastedImage)
sA32.pack(side="right")  

ZoneA33 = tk.Frame(ZoneA3)
ZoneA33.pack(padx=3, pady=3)   
label = tk.Label(ZoneA33, text="Bleu (0 à 255)")
label.pack(side="left")
#Selectionneur
cursorA33 = tk.IntVar()
sA33 = tk.Spinbox(ZoneA33, from_=0, to=255,textvariable=cursorA33, command=MatrixImageToMatrixContrastedImage)
sA33.pack(side="right")

#Définition du bouton pour ouvrir le fichier mp4
applique_button = ttk.Button(ZoneA,text='Appliquer',command=aff_image)
applique_button.pack(padx=3, pady=3)  

#Définition du bouton pour ouvrir le fichier mp4
convert_button = ttk.Button(ZoneA,text='Convertir en fichier MIDI',command=MatrixContrasted_to_NoteTab)
convert_button.pack(side="bottom",padx=10, pady=20)
    
#-------------------------
#Fenetre de visualisation
#-------------------------

ZoneB = tk.LabelFrame(root, text="Visualisation", padx=30, pady=30)
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
#-------------------------
#Lancement de la l'interface
#-------------------------
    
root.mainloop()
