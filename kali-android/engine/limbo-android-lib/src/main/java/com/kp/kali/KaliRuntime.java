// SPDX-License-Identifier: GPL-2.0-or-later
package com.kp.kali;

import android.app.Activity;
import android.content.Context;
import android.net.LocalSocket;
import android.net.LocalSocketAddress;
import android.os.SystemClock;
import android.preference.PreferenceManager;
import com.kp.kali.core.*;
import com.max2idea.android.limbo.main.*;
import com.max2idea.android.limbo.files.FileInstaller;
import com.max2idea.android.limbo.log.Logger;
import com.max2idea.android.limbo.machine.KaliMachineBridge;
import org.json.JSONObject;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;

/** Process-owned state survives activity recreation; the foreground service owns native execution. */
public final class KaliRuntime {
    public static final VmSession session=new VmSession();
    public static volatile String diagnostic="";
    private static boolean loaded;
    private KaliRuntime() {}

    public static void prepare(Activity activity, File disk, VmConfig config) throws IOException {
        managedArguments=null;protocol=null;initialize(activity);
        KaliMachineBridge.prepare(disk.getAbsolutePath(),DiskImporter.inspect(disk),config);
    }
    /** Fail before large downloads when the APK cannot perform direct Linux boot. */
    public static void verifyBootAssets(Context context) throws IOException {
        for(String name:new String[]{"bios-256k.bin","linuxboot.bin","linuxboot_dma.bin"}) {
            try(InputStream in=context.getAssets().open("roms/"+name)) {
                if(in.read()<0)throw new IOException("Empty firmware");
            }catch(IOException e){throw new IOException("Required PC boot firmware missing: "+name+". Update this app; guest data is retained.");}
        }
    }
    private static void initialize(Activity activity) throws IOException {
        verifyBootAssets(activity);
        LimboApplication.arch=Config.Arch.x86_64;Config.clientClass=activity.getClass();Config.enableKVM=false;
        Config.enableSoftwareUpdates=false;Config.enableSharedFolder=false;
        Config.storagedir=activity.getFilesDir().getAbsolutePath();
        LimboApplication.setupEnv(activity);
        PreferenceManager.getDefaultSharedPreferences(activity).edit()
            .putBoolean("enableExternalQMP",false).putBoolean("enableQMP",true).putBoolean("enableAaudio",false)
            .putBoolean("AlwaysShowMenuToolbar",true).putBoolean("ShowFullscreen",false).apply();
        new File(LimboApplication.getMachineDir()).mkdirs();
        FileInstaller.installFiles(activity,false);
        // These small trusted ROMs are always refreshed, repairing interrupted/stale cache copies.
        for(String name:new String[]{"bios-256k.bin","linuxboot.bin","linuxboot_dma.bin"}) {
            if(!FileInstaller.installAssetFile(activity,name,LimboApplication.getBasefileDir(),"roms",null)
                ||new File(LimboApplication.getBasefileDir(),name).length()==0)
                throw new IOException("Cannot prepare PC boot firmware: "+name+". Guest data is retained.");
        }
        if(!loaded) {
            for(String lib:new String[]{"compat-limbo","compat-musl","glib-2.0","pixman-1","compat-SDL2-addons","SDL2","compat-SDL2-ext","limbo","qemu-system-x86_64"}) System.loadLibrary(lib);
            loaded=true;
        }
        Logger.setupLogFile("/kali-vm.log");
        LaunchLogs.rotate(new File(Config.logFilePath),new File(activity.getCacheDir(),"kali-vm.previous.log"));
    }
    private static volatile String[] managedArguments;
    private static volatile BootstrapProtocol protocol;
    private static ManagedVolume managedVolume;
    private static File serialPath,serialLog;
    private static volatile boolean serialWatching;
    public static boolean isManaged(){return managedArguments!=null;}
    public static boolean desktopReady(){BootstrapProtocol p=protocol;return p!=null&&p.isReady();}
    public static String[] managedArguments(){String[] a=managedArguments;return a==null?null:a.clone();}
    public static void prepareManaged(Activity activity,ManagedVolume volume,File kernel,File initrd,java.util.List<File> layers,VmConfig config,String digest)throws IOException{
        if(session.state()==VmSession.State.STARTING||session.state()==VmSession.State.RUNNING||session.state()==VmSession.State.STOPPING||session.state()==VmSession.State.EXITING)throw new IOException("A guest is already active");
        initialize(activity);managedVolume=volume;protocol=new BootstrapProtocol(digest);
        serialPath=new File(activity.getFilesDir(),"managed-serial.sock");serialLog=new File(activity.getCacheDir(),"managed-serial.log");
        java.nio.file.Files.deleteIfExists(serialPath.toPath());
        KaliMachineBridge.prepareManaged(config);
        java.util.ArrayList<String> args=new java.util.ArrayList<>();
        java.util.Collections.addAll(args,"-kernel",kernel.getAbsolutePath(),"-initrd",initrd.getAbsolutePath(),"-append",
            "console=ttyS0 console=tty0 root=/dev/vda rw kp.uuid="+volume.uuid+" kp.profile="+digest.substring(7)+" kp.format="+(volume.isReady()?"0":"1"),
            "-serial","unix:"+serialPath.getAbsolutePath()+",server,nowait","-drive","file="+volume.disk.getAbsolutePath()+",format=raw,if=virtio,index=0");
        int index=1;for(File layer:layers){args.add("-drive");args.add("file="+layer.getAbsolutePath()+",format=raw,if=virtio,index="+(index++)+",readonly=on");}
        managedArguments=args.toArray(new String[0]);diagnostic="Booting Kali kernel… first installation can take a long time.";
    }
    private static synchronized void watchManagedSerial(){
        if(serialWatching)return;serialWatching=true;
        new Thread(()->{
            try{
                while(session.state()==VmSession.State.STARTING||session.state()==VmSession.State.RUNNING){
                    try(LocalSocket socket=new LocalSocket()){
                        socket.connect(new LocalSocketAddress(serialPath.getAbsolutePath(),LocalSocketAddress.Namespace.FILESYSTEM));
                        // Keep the private guest stream connected across idle boot/install phases.
                        // Android LocalSocket may report receive timeouts as a plain IOException.
                        socket.setSoTimeout(0);InputStream in=socket.getInputStream();StringBuilder line=new StringBuilder();boolean oversized=false;
                        while(session.state()==VmSession.State.STARTING||session.state()==VmSession.State.RUNNING){
                            int value=in.read();if(value<0)break;
                            if(value=='\n'){
                                String text=line.toString();if(text.endsWith("\r"))text=text.substring(0,text.length()-1);
                                // Cache diagnostics must not discard one-shot guest protocol messages.
                                try{LaunchLogs.append(serialLog,text+"\n",1024*1024);}
                                catch(IOException e){android.util.Log.w("KaliRuntime","Guest diagnostic cache unavailable",e);}
                                BootstrapProtocol.Event event=protocol.accept(oversized&&text.startsWith("KP:")?"KP:PHASE:"+new String(new char[1100]).replace('\0','x'):text);
                                if(event==BootstrapProtocol.Event.PHASE)diagnostic="Kali: "+protocol.phase();
                                if(event==BootstrapProtocol.Event.ERROR){diagnostic=protocol.error()+". Open diagnostics from Advanced.";}
                                if(event==BootstrapProtocol.Event.READY){try{managedVolume.markReady();session.running();diagnostic="Kali desktop ready";}catch(IOException e){diagnostic="Desktop started, but its completion receipt could not be saved. Guest data retained.";}}
                                line.setLength(0);oversized=false;
                            }else if(line.length()<1024)line.append((char)value);else oversized=true;
                        }
                    }catch(IOException e){SystemClock.sleep(500);}
                }
            }finally{serialWatching=false;}
        },"Kali-guest-serial").start();
    }
    public static String command(String execute) throws Exception {
        try(LocalSocket socket=new LocalSocket()) {
            socket.connect(new LocalSocketAddress(LimboApplication.getLocalQMPSocketPath(),LocalSocketAddress.Namespace.FILESYSTEM));
            socket.setSoTimeout(1500);
            BufferedReader in=new BufferedReader(new InputStreamReader(socket.getInputStream(),StandardCharsets.UTF_8));
            BufferedWriter out=new BufferedWriter(new OutputStreamWriter(socket.getOutputStream(),StandardCharsets.UTF_8));
            String greeting=in.readLine();if(greeting==null||!new JSONObject(greeting).has("QMP"))throw new IOException("No QMP greeting");
            send(out,"qmp_capabilities",1);receive(in,1);send(out,execute,2);return receive(in,2).toString();
        }
    }
    private static void send(BufferedWriter out,String command,int id) throws Exception {
        out.write(new JSONObject().put("execute",command).put("id",id).toString());out.write('\n');out.flush();
    }
    private static JSONObject receive(BufferedReader in,int id) throws Exception {
        for(int n=0;n<100;n++) {String line=in.readLine();if(line==null)throw new EOFException("VM control connection closed");
            JSONObject json=new JSONObject(line);if(json.optInt("id",-1)==id){if(json.has("error"))throw new IOException(json.get("error").toString());return json;}}
        throw new IOException("No matching VM control response");
    }
    public static void watchStartup() {
        if(managedArguments!=null){watchManagedSerial();return;}
        new Thread(()->{
            for(int n=0;n<30&&session.state()==VmSession.State.STARTING;n++) {
                try {JSONObject response=new JSONObject(command("query-status"));
                    if(response.getJSONObject("return").getBoolean("running")){session.running();diagnostic="Guest CPU is running. Kali boot may take several minutes.";return;}}
                catch(Exception ignored) {}
                SystemClock.sleep(1000);
            }
            if(session.state()==VmSession.State.STARTING)diagnostic="Still starting. Use Force stop if the guest does not appear; verify BIOS amd64 image compatibility.";
        },"Kali-readiness").start();
    }
    public static void requestShutdown() {
        if(!session.requestShutdown(SystemClock.elapsedRealtime()))return;
        new Thread(()->{try{command("system_powerdown");diagnostic="Shutdown requested. Wait for guest power-off; disk is retained.";}
            catch(Exception e){diagnostic="Guest shutdown request failed. Use the guest shutdown menu or confirmed Force stop.";}},"Kali-shutdown").start();
    }
    public static void forceStop(boolean confirmed) {
        if(!session.confirmForceStop(confirmed,SystemClock.elapsedRealtime()))return;
        // QEMU may be stuck in native display/cleanup code and unable to service QMP. Only an
        // explicitly confirmed force stop arms this watchdog, and it can terminate only this app.
        new Thread(()->{
            SystemClock.sleep(5100);
            if(session.needsProcessTermination(SystemClock.elapsedRealtime())) {
                LimboApplication.getInstance().getSharedPreferences("kali",0).edit()
                    .putString("last_result","VM force-stopped after native timeout. Disk file retained; check guest filesystem before reuse.").commit();
                android.os.Process.killProcess(android.os.Process.myPid());
            }
        },"Kali-force-watchdog").start();
        new Thread(()->{try{command("quit");}catch(Exception ignored){}},"Kali-force-stop").start();
    }
    public static void onExit(String result) {
        boolean error=result==null||!result.equals("VM shutdown");
        String text=error?"VM exited: "+String.valueOf(result):"VM stopped. Disk retained.";
        LimboApplication.getInstance().getSharedPreferences("kali",0).edit().putString("last_result",text).commit();
        session.finishing(text);diagnostic=text+" Closing the engine process; reopen the app to start again.";
    }
    public static void startLogging() {
        final File log=new File(LimboApplication.getInstance().getCacheDir(),"kali-vm.log");
        new Thread(()->{
            java.lang.Process process=null;
            try {
                process=new ProcessBuilder("logcat","--pid="+android.os.Process.myPid(),"-v","threadtime","*:V").redirectErrorStream(true).start();
                try(BufferedReader reader=new BufferedReader(new InputStreamReader(process.getInputStream(),StandardCharsets.UTF_8))) {
                    String line;while((line=reader.readLine())!=null)LaunchLogs.append(log,line+"\n",1024*1024);
                }
            }catch(IOException e){android.util.Log.w("Kali","Cannot capture VM diagnostics",e);}
            finally {if(process!=null)process.destroy();}
        },"Kali-log-capture").start();
    }
    public static String readDiagnostics(Context context) {
        StringBuilder text=new StringBuilder(context.getSharedPreferences("kali",0).getString("last_result","No VM launch recorded.")).append("\n\n");
        for(String name:new String[]{"managed-serial.log","kali-vm.log","kali-vm.previous.log"})try {
            text.append(name).append(" (last 64 KiB)\n").append(LaunchLogs.tail(new File(context.getCacheDir(),name),64*1024)).append("\n\n");
        }catch(IOException e){text.append("Cannot read ").append(name).append("\n");}
        // A native exit() may outrun the file logger. Android's app-UID-filtered log buffer can still
        // contain the previous process's error after reopening. Never request other apps' logs.
        int pid=context.getSharedPreferences("kali",0).getInt("last_pid",0);
        if(pid>0) {
            java.lang.Process process=null;java.util.Timer timer=new java.util.Timer(true);
            try {
                process=new ProcessBuilder("logcat","-d","-t","80","--pid="+pid,"-v","brief").redirectErrorStream(true).start();
                final java.lang.Process proc=process;timer.schedule(new java.util.TimerTask(){public void run(){proc.destroy();}},5000);
                text.append("Previous VM process (recent app-only Android log)\n");
                try(InputStream in=process.getInputStream()){byte[] data=new byte[4096];int count,total=0;
                    while((count=in.read(data))>0&&total<64*1024){int n=Math.min(count,64*1024-total);text.append(new String(data,0,n,StandardCharsets.UTF_8));total+=n;}}
            }catch(Exception e){text.append("Android log buffer unavailable; use the preserved log above.\n");}
            finally{timer.cancel();if(process!=null)process.destroy();}
        }
        return text.toString();
    }
}
