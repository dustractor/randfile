import argparse,os,pathlib,shutil,sqlite3,hashlib


class FSCache:
    def count(self):
        return self.cu.execute("select count() from fscache").fetchone()

    def __init__(self,path):
        _appdata_p = pathlib.Path(os.environ.get("LOCALAPPDATA")) / "randfile_appdata"
        _appdata_p.mkdir(exist_ok=True)
        dbname = ".".join((hashlib.md5(path.encode()).hexdigest(),"fscache"))
        self.dbfile = _appdata_p / dbname
        self.cx = sqlite3.connect(self.dbfile)
        self.cx.executescript("""
            create table if not exists fscache ( path,
            unique (path) on conflict ignore);
            """)
        self.cu = self.cx.cursor()
        self.cu.row_factory = lambda c,r:r[0]
        if not self.count():
            exts = ".mp3",".ogg",".wav",".flac",".m4a",".wma"
            for r,ds,fs in os.walk(path):
                for f in fs:
                    if any(list(map(f.endswith,exts))):
                        self.cx.execute(
                                "insert into fscache(path) values (?)",
                                (os.path.join(r,f),))
        self.cx.commit()


def dir_type(path):
    p = pathlib.Path(path)
    if p.is_dir():
        return str(p.resolve())
    else:
        raise TypeError

args = argparse.ArgumentParser()
args.add_argument("source",type=dir_type)
args.add_argument("dest",type=dir_type)

ns = args.parse_args()

source = FSCache(ns.source)
f = source.cu.execute(
        "select path from fscache order by random() limit 1").fetchone()
shutil.copy(f,ns.dest)
