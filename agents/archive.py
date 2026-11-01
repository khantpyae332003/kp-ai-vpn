"""Inspect public archives in memory; never extract source-provided paths."""
import io,zipfile,hashlib
from pathlib import PurePosixPath
MAX_ARCHIVE=8*1024*1024
MAX_EXPANDED=16*1024*1024
MAX_MEMBER=128*1024

def safe_member(name):
 p=PurePosixPath(name)
 return bool(name) and not p.is_absolute() and '..' not in p.parts and '\\' not in name and name.lower().endswith('.conf')

def inspect_archive(raw,limit=20,slot=0,preferred=()):
 if len(raw)>MAX_ARCHIVE:raise ValueError('Archive limit')
 archive_hash=hashlib.sha256(raw).hexdigest()
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  entries=z.infolist()
  if len(entries)>4000 or sum(e.file_size for e in entries)>MAX_EXPANDED:raise ValueError('Expansion limit')
  names=sorted({e.filename for e in entries if safe_member(e.filename) and not e.is_dir() and 0<e.file_size<=MAX_MEMBER})
  if not names:return []
  first=[n for n in preferred if n in names][:min(8,limit)]
  rest=[n for n in names if n not in first];offset=(slot*max(1,limit-len(first)))%len(rest) if rest else 0
  chosen=(first+rest[offset:]+rest[:offset])[:limit];out=[]
  for name in chosen:
   with z.open(name) as f:body=f.read(MAX_MEMBER+1)
   if len(body)>MAX_MEMBER:raise ValueError('Member limit')
   out.append({'member':name,'name':PurePosixPath(name).name,'archive_sha256':archive_hash,'member_sha256':hashlib.sha256(body).hexdigest()})
  return out

def read_member(raw,item):
 if len(raw)>MAX_ARCHIVE or hashlib.sha256(raw).hexdigest()!=item['archive_sha256']:raise ValueError('Archive changed')
 name=item['member']
 if not safe_member(name):raise ValueError('Unsafe member')
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  entry=z.getinfo(name)
  if entry.file_size>MAX_MEMBER:raise ValueError('Member limit')
  with z.open(entry) as f:body=f.read(MAX_MEMBER+1)
 if len(body)>MAX_MEMBER or hashlib.sha256(body).hexdigest()!=item['member_sha256']:raise ValueError('Member changed')
 return body
