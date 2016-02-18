#!/usr/bin/python
from Tkinter import *
from tkFileDialog import *
import platform
import glob
import sys
import os

# =================== constants ===================

INPUT_DIR = sys.argv[1]
if len(sys.argv) > 2: INPUT_EXT = sys.argv[2]
else: INPUT_EXT = 'txt'

INPUT_FILE  = None
OUTPUT_FILE = None

VERSION = 'Tabernacle 1.0'
CONTROL = 'Control'

if platform.system() == 'Darwin':
    CONTROL = 'Command'

ROOT = Tk()

# =================== text area ===================

TEXT_AREA = Text(ROOT, width=120, height=55)
TEXT_AREA.bind('<1>', lambda event: TEXT_AREA.focus_set())
TEXT_AREA.pack()

# =================== file list ===================

def selectList(event):
    index = FILE_LIST.curselection()[0]
    selectFile(index)

def selectFile(index):
    global ROOT, INPUT_FILE, OUTPUT_FILE, TEXT_AREA, ANN_DICT, ANN_TAG_ID
    fileSave()

    # title
    INPUT_FILE = os.path.join(INPUT_DIR, FILE_LIST.get(index))
    ROOT.title(INPUT_FILE)

    # text
    fin = open(INPUT_FILE)
    TEXT_AREA.config(state=NORMAL)
    TEXT_AREA.delete(1.0, END)
    TEXT_AREA.insert(END, fin.read())
    TEXT_AREA.config(state=DISABLED)
    fin.close()

    # annotation
    OUTPUT_FILE = INPUT_FILE+'.map'
    ANN_DICT = dict()
    ANN_TAG_ID = 0
    if not os.path.isfile(OUTPUT_FILE): return

    fin = open(OUTPUT_FILE)
    for line in fin:
        l = line.split()
        addTag(l[1], l[2], int(l[0]))
    fin.close()

FILE_LIST = Listbox(ROOT, width=12, height=49)
FILE_LIST.bind('<<ListboxSelect>>', selectList)
FILE_LIST.pack()

for filename in sorted(glob.glob(os.path.join(INPUT_DIR, '*.'+INPUT_EXT))):
    FILE_LIST.insert(END, os.path.basename(filename))

# =================== annotation ===================

class Tag:
    def __init__(self, desc, color, func):
        self.desc  = desc
        self.color = color
        self.func  = func

def annotateAdd(event, id):
    (start, end) = getSpan()
    addTag(start, end, id)

def annotateDelete(event):
    (start, end) = getSpan()
    deleteTag(start, end)

def addTag(start, end, id):
    global ANN_DICT, ANN_TAGS, ANN_TAG_ID, TEXT_AREA
    TEXT_AREA.config(state=NORMAL)
    deleteTag(start, end)

    key = (start, end)
    tag = str(ANN_TAG_ID)
    ANN_DICT[key] = (id, tag)
    ANN_TAG_ID += 1

    TEXT_AREA.tag_add(tag, start, end)
    TEXT_AREA.tag_config(tag, background=ANN_TAGS[id].color, foreground='black')
    TEXT_AREA.config(state=DISABLED)

def deleteTag(start, end):
    global ANN_DICT, TEXT_AREA
    key = (start, end)

    if key in ANN_DICT:
        tag = ANN_DICT[key][1]
        del ANN_DICT[key]
        TEXT_AREA.tag_delete(tag)
        return True

    return False

def getSpan():
    global TEXT_AREA
    start = TEXT_AREA.index(SEL_FIRST)
    end   = TEXT_AREA.index(SEL_LAST)
    text  = TEXT_AREA.selection_get()

    start = adjustSpan(start, len(text) - len(text.lstrip()))
    end   = adjustSpan(end  , len(text.rstrip()) - len(text))
    return (start, end)

def adjustSpan(index, margin):
    if margin == 0: return index
    t = index.split('.')
    t[1] = str(int(t[1]) + margin)
    return '.'.join(t)

def annotate0(event=None): annotateAdd(event, 0)
def annotate1(event=None): annotateAdd(event, 1)
def annotate2(event=None): annotateAdd(event, 2)
def annotate3(event=None): annotateAdd(event, 3)
def annotate4(event=None): annotateAdd(event, 4)

ANN_TAGS = [Tag('Name'                 , '#FFFF00', annotate0), # yellow
            Tag('Date'                 , '#FFA070', annotate1), # light-salmon
            Tag('Time'                 , '#FFB8C0', annotate2), # light-pick
            Tag('Accession Number'     , '#90F090', annotate3), # light-green
            Tag('Medical Record Number', '#C0B860', annotate4)] # dark-khaki

ANN_DICT = None
ANN_TAG_ID = 0

# =================== file handlers ===================

def fileSave(event=None):
    global ANN_DICT
    if not OUTPUT_FILE or not ANN_DICT: return
    fout = open(OUTPUT_FILE,'w')

    for key in ANN_DICT:
        id = ANN_DICT[key][0]
        s = '%d %s %s\n' % (id, key[0], key[1])
        fout.write(s)

    fout.close()

def fileQuit(event=None):
    fileSave()
    ROOT.quit

# =================== menu ===================

def popupMenu(event):
    popupmenu.post(event.x_root, event.y_root)

menubar = Menu(ROOT)
ROOT.config(menu=menubar)

# file menu
filemenu = Menu(menubar, tearoff=0)
menubar .add_cascade(label='File', menu=filemenu)
filemenu.add_command(label='Save', command=fileSave, accelerator=CONTROL+'-s')
filemenu.add_command(label='Quit', command=fileQuit, accelerator=CONTROL+'-q')

ROOT.bind('<%s-%s>' % (CONTROL, 's'), fileSave)
ROOT.bind('<%s-%s>' % (CONTROL, 'q'), fileQuit)

# annotate menu
annotatemenu = Menu(menubar, tearoff=0)
menubar.add_cascade(label='Annotate', menu=annotatemenu)
annotatemenu.add_command(label='Delete', command=annotateDelete, accelerator='-')
annotatemenu.add_separator()

for i,t in enumerate(ANN_TAGS):
    id = str(i+1)
    annotatemenu.add_command(label=t.desc, command=t.func, accelerator=id)
    ROOT.bind(id, t.func)

ROOT.bind('-', annotateDelete)

# popup menu
popupmenu = Menu(ROOT, tearoff=0)
popupmenu.add_command(label="Delete", command=annotateDelete, accelerator='-')
popupmenu.add_separator()
for i,t in enumerate(ANN_TAGS): popupmenu.add_command(label=t.desc, command=t.func, accelerator=str(i+1))
TEXT_AREA.bind('<Button-2>', popupMenu)

# =================== main ===================

# grid
ROOT.grid_rowconfigure   (0, weight=1)
ROOT.grid_columnconfigure(0, weight=0)
ROOT.grid_columnconfigure(1, weight=1)

TEXT_AREA.grid(row=0, column=1, sticky=NW+SE)
FILE_LIST.grid(row=0, column=0, sticky=NW+SE)

ROOT.mainloop()
