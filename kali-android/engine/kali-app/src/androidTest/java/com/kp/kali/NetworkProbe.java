package com.kp.kali;
import android.app.Instrumentation;import android.os.Bundle;
import java.net.*;import java.io.*;import java.lang.reflect.*;
/** Test-only diagnostic: never emits bearer tokens, signed URLs, paths or query strings. */
public final class NetworkProbe extends Instrumentation {
 @Override public void onCreate(Bundle args){super.onCreate(args);start();}
 private void report(String value){Bundle b=new Bundle();b.putString("stream",value+"\n");sendStatus(0,b);}
 @Override public void onStart(){
  try{
   report("app_uid="+android.os.Process.myUid());
   ManagedProfile profile=new ManagedProfile(getTargetContext());
   ManagedSetupService service=new ManagedSetupService();Method m=ManagedSetupService.class.getDeclaredMethod("token",String.class);m.setAccessible(true);
   String token;
   try{token=(String)m.invoke(service,profile.repository);report("auth.docker.io token request succeeded");}
   catch(InvocationTargetException e){report("TOKEN FAILURE CLASS "+e.getCause().getClass().getName());finish(1,new Bundle());return;}
   URL url=new URL("https://registry-1.docker.io/v2/"+profile.repository+"/blobs/sha256:"+profile.layers.get(0).hash);
   for(int n=0;n<6;n++){
    HttpURLConnection c=(HttpURLConnection)url.openConnection();c.setInstanceFollowRedirects(false);c.setConnectTimeout(20000);c.setReadTimeout(20000);
    if(url.getHost().equals("registry-1.docker.io"))c.setRequestProperty("Authorization","Bearer "+token);
    try{
     int status=c.getResponseCode();report("host="+url.getHost()+" status="+status);
     if(status>=300&&status<400){URL next=new URL(url,c.getHeaderField("Location"));report("redirect_host="+next.getHost());if(!next.getProtocol().equals("https"))throw new IOException("Non-TLS redirect");url=next;continue;}
     if(status==200||status==206){try(InputStream in=c.getInputStream()){byte[] buf=new byte[32];report("readable_bytes="+in.read(buf));}finish(0,new Bundle());return;}
     finish(1,new Bundle());return;
    }finally{c.disconnect();}
   }
  }catch(Throwable e){report("FAILURE CLASS "+e.getClass().getName());}
  finish(1,new Bundle());
 }
}
