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
import re

class ToolTip:
    def __init__(self, master, text='Your text here', delay=1500, **opts):
        self.master = master
        self._opts = {'anchor':'center', 'bd':1, 'bg':'lightyellow', 'delay':delay, 'fg':'black',\
                      'follow_mouse':0, 'font':None, 'justify':'left', 'padx':4, 'pady':2,\
                      'relief':'solid', 'state':'normal', 'text':text, 'textvariable':None,\
                      'width':0, 'wraplength':150}
        self.configure(**opts)
        self._tipwindow = None
        self._id = None
        self._id1 = self.master.bind("<Enter>", self.enter, '+')
        self._id2 = self.master.bind("<Leave>", self.leave, '+')
        self._id3 = self.master.bind("<ButtonPress>", self.leave, '+')
        self._follow_mouse = 0
        if self._opts['follow_mouse']:
            self._id4 = self.master.bind("<Motion>", self.motion, '+')
            self._follow_mouse = 1

    def configure(self, **opts):
        for key in opts:
            if self._opts.has_key(key):
                self._opts[key] = opts[key]
            else:
                KeyError = 'KeyError: Unknown option: "%s"' %key
                raise KeyError

    ##----these methods handle the callbacks on "<Enter>", "<Leave>" and "<Motion>"---------------##
    ##----events on the parent widget; override them if you want to change the widget's behavior--##

    def enter(self, event=None):
        self._schedule()

    def leave(self, event=None):
        self._unschedule()
        self._hide()

    def motion(self, event=None):
        if self._tipwindow and self._follow_mouse:
            x, y = self.coords()
            self._tipwindow.wm_geometry("+%d+%d" % (x, y))

    ##------the methods that do the work:---------------------------------------------------------##

    def _schedule(self):
        self._unschedule()
        if self._opts['state'] == 'disabled':
            return
        self._id = self.master.after(self._opts['delay'], self._show)

    def _unschedule(self):
        id = self._id
        self._id = None
        if id:
            self.master.after_cancel(id)

    def _show(self):
        if self._opts['state'] == 'disabled':
            self._unschedule()
            return
        if not self._tipwindow:
            self._tipwindow = tw = Tkinter.Toplevel(self.master)
            # hide the window until we know the geometry
            tw.withdraw()
            tw.wm_overrideredirect(1)

            if tw.tk.call("tk", "windowingsystem") == 'aqua':
                tw.tk.call("::tk::unsupported::MacWindowStyle", "style", tw._w, "help", "none")

            self.create_contents()
            tw.update_idletasks()
            x, y = self.coords()
            tw.wm_geometry("+%d+%d" % (x, y))
            tw.deiconify()

    def _hide(self):
        tw = self._tipwindow
        self._tipwindow = None
        if tw:
            tw.destroy()

    ##----these methods might be overridden in derived classes:----------------------------------##

    def coords(self):
        # The tip window must be completely outside the master widget;
        # otherwise when the mouse enters the tip window we get
        # a leave event and it disappears, and then we get an enter
        # event and it reappears, and so on forever :-(
        # or we take care that the mouse pointer is always outside the tipwindow :-)
        tw = self._tipwindow
        twx, twy = tw.winfo_reqwidth(), tw.winfo_reqheight()
        w, h = tw.winfo_screenwidth(), tw.winfo_screenheight()
        # calculate the y coordinate:
        if self._follow_mouse:
            y = tw.winfo_pointery() + 20
            # make sure the tipwindow is never outside the screen:
            if y + twy > h:
                y = y - twy - 30
        else:
            y = self.master.winfo_rooty() + self.master.winfo_height() + 3
            if y + twy > h:
                y = self.master.winfo_rooty() - twy - 3
        # we can use the same x coord in both cases:
        x = tw.winfo_pointerx() - twx / 2
        if x < 0:
            x = 0
        elif x + twx > w:
            x = w - twx
        return x, y

    def create_contents(self):
        opts = self._opts.copy()
        for opt in ('delay', 'follow_mouse', 'state'):
            del opts[opt]
        label = Tkinter.Label(self._tipwindow, **opts)
        label.pack()

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

