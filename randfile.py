import argparse,os,pathlib,shutil,sqlite3,hashlib,locale

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
lappdata = pathlib.Path(os.environ.get("LOCALAPPDATA")) / "randfile_appdata"
lappdata.mkdir(exist_ok=True)
dbname = hashlib.md5(ns.source.encode(locale.getpreferredencoding())).hexdigest()+"fscache"
dbfile = lappdata / dbname
cx = sqlite3.connect(dbfile)
cx.executescript(""" create table if not exists fscache(path,
    unique(path) on conflict ignore);""")
cu = cx.cursor()
cu.row_factory = lambda c,r:r[0]
if not cu.execute("select count() from fscache").fetchone():
    exts = ".mp3",".ogg",".wav",".flac",".m4a",".wma"
    for r,ds,fs in os.walk(ns.source):
        for f in fs:
            if any(list(map(f.endswith,exts))):
                cx.execute(
                        "insert into fscache(path) values (?)",
                        (os.path.join(r,f),))
cx.commit()
f = cu.execute(
        "select path from fscache order by random() limit 1").fetchone()
shutil.copy(f,ns.dest)
