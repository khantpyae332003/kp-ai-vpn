#!/usr/bin/env python3
"""Reconstruct the pinned compressed initramfs without replacing valid data on failure."""
import hashlib,json,os,re,sys,tempfile
from pathlib import Path

def restore(root):
 root=Path(root);parts=root/'ci-payload';manifest=json.loads((parts/'manifest.json').read_text())
 assets=root/'engine/kali-app/src/main/assets/managed';profile=json.loads((assets/'profile.json').read_text())
 if manifest['sha256']!=profile['initrdSha256']:raise ValueError('Payload manifest/profile mismatch')
 target=assets/'initrd.bin';stage=None
 try:
  digest=hashlib.sha256();size=0
  with tempfile.NamedTemporaryFile(dir=assets,prefix='verified-initrd-',delete=False) as out:
   stage=Path(out.name)
   for name in manifest['parts']:
    if not re.fullmatch(r'part-\d{3}',name):raise ValueError('Invalid payload part path')
    with (parts/name).open('rb') as part:
     while chunk:=part.read(1024*1024):out.write(chunk);digest.update(chunk);size+=len(chunk)
   out.flush();os.fsync(out.fileno())
  if size!=manifest['size'] or digest.hexdigest()!=manifest['sha256']:raise ValueError('Payload integrity check failed')
  stage.replace(target);print('Verified compressed initramfs:',size,'bytes; SHA256 matches profile')
 finally:
  if stage and stage.exists():stage.unlink()
if __name__=='__main__':restore(sys.argv[1])
