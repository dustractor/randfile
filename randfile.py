
import os
import pathlib
import shutil
import sqlite3
from tkinter import (
        Tk,
        Frame,
        Entry,
        Label,
        Listbox,
        Button,
        StringVar,
        filedialog)
from tkinter.ttk import LabelFrame


class Db(sqlite3.Connection):
    def __init__(self,*kw,**kwds):
        super().__init__(*kw,*kwds)
        self.executescript( """
                create table if not exists settings( name text, value text,
                unique (name) on conflict replace);
                create table if not exists files( path text,
                unique (path) on conflict replace); """)
        self.commit()
        self.cu = self.cursor()
        self.cu.row_factory=lambda c,r:r[0]

dbfile = os.path.expanduser("~/_randfile.db")
db = Db(dbfile)


class App(Tk):
    def __init__(self,master=None):
        super().__init__(master)
        self.input_dir = StringVar()
        self.filter_ext = StringVar()
        self.output_dir = StringVar()
        self.input_dir.trace('w',self.input_dir_trace)
        self.output_dir.trace('w',self.output_dir_trace)
        self.filter_ext.trace('w',self.filter_ext_trace)
        input_dir = db.cu.execute(
                "select value from settings where name=?",
                ("input_dir",)).fetchone()
        if input_dir:
            self.input_dir.set(input_dir)
        output_dir = db.cu.execute(
                "select value from settings where name=?",
                ("output_dir",)).fetchone()
        if output_dir:
            self.output_dir.set(output_dir)
        filter_ext = db.cu.execute(
                "select value from settings where name=?",
                ("filter_ext",)).fetchone()
        if filter_ext:
            self.filter_ext.set(filter_ext)
        else:
            self.filter_ext.set("mp3")

        self.lbl_input_dir = Label(self,textvariable=self.input_dir)
        self.frame_input = LabelFrame(self,labelwidget=self.lbl_input_dir)
        self.frame_input.pack(fill="both",expand=True)

        self.btn_input_dir_select = Button(self.frame_input,text="Select Input Dir",
                command=self.ask_inputdir_cmd)
        self.btn_input_dir_select.pack()

        self.lbl_filter_ext = Entry(self.frame_input,textvariable=self.filter_ext)
        self.lbl_filter_ext.pack()
        self.btn_input_dir_scan = Button(self.frame_input,text="Scan Input Dir",
                command=self.scan_inputdir_cmd)
        self.btn_input_dir_scan.pack()

        self.lbl_output_dir = Label(self,textvariable=self.output_dir)
        self.frame_output = LabelFrame(self,labelwidget=self.lbl_output_dir)
        self.frame_output.pack(fill="both",expand=True)

        self.btn_output_dir_select = Button(self.frame_output,text="Select Output Dir",
                command=self.ask_outputdir_cmd)
        self.btn_output_dir_select.pack()
        self.btn_get_random_file = Button(self.frame_output,text="Get Random File",
                command=self.get_random_file_cmd)
        self.btn_get_random_file.pack()
        self.bind("<Control-q>",lambda *_:self.quit())
        self.bind("<Control-w>",lambda *_:self.quit())

    def scan_inputdir_cmd(self):
        path = self.input_dir.get()
        ext = "." + self.filter_ext.get()
        if not pathlib.Path(path).is_dir():
            return
        try:
            for r,ds,fs in os.walk(path):
                for f in fs:
                    if f.endswith(ext):
                        path = os.path.join(r,f)
                        db.execute(
                                "insert into files(path) values (?)",
                                (path,))
        except:
            pass
        finally:
            db.commit()

    def input_dir_trace(self,*v):
        t = pathlib.Path(self.input_dir.get())
        if t.is_dir():
            db.execute(
                    "insert into settings(name,value) values(?,?)",
                    ("input_dir",str(t)))
            db.commit()

    def output_dir_trace(self,*v):
        t = pathlib.Path(self.output_dir.get())
        if t.is_dir():
            db.execute(
                    "insert into settings(name,value) values(?,?)",
                    ("output_dir",str(t)))
            db.commit()

    def filter_ext_trace(self,*v):
        t = self.filter_ext.get()
        db.execute(
                "insert into settings(name,value) values(?,?)",
                ("filter_ext",t))
        db.commit()
    def ask_inputdir_cmd(self):
        chosen_input_dir = pathlib.Path(filedialog.askdirectory())
        if chosen_input_dir.is_dir():
            print("you chose",chosen_input_dir)
            self.input_dir.set(str(chosen_input_dir))

    def ask_outputdir_cmd(self):
        chosen_output_dir = pathlib.Path(filedialog.askdirectory())
        if chosen_output_dir.is_dir():
            print("you chose",chosen_output_dir)
            self.output_dir.set(str(chosen_output_dir))

    def get_random_file_cmd(self):
        input_dir = self.input_dir.get()
        output_dir = self.output_dir.get()
        if ( pathlib.Path(input_dir).is_dir() and
             pathlib.Path(output_dir).is_dir()):
            rf = db.cu.execute("select path from files order by random() limit 1").fetchone()
        shutil.copy(rf,output_dir)
        print("random file (",rf,") copied to:", output_dir)


if __name__ == "__main__":
    App().mainloop()

