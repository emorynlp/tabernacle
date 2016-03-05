#  Copyright 2016, Emory University
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import Tkinter
import argparse
import platform
import glob
import os
from Tkinter import *


class Tag:
    def __init__(self, desc, color, func):
        self.desc = desc
        self.color = color
        self.func = func

class TextLocation:
    def __init__(self, tuple):
        string = tuple.split('.')
        self.line = int(string[0])
        self.pos = int(string[1])

    def getindex(self,line,pos):
        return str(line)+'.'+ str(pos)

    def findstart(self, textarea):
        newpos = self.pos
        while True:
            newpos = newpos-1
            teststart = self.getindex(self.line, newpos)
            testend = self.getindex(self.line, newpos+1)

            if newpos<0:
                return teststart

            if textarea.get(teststart, testend)==' ':
                return testend


    def findend(self,textarea):
        newpos = self.pos
        endloc= textarea.index("insert lineend")
        string = endloc.split('.')
        # endline = int(string[0])
        endpos = int(string[1])
        escape_chars = [' ', '.', ',', ':']

        while True:
            teststart = self.getindex(self.line, newpos)
            testend = self.getindex(self.line, newpos+1)

            if newpos>=endpos:
                return self.getindex(self.line, endpos)

            if textarea.get(teststart, testend) in escape_chars:
                return teststart

            if textarea.get(teststart, testend)==u"\r":
                return self.getindex(self.line, newpos)

            newpos = newpos+1



