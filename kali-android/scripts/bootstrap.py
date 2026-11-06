#!/usr/bin/env python3
"""Linux x86_64 build prerequisites, verified against toolchain-lock.json."""
import argparse,hashlib,json,os,pathlib,shutil,subprocess,tarfile,urllib.request,zipfile
root=pathlib.Path(__file__).resolve().parents[1]
tools=root/'.tools';downloads=tools/'downloads';downloads.mkdir(parents=True,exist_ok=True)
lock=json.loads((root/'toolchain-lock.json').read_text())
parser=argparse.ArgumentParser();parser.add_argument('--accept-sdk-license',action='store_true',help='Accept the Android SDK license provided by Google for this build machine');args=parser.parse_args()

def fetch(name,spec):
    p=downloads/(name+('.zip' if spec['url'].endswith(('.zip','.apk')) else '.tar.gz'))
    algo='sha256' if 'sha256' in spec else 'sha1'
    if not p.exists() or hashlib.new(algo,p.read_bytes()).hexdigest()!=spec[algo]:
        stage=p.with_suffix('.download');urllib.request.urlretrieve(spec['url'],stage)
        if hashlib.new(algo,stage.read_bytes()).hexdigest()!=spec[algo]:raise RuntimeError('Checksum mismatch: '+name)
        stage.replace(p)
    return p

for name,destination in [('jdk',tools/'jdk-17.0.17+10'),('gradle',tools/'gradle-7.6.4'),('platform',tools/'android-sdk/platforms/android-33'),('build-tools',tools/'android-sdk/build-tools/33.0.2')]:
    if destination.exists():continue
    p=fetch(name,lock[name]);stage=tools/('extract-'+name);stage.mkdir(exist_ok=True)
    if p.suffix=='.zip':subprocess.run(['unzip','-q',str(p),'-d',str(stage)],check=True)
    else:
        with tarfile.open(p) as t:t.extractall(stage,filter='data')
    entries=list(stage.iterdir());assert len(entries)==1,entries
    destination.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(entries[0]),destination);stage.rmdir()

# Use the JDK's standard trust roots plus the cloud machine's installed proxy roots.
trust=tools/'java-cacerts'
if not trust.exists():
    shutil.copyfile(tools/'jdk-17.0.17+10/lib/security/cacerts',trust)
    for cert in pathlib.Path('/usr/local/share/ca-certificates').glob('*.crt'):
        subprocess.run([str(tools/'jdk-17.0.17+10/bin/keytool'),'-importcert','-noprompt','-keystore',str(trust),'-storepass','changeit','-alias',cert.stem,'-file',str(cert)],check=True,stdout=subprocess.DEVNULL)
license_dir=tools/'android-sdk/licenses'
if not (license_dir/'android-sdk-license').exists():
    if not args.accept_sdk_license:raise SystemExit('Read https://developer.android.com/studio/terms and rerun with --accept-sdk-license, or install/accept the SDK through Android Studio.')
    # The same public license identifier written by sdkmanager --licenses, not a credential.
    license_dir.mkdir(exist_ok=True);(license_dir/'android-sdk-license').write_text('8933bad161af4178b1185d1a37fbf41ea5269c55\nd56f5187479451eabf01fb78af6dfcb131a6481e\n24333f8a63b6825ea9c5514f83c2829b004d1fee\n')
(root/'engine/local.properties').write_text('sdk.dir='+str(tools/'android-sdk')+'\n')

apk=fetch('limbo-runtime',lock['runtime'])
keep={'bios-256k.bin','bios.bin','vgabios-stdvga.bin','efi-e1000.rom','kvmvapic.bin','linuxboot.bin','linuxboot_dma.bin','README'}
with zipfile.ZipFile(apk) as z:
    for n in z.namelist():
        if n.endswith('/'):continue
        if n.startswith(('lib/arm64-v8a/','lib/x86_64/')):
            dest=root/'engine/limbo-android-lib/src/main/jniLibs'/pathlib.Path(n).relative_to('lib')
        elif n.startswith('assets/'):
            rel=pathlib.Path(n).relative_to('assets')
            if str(rel).startswith('roms/') and rel.name not in keep and not str(rel).startswith(('roms/keymaps/','roms/etc/')):continue
            dest=root/'engine/limbo-android-lib/src/main'/n
        else:continue
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(n))
print('Verified build prerequisites and original QEMU runtime installed. Run python3 scripts/gradle.py :kali-core:test :kali-app:assembleDebug')
