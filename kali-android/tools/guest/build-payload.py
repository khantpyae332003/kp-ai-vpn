#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Reproducible local payload assembly using verified distribution packages.
Requires the documented unprivileged kp-kali-build container and OCI fetch output.
"""
import hashlib,json,pathlib,shlex,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]
WORK=ROOT/'.tools/auto-setup'; ASSETS=ROOT/'engine/kali-app/src/main/assets/managed'
D=['docker','--host=unix:///var/run/docker.sock']
def run(*args): subprocess.run([*D,*args],check=True)
profile=json.loads((WORK/'oci-profile.json').read_text())
assert len(profile['layers'])==6
run('exec','kp-kali-build','mkdir','-p','/payload/kp')
for name in ['init','configure-root.sh']:
 run('cp',str(ROOT/'tools/guest'/name),'kp-kali-build:/payload/'+('init' if name=='init' else 'kp/'+name))
(WORK/'profile-digest').write_text(profile['manifestDigest'].split(':')[1]+'\n')
run('cp',str(WORK/'profile-digest'),'kp-kali-build:/payload/kp/profile-digest')
for i,layer in enumerate(profile['layers'],1):
 (WORK/f'layer-{i}').write_text('drive=/dev/vd'+chr(ord('a')+i)+'\n')
 for prefix,cleanup in [('whiteout',False),('cleanup',True)]:
  lines=['#!/bin/sh','set -eu']
  for w in layer['whiteouts']:
   p=pathlib.PurePosixPath(w['path']); assert not p.is_absolute() and '..' not in p.parts
   if cleanup:p=(p.parent/('.wh.'+p.name)) if w['type']=='remove' else p/'.wh..wh..opq'
   path=shlex.quote('/'+str(p))
   if not cleanup and w['type']=='opaque':
    lines.append('chroot /newroot /.kp-tools/busybox find '+path+' -mindepth 1 -maxdepth 1 -exec /.kp-tools/busybox rm -rf -- {} \\;')
   else:lines.append('chroot /newroot /.kp-tools/busybox rm -rf -- '+path)
  (WORK/f'{prefix}-{i}.sh').write_text('\n'.join(lines)+'\n')
 for name in [f'layer-{i}',f'whiteout-{i}.sh',f'cleanup-{i}.sh']:
  run('cp',str(WORK/name),'kp-kali-build:/payload/kp/'+name)
script=r'''set -eu
cd /payload
mkdir -p bin sbin usr/bin usr/sbin dev proc sys run tmp newroot lib/modules
cp /bin/busybox bin/busybox
for command in $(bin/busybox --list); do [ -e bin/$command ] || ln -s busybox bin/$command; done
copybin() {
 binary=$(command -v "$1")
 cp --parents "$binary" /payload
 ldd "$binary" | awk '/=> \/|^\s*\// {for(i=1;i<=NF;i++) if ($i ~ /^\//) print $i}' | while read -r lib; do cp -L --parents "$lib" /payload; done
}
for b in mke2fs e2fsck blkid; do copybin "$b"; done
# ELF loader is reported without an => token on some ldd versions.
mkdir -p lib64
cp -L /lib64/ld-linux-x86-64.so.2 lib64/
cp -a /lib/modules/6.1.0-54-amd64 lib/modules/
chmod 755 init kp/configure-root.sh
find . -print0 | cpio --null -o --format=newc --owner=0:0 2>/work/cpio.log | gzip -1 > /work/initrd.gz
cp /boot/vmlinuz-6.1.0-54-amd64 /work/vmlinuz
'''
(WORK/'build-initrd.sh').write_text(script)
run('exec','kp-kali-build','sh','/work/build-initrd.sh')
ASSETS.mkdir(parents=True,exist_ok=True)
for name,key in [('vmlinuz','kernelSha256'),('initrd.gz','initrdSha256')]:
 data=(WORK/name).read_bytes(); profile[key]=hashlib.sha256(data).hexdigest();(ASSETS/('initrd.bin' if name=='initrd.gz' else name)).write_bytes(data)
(ASSETS/'initrd.gz').unlink(missing_ok=True)
profile['minimumFreeBytes']=18*1024**3
profile['logicalVolumeBytes']=32*1024**3
profile['kernel']='Debian Linux 6.1.0-54-amd64; Kali userspace from Kasm Technologies'
(ASSETS/'profile.json').write_text(json.dumps(profile,indent=2)+'\n')
print('Payload SHA256 verified and staged. Sizes:',[(p.name,p.stat().st_size) for p in ASSETS.iterdir()])
