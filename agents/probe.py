"""Live server check. Requires root/CAP_NET_ADMIN; never runs source-provided code."""
import ipaddress,os,re,socket,subprocess,tempfile,time,uuid
from pathlib import Path
from .core import global_ip

ENV={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LANG':'C'}
def run(args,timeout=15):
 return subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=timeout,check=True,env=ENV).stdout.decode().strip()

def probe(profile):
 name='kp'+uuid.uuid4().hex[:10];namespace=name;created=False;device=False
 try:
  host,port=profile['endpoint']
  answers=socket.getaddrinfo(host,port,type=socket.SOCK_DGRAM)
  ips=[a[4][0] for a in answers]
  if not ips or any(not global_ip(ip) for ip in ips):return False
  ip=ips[0];endpoint=f'[{ip}]:{port}' if ':' in ip else f'{ip}:{port}'
  config=re.sub(r'(?m)^Endpoint = .+$','Endpoint = '+endpoint,profile['wg_setconf'])
  with tempfile.TemporaryDirectory(prefix='kpvpn-') as d:
   path=Path(d)/'peer';path.write_text(config);path.chmod(0o600)
   run(['ip','netns','add',namespace]);created=True
   # The encrypted UDP socket stays in the initial namespace; only tunnel-side
   # routes live in the namespace, so the runner's own network is never replaced.
   run(['ip','link','add',name,'type','wireguard']);device=True
   run(['wg','setconf',name,str(path)])
   run(['ip','link','set',name,'netns',namespace]);device=False
   run(['ip','-n',namespace,'link','set','lo','up'])
   for address in profile['addresses']:run(['ip','-n',namespace,'address','add',address,'dev',name])
   run(['ip','-n',namespace,'link','set',name,'up'])
   run(['ip','-n',namespace,'route','add','default','dev',name])
   start=int(time.time())
   # Fixed public HTTPS target; no private HTTP target or credentials.
   run(['ip','netns','exec',namespace,'curl','--silent','--fail','--max-time','12','--noproxy','*','--resolve','www.cloudflare.com:443:104.16.132.229','https://www.cloudflare.com/cdn-cgi/trace'])
   handshakes=run(['ip','netns','exec',namespace,'wg','show',name,'latest-handshakes'])
   values=[int(line.split()[1]) for line in handshakes.splitlines() if len(line.split())==2]
   return bool(values) and all(v>=start for v in values)
 except Exception:return False
 finally:
  if device:
   try:run(['ip','link','del',name])
   except Exception:pass
  if created:
   try:run(['ip','netns','del',namespace])
   except Exception:pass