class Tabernacle(Tkinter.Tk):
    def __init__(self, path, extension):
        Tkinter.Tk.__init__(self)
        self.VERSION = 'Tabernacle 1.0'
        self.INPUT_DIR = path
        self.INPUT_EXT = extension
        self.OUTPUT_FILE = None
        self.INPUT_FILE = None
        self.CONTROL = 'Control'

        if platform.system() == 'Darwin':
            self.CONTROL = 'Command'

        # self.ROOT = Tkinter.Frame(self)

        self.TEXT_AREA = Tkinter.Text(self, width=120, height=55,
                                      selectbackground="red",
                                      selectforeground="white",
                                      inactiveselectbackground="red")
        self.TEXT_AREA.bind('<1>', lambda event: self.TEXT_AREA.focus_set())
        self.TEXT_AREA.pack()
        self.TEXT_AREA.tag_raise("sel")

        self.FILE_LIST = Tkinter.Listbox(self, width=12, height=49)
        self.FILE_LIST.bind('<<ListboxSelect>>', self.select_list)
        self.FILE_LIST.pack()

        for filename in sorted(glob.glob(os.path.join(self.INPUT_DIR, '*.'+self.INPUT_EXT))):
            self.FILE_LIST.insert(Tkinter.END, os.path.basename(filename))

        self.ANN_TAGS = [Tag('Name', '#FFFF00', self.annotate0),  # yellow
                         Tag('Date', '#FFA070', self.annotate1),  # light-salmon
                         Tag('Time', '#FFB8C0', self.annotate2),  # light-pick
                         Tag('Accession Number', '#90F090', self.annotate3),  # light-green
                         Tag('Medical Record Number', '#C0B860', self.annotate4)]  # dark-khaki

        self.ANN_DICT = None
        self.ANN_TAG_ID = 0

        self.menubar = Tkinter.Menu(self)
        self.config(menu=self.menubar)

        # file menu
        self.filemenu = Tkinter.Menu(self.menubar, tearoff=0)
        self.menubar .add_cascade(label='File', menu=self.filemenu)
        self.filemenu.add_command(label='Save', command=self.file_save, accelerator=self.CONTROL+'-s')
        self.filemenu.add_command(label='Quit', command=self.file_quit, accelerator=self.CONTROL+'-q')

        self.bind('<%s-%s>' % (self.CONTROL, 's'), self.file_save)
        self.bind('<%s-%s>' % (self.CONTROL, 'q'), self.file_quit)

        # annotate menu
        self.annotatemenu = Tkinter.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='Annotate', menu=self.annotatemenu)
        self.annotatemenu.add_command(label='Delete', command=self.annotate_delete, accelerator='-')
        self.annotatemenu.add_separator()

        for i,t in enumerate(self.ANN_TAGS):
            aid = str(i+1)
            self.annotatemenu.add_command(label=t.desc, command=t.func, accelerator=aid)
            self.bind(aid, t.func)

        self.bind('-', self.annotate_delete)

        # popup menu
        self.popupmenu = Tkinter.Menu(self, tearoff=0)
        self.popupmenu.add_command(label="Delete", command=self.annotate_delete, accelerator='-')
        self.popupmenu.add_separator()
        for i,t in enumerate(self.ANN_TAGS):
            self.popupmenu.add_command(label=t.desc, command=t.func, accelerator=str(i+1))
        self.TEXT_AREA.bind('<Button-2>', self.popup_menu)


        # =================== main ===================

        # grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.TEXT_AREA.grid(row=0, column=1, sticky=Tkinter.NW+Tkinter.SE)
        self.FILE_LIST.grid(row=0, column=0, sticky=Tkinter.NW+Tkinter.SE)

        self.TEXT_AREA.bind('<ButtonRelease-1>', self.get_tag)


    def HelloWorld(self):
      print 'Hello World'

    def select_list(self, event):
        index = self.FILE_LIST.curselection()[0]
        self.select_file(index)

    def select_file(self, index):
        self.file_save()

        # title
        self.INPUT_FILE = os.path.join(self.INPUT_DIR, self.FILE_LIST.get(index))
        self.title(self.INPUT_FILE)

        # text
        fin = open(self.INPUT_FILE)
        self.TEXT_AREA.config(state=Tkinter.NORMAL)
        self.TEXT_AREA.delete(1.0, Tkinter.END)
        self.TEXT_AREA.insert(Tkinter.END, fin.read())
        self.TEXT_AREA.config(state=Tkinter.DISABLED)
        fin.close()

        # annotation
        self.OUTPUT_FILE = self.INPUT_FILE+'.map'
        self.ANN_DICT = dict()
        self.ANN_TAG_ID = 0
        if not os.path.isfile(self.OUTPUT_FILE): return

        fin = open(self.OUTPUT_FILE)
        for line in fin:
            l = line.split()
            self.add_tag(l[1], l[2], int(l[0]))
        fin.close()

    def annotate_add(self, event, aid):
        (start, end, bsel) = self.get_span()
        self.add_tag(start, end, aid)

    def annotate_delete(self, event):
        (start, end, bsel) = self.get_span()
        self.delete_tag(start, end)

    def annotate_delete(self):
        (start, end, bsel) = self.get_span()
        self.delete_tag(start, end)

    def add_tag(self, start, end, aid):
        sel_key = (start, end)
        key = sel_key

        for k,val in self.ANN_DICT.items():
            ks = float(k[0])
            ke = float(k[1])

            ss = float(sel_key[0])
            se = float(sel_key[1])

            # ss ks se
            if ss<ks and ks<se:
                return

            # ss ke se
            if ss<ke and ke<se:
                return


            # if float(k[0]) > float(sel_key[0]) and float(k[1]) < float(sel_key[1]):
            #     return

            if float(k[0]) == float(sel_key[0]) and float(k[1]) == float(sel_key[1]):
                tag = self.ANN_DICT[k][1]
                key = k
                start = k[0]
                end = k[1]
                break

        self.TEXT_AREA.config(state=Tkinter.NORMAL)
        self.delete_tag(start, end)

        tag = str(self.ANN_TAG_ID)
        self.ANN_DICT[key] = (aid, tag)
        self.ANN_TAG_ID += 1

        self.TEXT_AREA.tag_add(tag, start, end)
        self.TEXT_AREA.tag_config(tag, background=self.ANN_TAGS[aid].color, foreground='black')
        self.TEXT_AREA.tag_lower(tag)
        self.TEXT_AREA.config(state=Tkinter.DISABLED)

    def delete_tag(self, start, end):
        # global ANN_DICT, TEXT_AREA
        sel_key = (start, end)

        for k,val in self.ANN_DICT.items():
            if float(k[0]) <= float(sel_key[0]) and float(k[1]) >= float(sel_key[1]):
                tag = self.ANN_DICT[k][1]
                del self.ANN_DICT[k]
                self.TEXT_AREA.tag_delete(tag)
                return True

        return False

    @staticmethod
    def adjust_span(index, margin):
        if margin == 0:
            return index
        t = index.split('.')
        t[1] = str(int(t[1]) + margin)
        return '.'.join(t)

    def get_span(self):
        textselection = False
        try:
            self.TEXT_AREA.selection_get()
            lineend = self.TEXT_AREA.index("insert lineend")

            start = self.TEXT_AREA.index(Tkinter.SEL_FIRST)
            end = self.TEXT_AREA.index(Tkinter.SEL_LAST)
            text = self.TEXT_AREA.selection_get()
            start = Tabernacle.adjust_span(start, len(text) - len(text.lstrip()))
            end = Tabernacle.adjust_span(end, len(text.rstrip()) - len(text))

            startloc = TextLocation(start)
            start = startloc.findstart(self.TEXT_AREA)

            endloc = TextLocation(end)
            end = endloc.findend(self.TEXT_AREA)

            textselection = True
        except:
            start = self.TEXT_AREA.index("insert wordstart")
            end = self.TEXT_AREA.index("insert wordend")
        return start, end, textselection

    def annotate0(self, event=None):
        self.annotate_add(event, 0)

    def annotate1(self, event=None):
        self.annotate_add(event, 1)

    def annotate2(self, event=None):
        self.annotate_add(event, 2)

    def annotate3(self, event=None):
        self.annotate_add(event, 3)

    def annotate4(self, event=None):
        self.annotate_add(event, 4)

    def file_save(self, event=None):
        # global ANN_DICT
        if not self.OUTPUT_FILE or not self.ANN_DICT: return
        fout = open(self.OUTPUT_FILE,'w')

        for key in self.ANN_DICT:
            aid = self.ANN_DICT[key][0]
            s = '%d %s %s\n' % (aid, key[0], key[1])
            fout.write(s)

        fout.close()

    def file_quit(self, event=None):
        self.file_save()
        self.quit


    # =================== menu ===================

    def popup_menu(self, event):
        self.popupmenu.post(event.x_root, event.y_root)

    # def _on_click(self, event):
    #     try:
    #         self.text.selection_get()
    #         (start, end) = self.get_span()
    #     except:
    #         start = "insert wordstart"
    #         end = "insert wordend"
    #
    #     # (start, end) = self.get_span()
    #     self.TEXT_AREA.tag_remove("highlight", "1.0", "end")
    #     self.TEXT_AREA.tag_add("highlight", start, end)



    def get_tag(self, event):
        (start, end, bsel) = self.get_span()
        position = self.TEXT_AREA.index(CURRENT)
        ptl = TextLocation(position)
        print ptl.line, ptl.pos

        if self.ANN_DICT is None:
            return

        for k,val in self.ANN_DICT.items():
            tag = val[1]
            tl1 = TextLocation(k[0])
            tl2 = TextLocation(k[1])
            # print tl1.line, tl1.pos
            if (tl1.line is not ptl.line) and (tl2.line is not ptl.line):
                continue

            if  tl1.pos<=ptl.pos and ptl.pos<=tl2.pos:
                # if float(k[0]) > float(start) and float(k[1]) < float(end) and bsel:
                if ((float(k[0]) is not float(start)) or (float(k[1]) is not float(end))) and bsel:
                    continue
                print 'found', k
                self.popupmenu.post(event.x_root, event.y_root)
                # self.TEXT_AREA.tag_config(tag, background="black", foreground='black')

            if tl2.line is not tl1.line:
                if tl1.pos<=ptl.pos or ptl.pos<=tl2.pos:
                    if ((float(k[0]) is not float(start)) or (float(k[1]) is not float(end))) and bsel:
                        continue
                    print 'found', k
                    self.popupmenu.post(event.x_root, event.y_root)
                    # self.TEXT_AREA.tag_config(tag, background="black", foreground='black')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("extension")
    args = parser.parse_args()

    app = Tabernacle(args.path, args.extension)
    app.mainloop()

