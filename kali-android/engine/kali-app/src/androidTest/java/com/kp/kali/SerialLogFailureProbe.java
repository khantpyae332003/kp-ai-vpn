package com.kp.kali;

import android.net.LocalServerSocket;
import android.net.LocalSocket;
import android.net.LocalSocketAddress;
import com.kp.kali.core.BootstrapProtocol;
import java.io.*;
import java.lang.reflect.Field;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.CountDownLatch;

/** Headless transport test in a separate process. No guest socket, volume or READY messages. */
public final class SerialLogFailureProbe {
    private static void field(String name,Object value)throws Exception {
        Field f=KaliRuntime.class.getDeclaredField(name);f.setAccessible(true);f.set(null,value);
    }
    public static void main(String[] args) {
        File dir=null;LocalSocket listener=null;LocalServerSocket server=null;
        CountDownLatch release=new CountDownLatch(1);int status=2;
        try {
            if(args.length!=1||!args[0].matches("/data/(user/0|data)/com\\.kp\\.kali"))throw new IllegalArgumentException("Unexpected app directory");
            dir=new File(args[0]+"/cache/log-failure-fixture-"+System.nanoTime());
            if(!dir.mkdir())throw new IOException("Cannot create isolated fixture");
            File socket=new File(dir,"serial"),badLog=new File(dir,"log-is-a-directory");
            if(!badLog.mkdir())throw new IOException("Cannot create unwritable log destination");
            BootstrapProtocol protocol=new BootstrapProtocol(ManagedProfile.MANIFEST);
            field("managedArguments",new String[0]);field("protocol",protocol);field("serialPath",socket);field("serialLog",badLog);
            listener=new LocalSocket();listener.bind(new LocalSocketAddress(socket.getAbsolutePath(),LocalSocketAddress.Namespace.FILESYSTEM));
            server=new LocalServerSocket(listener.getFileDescriptor());final LocalServerSocket srv=server;
            Thread writer=new Thread(()->{
                try(LocalSocket peer=srv.accept()) {
                    peer.getOutputStream().write("KP:PHASE:first phase\nKP:PHASE:after log failure\n".getBytes(StandardCharsets.UTF_8));peer.getOutputStream().flush();release.await();
                }catch(Exception ignored){}
            },"log-failure-fixture-writer");writer.setDaemon(true);writer.start();
            if(!KaliRuntime.session.tryStart())throw new AssertionError("Separate fixture session not stopped");
            KaliRuntime.watchStartup();long end=android.os.SystemClock.elapsedRealtime()+7000;
            while(android.os.SystemClock.elapsedRealtime()<end&&!"after log failure".equals(protocol.phase()))Thread.sleep(100);
            if(!"after log failure".equals(protocol.phase()))throw new AssertionError("Diagnostic log failure discarded production serial messages");
            if(protocol.isReady())throw new AssertionError("Phase-only fixture must never simulate guest readiness");
            System.out.println("KP_TEST_LOG_FAILURE=PASS phases received despite unwritable log; no guest readiness simulated");status=0;
        }catch(Throwable e){System.out.println("KP_TEST_LOG_FAILURE=FAIL "+e);}
        finally {
            release.countDown();KaliRuntime.session.failed("Separate transport fixture ended");
            try{if(server!=null)server.close();}catch(IOException ignored){}
            try{if(listener!=null)listener.close();}catch(IOException ignored){}
            if(dir!=null){File[] files=dir.listFiles();if(files!=null)for(File file:files)file.delete();dir.delete();}
        }
        System.exit(status);
    }
}
