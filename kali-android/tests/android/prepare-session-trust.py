#!/usr/bin/env python3
"""Session-proxy trust ONLY for the dedicated userdebug kali-auto-test emulator.
No production app/root/TLS changes. Restores adbd to the normal shell UID before testing.
"""
from pathlib import Path
import subprocess,time,shlex
root=Path(__file__).resolve().parents[2];adb=root/'.tools/android-sdk/platform-tools/adb'
def run(*a,timeout=45):
 if a[:3]==('shell','sh','-c'):a=(*a[:3],shlex.quote(a[3]))
 p=subprocess.run([str(adb),'-s','emulator-5554',*a],capture_output=True,timeout=timeout)
 if p.returncode:raise RuntimeError(p.stderr.decode()+p.stdout.decode())
 return p.stdout.decode().strip()
assert run('emu','avd','name').splitlines()[0].strip()=='kali-auto-test'
assert run('shell','getprop','ro.kernel.qemu')=='1'
run('wait-for-device',timeout=420)
print(run('root'),flush=True);run('wait-for-device',timeout=45)
assert run('shell','id','-u')=='0'
run('shell','mkdir','-p','/data/local/tmp/kp-test-cacerts')
run('shell','sh','-c','cp /system/etc/security/cacerts/* /data/local/tmp/kp-test-cacerts/')
names=[]
for ca in sorted(Path('/usr/local/share/ca-certificates').glob('*.crt')):
 h=subprocess.check_output(['openssl','x509','-in',str(ca),'-subject_hash_old','-noout'],text=True).strip();name=h+'.0';names.append(name)
 run('push',str(ca),'/data/local/tmp/kp-test-cacerts/'+name)
run('shell','chmod','755','/data/local/tmp/kp-test-cacerts')
run('shell','sh','-c','chmod 644 /data/local/tmp/kp-test-cacerts/*; chcon -R u:object_r:system_file:s0 /data/local/tmp/kp-test-cacerts')
# Bind test trust into the zygote namespace; original verified OS partitions stay unchanged.
for _ in range(60):
 raw=run('shell','sh','-c','pidof zygote64 || true');pid=raw.split()[0] if raw else ''
 if pid:break
 time.sleep(1)
assert pid.isdigit()
print('Binding session trust to isolated emulator zygote namespace',pid,flush=True)
run('shell','nsenter','-t',pid,'-m','--','mount','--bind','/data/local/tmp/kp-test-cacerts','/system/etc/security/cacerts')
for name in names:run('shell','ls','/proc/'+pid+'/root/system/etc/security/cacerts/'+name)
print(run('unroot'),flush=True);run('wait-for-device',timeout=45)
assert run('shell','id','-u')=='2000'
print('Session CA trust prepared in disposable OS namespace; adbd returned to unrooted shell. Exact APK unchanged.',flush=True)
