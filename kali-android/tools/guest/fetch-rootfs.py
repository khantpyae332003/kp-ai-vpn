#!/usr/bin/env python3
"""Fetch the pinned vendor Kali desktop OCI layers and safely inspect/extract in our build container."""
import hashlib,json,os,pathlib,subprocess,tarfile,urllib.request as U,urllib.parse as P
class SafeRedirect(U.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  old=P.urlsplit(req.full_url);new=P.urlsplit(newurl)
  if new.scheme!='https' or new.hostname not in {'registry-1.docker.io','production.cloudfront.docker.com'} or new.username or new.port not in (None,443):raise RuntimeError('Artifact redirect rejected')
  result=super().redirect_request(req,fp,code,msg,headers,newurl)
  if (old.scheme,old.hostname,old.port)!=(new.scheme,new.hostname,new.port):result.remove_header('Authorization')
  return result
U.install_opener(U.build_opener(SafeRedirect()))
ROOT=pathlib.Path(__file__).resolve().parents[2];WORK=ROOT/'.tools/auto-setup';BLOBS=WORK/'blobs';BLOBS.mkdir(parents=True,exist_ok=True)
REPO='kasmweb/kali-rolling-desktop';DIGEST='sha256:e1734859c9c508c41c0f30cb33cfa56c9d9a7044a4250dc9ae0be078792623d4'
DOCKER=['docker','--host=unix:///var/run/docker.sock','exec','kp-kali-build']
def run(*args,stdin=None):subprocess.run(DOCKER+list(args),stdin=stdin,check=True,stdout=subprocess.DEVNULL)
def token():return json.load(U.urlopen('https://auth.docker.io/token?'+P.urlencode({'service':'registry.docker.io','scope':'repository:'+REPO+':pull'})))['token']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def fetch_blob(spec):
 digest=spec['digest'].split(':')[1];target=BLOBS/(digest+'.gz');part=target.with_suffix('.part')
 if target.exists() and target.stat().st_size==spec['size'] and sha(target)==digest:return target
 offset=part.stat().st_size if part.exists() else 0
 if offset>spec['size']:part.unlink();offset=0
 headers={'Authorization':'Bearer '+token()}
 if offset:headers['Range']='bytes='+str(offset)+'-'
 req=U.Request('https://registry-1.docker.io/v2/'+REPO+'/blobs/'+spec['digest'],headers=headers)
 with U.urlopen(req,timeout=120) as r:
  if offset and r.status!=206:offset=0
  if offset and not r.headers.get('Content-Range','').startswith('bytes '+str(offset)+'-'):raise RuntimeError('Invalid resume response')
  mode='ab' if offset else 'wb';reported=offset
  with part.open(mode) as out:
   count=offset
   while True:
    data=r.read(4*1024*1024)
    if not data:break
    count+=len(data)
    if count>spec['size']:raise RuntimeError('Oversized artifact')
    out.write(data)
    if count-reported>=256*1024*1024:print('download',digest[:12],count,'/',spec['size'],flush=True);reported=count
   out.flush();os.fsync(out.fileno())
 if part.stat().st_size!=spec['size'] or sha(part)!=digest:raise RuntimeError('Image layer size/SHA256 mismatch')
 part.replace(target);return target
headers={'Authorization':'Bearer '+token(),'Accept':'application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.manifest.v1+json'}
with U.urlopen(U.Request('https://registry-1.docker.io/v2/'+REPO+'/manifests/'+DIGEST,headers=headers)) as r:manifest_bytes=r.read()
assert 'sha256:'+hashlib.sha256(manifest_bytes).hexdigest()==DIGEST,'Manifest mismatch'
manifest=json.loads(manifest_bytes);profile={'schema':1,'publisher':'Kasm Technologies','repository':REPO,'tag':'1.19.0','manifestDigest':DIGEST,'layers':[]}
run('mkdir','-p','/guestroot/.kp-tools');run('cp','/bin/busybox','/guestroot/.kp-tools/busybox');run('chmod','755','/guestroot/.kp-tools/busybox')
for index,spec in enumerate(manifest['layers']):
 print('layer',index+1,'/',len(manifest['layers']),'compressed bytes',spec['size'],flush=True)
 p=fetch_blob(spec);whiteouts=[];entries=0;unpacked=0
 with tarfile.open(p,'r|gz') as tar:
  for m in tar:
   entries+=1;name=m.name.removeprefix('./');path=pathlib.PurePosixPath(name)
   if path.is_absolute() or '..' in path.parts or '\x00' in name or '\n' in name:raise RuntimeError('Unsafe archive path')
   if path.parts and path.parts[0]=='.kp-tools':raise RuntimeError('Reserved helper path in producer layer')
   if m.isfile():unpacked+=m.size
   if path.name.startswith('.wh.'):
    if path.name=='.wh..wh..opq':whiteouts.append({'type':'opaque','path':str(path.parent)})
    else:whiteouts.append({'type':'remove','path':str(path.parent/path.name[4:])})
 print('verified tar',index+1,'entries',entries,'regular-file bytes',unpacked,'whiteouts',len(whiteouts),flush=True)
 for w in whiteouts:
  dest='/' if w['path']=='.' else '/'+w['path']
  if w['type']=='remove':run('chroot','/guestroot','/.kp-tools/busybox','rm','-rf','--',dest)
  else:run('chroot','/guestroot','/.kp-tools/busybox','find',dest,'-mindepth','1','-maxdepth','1','!','-name','.kp-tools','-exec','/.kp-tools/busybox','rm','-rf','--','{}',';')
 with p.open('rb') as data:
  subprocess.run(['docker','--host=unix:///var/run/docker.sock','exec','-i','kp-kali-build','chroot','/guestroot','/.kp-tools/busybox','tar','-xzpf','-','--numeric-owner'],stdin=data,check=True,stdout=subprocess.DEVNULL)
 # OCI whiteout marker files are not part of the installed root filesystem.
 for w in whiteouts:
  marker=(pathlib.PurePosixPath(w['path']).parent/('.wh.'+pathlib.PurePosixPath(w['path']).name)) if w['type']=='remove' else pathlib.PurePosixPath(w['path'])/'.wh..wh..opq'
  run('chroot','/guestroot','/.kp-tools/busybox','rm','-f','--','/'+str(marker))
 profile['layers'].append({'digest':spec['digest'],'size':spec['size'],'whiteouts':whiteouts,'regularBytes':unpacked})
 (WORK/'oci-profile.json').write_text(json.dumps(profile,indent=2)+'\n')
 print('extracted layer',index+1,flush=True)
run('rm','/guestroot/.kp-tools/busybox');run('rmdir','/guestroot/.kp-tools')
print('Rootfs producer layers verified and extracted.',flush=True)
