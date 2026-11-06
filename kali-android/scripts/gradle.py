#!/usr/bin/env python3
import os,pathlib,subprocess,sys,urllib.parse
r=pathlib.Path(__file__).resolve().parents[1]; t=r/'.tools'
env=os.environ.copy();env['JAVA_HOME']=str(t/'jdk-17.0.17+10');env['ANDROID_HOME']=str(t/'android-sdk');env['ANDROID_SDK_ROOT']=env['ANDROID_HOME'];env['GRADLE_USER_HOME']=str(t/'gradle-home')
args=[str(t/'gradle-7.6.4/bin/gradle'),'--no-daemon','--max-workers=4','-Djavax.net.ssl.trustStore='+str(t/'java-cacerts'),'-Djavax.net.ssl.trustStorePassword=changeit']
p=urllib.parse.urlparse(env.get('HTTPS_PROXY',''))
if p.hostname:
 for scheme in ('http','https'):
  args+=['-D'+scheme+'.proxyHost='+p.hostname,'-D'+scheme+'.proxyPort='+str(p.port or 80)]
args+=sys.argv[1:]
sys.exit(subprocess.call(args,cwd=r/'engine',env=env))
