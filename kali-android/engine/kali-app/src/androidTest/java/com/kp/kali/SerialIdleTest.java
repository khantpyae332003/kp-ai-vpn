package com.kp.kali;
import android.app.Instrumentation;import android.os.Bundle;import android.net.*;
import com.kp.kali.core.BootstrapProtocol;
import java.io.*;import java.lang.reflect.Field;import java.nio.charset.StandardCharsets;import java.util.concurrent.CountDownLatch;
/** Transport-only fixture: sends a phase after idle, never root/READY and never changes a guest volume. */
public final class SerialIdleTest extends Instrumentation {
 @Override public void onCreate(Bundle b){super.onCreate(b);start();}
 private static void field(String name,Object value)throws Exception{Field f=KaliRuntime.class.getDeclaredField(name);f.setAccessible(true);f.set(null,value);}
 @Override public void onStart(){Bundle result=new Bundle();LocalSocket listener=null;LocalServerSocket server=null;CountDownLatch release=new CountDownLatch(1);
  File path=new File(getTargetContext().getCacheDir(),"idle-fixture-"+System.nanoTime());
  try{
   runOnMainSync(()->{});
   listener=new LocalSocket();listener.bind(new LocalSocketAddress(path.getAbsolutePath(),LocalSocketAddress.Namespace.FILESYSTEM));server=new LocalServerSocket(listener.getFileDescriptor());final LocalServerSocket srv=server;
   BootstrapProtocol protocol=new BootstrapProtocol(ManagedProfile.MANIFEST);
   field("managedArguments",new String[0]);field("protocol",protocol);field("serialPath",path);field("serialLog",new File(getTargetContext().getCacheDir(),"idle-fixture.log"));
   Thread writer=new Thread(()->{try(LocalSocket peer=srv.accept()){
    Thread.sleep(3500);peer.getOutputStream().write("KP:PHASE:after idle\n".getBytes(StandardCharsets.UTF_8));peer.getOutputStream().flush();release.await();
   }catch(Exception ignored){}},"idle-fixture-writer");writer.start();
   if(!KaliRuntime.session.tryStart())throw new AssertionError("Fixture session not stopped");KaliRuntime.watchStartup();
   long end=android.os.SystemClock.elapsedRealtime()+12000;
   while(android.os.SystemClock.elapsedRealtime()<end&&!"after idle".equals(protocol.phase()))Thread.sleep(100);
   if(!"after idle".equals(protocol.phase()))throw new AssertionError("Production serial watcher lost its connection/message across a 3.5-second idle gap");
   if(protocol.isReady())throw new AssertionError("Phase-only fixture must never claim desktop readiness");
   result.putString("stream","PASS production serial watcher retained idle connection and received a phase; no desktop/volume readiness simulated\n");finish(0,result);
  }catch(Throwable e){result.putString("stream","FAIL "+android.util.Log.getStackTraceString(e)+"\n");finish(1,result);}
  finally{release.countDown();KaliRuntime.session.failed("Idle transport fixture ended");try{if(server!=null)server.close();}catch(IOException ignored){}try{if(listener!=null)listener.close();}catch(IOException ignored){}path.delete();}
 }
}