class HoverInfo(Menu):
    def __init__(self, parent, text, command=None):
        self._com = command
        Menu.__init__(self,parent, tearoff=0)
        if not isinstance(text, str):
            raise TypeError('Trying to initialise a Hover Menu with a non string type: ' + text.__class__.__name__)
        toktext=re.split('\n', text)
        for t in toktext:
            self.add_command(label = t)
            self._displayed=False
            self.master.bind("<Enter>",self.Display )
            self.master.bind("<Leave>",self.Remove )

    def __del__(self):
        self.master.unbind("<Enter>")
        self.master.unbind("<Leave>")

    def Display(self,event):
        if not self._displayed:
            self._displayed=True
            self.post(event.x_root, event.y_root)
        if self._com != None:
            self.master.unbind_all("<Return>")
            self.master.bind_all("<Return>", self.Click)

    def Remove(self, event):
        if self._displayed:
            self._displayed=False
            self.unpost()
        if self._com != None:
            self.unbind_all("<Return>")

    def Click(self, event):
        self._com()

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

        self.TEXT_AREA = Tkinter.Text(self, width=120, height=55, selectbackground="red", selectforeground="white", inactiveselectbackground="red")
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
        for i,t in enumerate(self.ANN_TAGS): self.popupmenu.add_command(label=t.desc, command=t.func, accelerator=str(i+1))
        self.TEXT_AREA.bind('<Button-2>', self.popup_menu)


        # =================== main ===================

        # grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.TEXT_AREA.grid(row=0, column=1, sticky=Tkinter.NW+Tkinter.SE)
        self.FILE_LIST.grid(row=0, column=0, sticky=Tkinter.NW+Tkinter.SE)

        # self.TEXT_AREA.bind("<ButtonRelease-1>", self._on_click)

    #     self.ANN_DICT.label.bind("<Enter>", lambda e, x=x: e.widget.config(text=x))
    # label.bind("<Leave>", lambda e, i=i: e.widget.config(text="Label "+str(i)))


        # self.hover = HoverInfo(self.ANN_DICT, 'while hovering press return \n for an exciting msg', self.HelloWorld)

        # self.l1 = Tkinter.Label(self, text="Hover over me")
        # self.l2 = Tkinter.Label(self, text="", width=40)
        # self.l1.pack(side="top")
        # self.l2.pack(side="top", fill="x")
        # self.l1.bind("<Enter>", self.on_enter)
        # self.l1.bind("<Leave>", self.on_leave)

        self.TEXT_AREA.bind('<ButtonRelease-1>', self.get_tag)
        # t1 = ToolTip(self.TEXT_AREA, follow_mouse=1, text="I'm a tooltip with follow_mouse set to 1, so I won't be placed outside my parent")

    # def on_enter(self, event):
    #     self.l2.configure(text="Hello world")
    #
    # def on_leave(self, enter):
    #     self.l2.configure(text="")

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
        # self.hover = HoverInfo(self.ANN_DICT, 'while hovering press return \n for an exciting msg', self.HelloWorld)

    def annotate_add(self, event, aid):
        (start, end) = self.get_span()
        self.add_tag(start, end, aid)

    def annotate_delete(self, event):
        (start, end) = self.get_span()
        self.delete_tag(start, end)

    def annotate_delete(self):
        (start, end) = self.get_span()
        # try:
        #     self.TEXT_AREA.selection_get()
        #     (start, end) = self.get_span()
        # except:
        #     start = self.TEXT_AREA.index("insert wordstart")
        #     end = self.TEXT_AREA.index("insert wordend")

        self.delete_tag(start, end)

    def add_tag(self, start, end, aid):
        self.TEXT_AREA.config(state=Tkinter.NORMAL)
        self.delete_tag(start, end)

        key = (start, end)
        tag = str(self.ANN_TAG_ID)
        self.ANN_DICT[key] = (aid, tag)
        self.ANN_TAG_ID += 1

        self.TEXT_AREA.tag_add(tag, start, end)
        self.TEXT_AREA.tag_config(tag, background=self.ANN_TAGS[aid].color, foreground='black')
        self.TEXT_AREA.tag_lower(tag)
        self.TEXT_AREA.config(state=Tkinter.DISABLED)

    def delete_tag(self, start, end):
        # global ANN_DICT, TEXT_AREA
        key = (start, end)

        if key in self.ANN_DICT:
            tag = self.ANN_DICT[key][1]
            del self.ANN_DICT[key]
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
        try:
            self.TEXT_AREA.selection_get()
            start = self.TEXT_AREA.index(Tkinter.SEL_FIRST)
            end = self.TEXT_AREA.index(Tkinter.SEL_LAST)
            text = self.TEXT_AREA.selection_get()
            start = Tabernacle.adjust_span(start, len(text) - len(text.lstrip()))
            end = Tabernacle.adjust_span(end, len(text.rstrip()) - len(text))
        except:
            start = self.TEXT_AREA.index("insert wordstart")
            end = self.TEXT_AREA.index("insert wordend")

            # for k,val in self.ANN_DICT.items():
            #     tag = val[1]
            #     tl1 = TextLocation(k[0])
            #     tl2 = TextLocation(k[1])
            #     # print tl1.line, tl1.pos
            #     if (tl1.line is not ptl.line) and (tl2.line is not ptl.line):
            #         continue
            #
            #     if  tl1.pos<=start and end<=tl2.pos:
            #         print 'found', k
            #
            #         # self.TEXT_AREA.tag_config(tag, background="black", foreground='black')
            #
            #     if tl2.line is not tl1.line:
            #         if tl1.pos<=ptl.pos or ptl.pos<=tl2.pos:
            #             print 'found', k

                    # self.TEXT_AREA.tag_config(tag, background="black", foreground='black')



        return start, end

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

    def _on_click(self, event):
        try:
            self.text.selection_get()
            (start, end) = self.get_span()
        except:
            start = "insert wordstart"
            end = "insert wordend"

        # (start, end) = self.get_span()
        self.TEXT_AREA.tag_remove("highlight", "1.0", "end")
        self.TEXT_AREA.tag_add("highlight", start, end)



    def get_tag(self, event):
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
                print 'found', k
                self.popupmenu.post(event.x_root, event.y_root)
                # self.TEXT_AREA.tag_config(tag, background="black", foreground='black')

            if tl2.line is not tl1.line:
                if tl1.pos<=ptl.pos or ptl.pos<=tl2.pos:
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

