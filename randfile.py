# randfile.py
from pathlib import Path
from sys import exit
from os import getenv
from shutil import copy
from os.path import expanduser
from tkinter import Tk,StringVar,filedialog
from tkinter.ttk import Entry,Label,Button,Frame,LabelFrame,OptionMenu
from sqlite3 import connect,Connection
from argparse import ArgumentParser
from ttkthemes import ThemedStyle

class Cx(object):
    def __init__(self,cx):
        self.cx = cx

class Data(Cx):
    def set(self,attr,value):
        print("setting",attr,"to",value)
        self.cx.execute(
                "insert into data(name,value)"
                "values (?,?)",
                (attr,value))
        self.cx.commit()
    def get(self,attr):
        return self.cx.cu.execute(
            "select value from data where name=?", (attr,)).fetchone()

class Files(Cx):
    def add(self,path):
        self.cx.execute("insert into fscache(path) values (?)",(path,))
    def pick(self):
        return self.cx.cu.execute(
                "select path from fscache order by random() limit 1"
                ).fetchone()



class AppData(Connection):
    definitions = """

            create table if not exists data (
            name, value default '',
            unique(name) on conflict replace);

            create table if not exists fscache (
            path,unique (path) on conflict ignore);

            """

    def __init__(self,*kw,**kwds):
        super().__init__(*kw,**kwds)
        self.executescript(self.definitions)
        self.commit()
        self.cu = self.cursor()
        self.cu.row_factory = lambda c,r:r[0]
        self.data = Data(self)
        self.files = Files(self)

args = ArgumentParser()
args.add_argument("--get",action="store_true")
args.add_argument("--clear",action="store_true")
args.add_argument("--theme",default="equilux")
argument = args.parse_args()

data_dir = Path(str(getenv("LOCALAPPDATA"))) / "randfile"
data_dir.mkdir(exist_ok=True)
db_path = str(data_dir / "randfile_data.sqlitedb")
db = connect(db_path,factory=AppData)
data = db.data
files = db.files

if argument.clear:
    db.execute("delete from fscache")
    data.set("last_scan","")
    exit()


if argument.get:
    input_path,output_path,last_scan,extension_filter = map(data.get,
            ("input_path","output_path","last_scan","extension_filter"))
    if not input_path and output_path:
        exit()
    source = Path(input_path)
    destination = Path(output_path)
    if not source.is_dir() and destination.is_dir():
        exit()
    if not last_scan == input_path:
        db.execute("delete from fscache")
        print("Scanning",input_path)
        globfilt = "**/*." + [extension_filter,"*"][extension_filter==None]
        for i,f in enumerate(source.glob(globfilt)):
            try:
                files.add(str(f))
            except UnicodeEncodeError:
                pass
        print(i,"files added")
        data.set("last_scan",input_path)
    selected_file = files.pick()
    if not selected_file:
        exit()
    copy(selected_file,output_path)
    print("Copied",selected_file,"to",output_path)
    exit()


def CxVar(name):
    v = StringVar()
    t = data.get(name)
    if t:
        v.set(t)
    def trace(*_):
        data.set(name,v.get())
    v.trace("w",trace)
    return v


class App(Frame):
    def __init__(self):
        super().__init__()

        self.v_lastscan = CxVar("last_scan")
        self.v_extfilt = CxVar("extension_filter")
        self.v_inputpath = CxVar("input_path")
        self.v_outputpath = CxVar("output_path")

        self.frame_top,self.frame_bot = Frame(self),Frame(self)

        self.frame_input = LabelFrame(self.frame_top,text="Source")
        self.frame_ext = LabelFrame(self.frame_top,text="Filetype Filter")
        self.frame_output = LabelFrame(self.frame_bot,text="Destination")



        self.btn_inputpath = Button(
                self.frame_input,
                textvariable=self.v_inputpath,
                command=lambda:self.v_inputpath.set(filedialog.askdirectory(title="Choose input folder")))
        
        common_extensions = "mp3","ogg","wav","jpg","gif","png","blend"

        self.opt_extfilt = OptionMenu(
                self.frame_ext,
                self.v_extfilt,
                "mp3",
                *common_extensions)

        self.btn_outputpath = Button(
                self.frame_output,
                textvariable=self.v_outputpath,
                command=lambda:self.v_outputpath.set(filedialog.askdirectory(title="Choose output folder")))
        self.config(padding="10")

        self.pack(fill="both",expand=True)

        self.frame_top.pack(fill="both",expand=True)
        self.frame_bot.pack(fill="both",expand=True)


        self.frame_input.pack(side="left",fill="both",expand=True)
        self.frame_ext.pack(fill="both",expand=True)

        self.frame_output.pack(fill="x")

        self.btn_inputpath.pack(anchor="ne")
        self.opt_extfilt.pack(anchor="ne")
        self.btn_outputpath.pack(anchor="ne")



app = App()
app.style = ThemedStyle()
print("app.style.theme_names():",app.style.theme_names())
app.style.set_theme(argument.theme)
app.mainloop()
