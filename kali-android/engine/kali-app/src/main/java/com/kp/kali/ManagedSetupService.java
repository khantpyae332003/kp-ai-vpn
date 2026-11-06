package com.kp.kali;

import android.app.*;
import android.content.*;
import android.os.*;
import com.kp.kali.core.*;
import org.json.JSONObject;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;

/** Foreground, process-owned transfer. Retrying retains validated cache and partial bodies. */
public final class ManagedSetupService extends Service {
    static volatile boolean busy,prepared;
    static volatile String status="Preparing Kali desktop…",error="";
    static volatile long done,total;
    static volatile ManagedVolume volume;
    static volatile File kernel,initrd;
    static volatile List<File> layers=Collections.emptyList();
    private static final AtomicBoolean cancelled=new AtomicBoolean();
    private static final String CHANNEL="managed-setup";
    private long notifiedAt;
    @Override public android.os.IBinder onBind(Intent intent){return null;}
    @Override public int onStartCommand(Intent intent,int flags,int id){
        if(intent!=null&&"cancel".equals(intent.getAction())){cancelled.set(true);return START_NOT_STICKY;}
        if(busy||prepared){if(!busy)stopSelf();return START_NOT_STICKY;}
        busy=true;cancelled.set(false);error="";
        getSystemService(NotificationManager.class).createNotificationChannel(new NotificationChannel(CHANNEL,"Kali desktop preparation",NotificationManager.IMPORTANCE_LOW));
        startForeground(71,notification());
        new Thread(()->{try{prepare();prepared=true;status="Ready to boot Kali desktop";}catch(Exception e){error=cancelled.get()?"Preparation cancelled. Open the app to resume.":safeError(e);status=error;}finally{busy=false;stopForeground(true);stopSelf();}},"Kali-managed-setup").start();
        return START_NOT_STICKY;
    }
    private Notification notification(){
        PendingIntent open=PendingIntent.getActivity(this,0,new Intent(this,BootstrapActivity.class),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
        PendingIntent cancel=PendingIntent.getService(this,1,new Intent(this,ManagedSetupService.class).setAction("cancel"),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder b=new Notification.Builder(this,CHANNEL).setSmallIcon(android.R.drawable.stat_sys_download).setContentTitle("Preparing Kali desktop").setContentText(status).setContentIntent(open).setOngoing(true).addAction(new Notification.Action.Builder(null,"Cancel",cancel).build());
        if(total>0)b.setProgress(1000,(int)Math.min(1000,done*1000/total),false);else b.setProgress(0,0,true);
        return b.build();
    }
    private void update(String text){status=text;long now=SystemClock.elapsedRealtime();if(now-notifiedAt>700){getSystemService(NotificationManager.class).notify(71,notification());notifiedAt=now;}}
    private void checkCancel()throws InterruptedIOException{if(cancelled.get())throw new InterruptedIOException("Preparation cancelled");}
    private void prepare()throws Exception{
        ActivityManager.MemoryInfo memory=new ActivityManager.MemoryInfo();getSystemService(ActivityManager.class).getMemoryInfo(memory);
        if(memory.totalMem<4L*1024*1024*1024)throw new IOException("Kali desktop needs a phone with at least 4 GiB RAM (2048 MiB guest).");
        KaliRuntime.verifyBootAssets(this);
        ManagedProfile profile=new ManagedProfile(this);File dir=new File(getFilesDir(),"managed");if(!dir.isDirectory()&&!dir.mkdirs())throw new IOException("Cannot create private managed storage");
        volume=ManagedVolume.createOrOpen(dir,ManagedProfile.MANIFEST,32L*1024*1024*1024);
        File reservation=new File(dir,"storage-checked");
        if(!volume.isReady()&&!reservation.exists()) {
            if(new StatFs(dir.getPath()).getAvailableBytes()<18L*1024*1024*1024)throw new IOException("Free at least 18 GiB of app storage for the first Kali installation, then retry.");
            try(FileOutputStream checked=new FileOutputStream(reservation)){checked.write(1);checked.getFD().sync();}
        }
        File assets=new File(getFilesDir(),"managed-assets");if(!assets.isDirectory()&&!assets.mkdirs())throw new IOException("Cannot create boot asset storage");
        kernel=copyAsset("vmlinuz",profile.kernelHash,assets);initrd=copyAsset("initrd.bin",profile.initrdHash,assets);
        if(volume.isReady()){layers=Collections.emptyList();return;}
        File blobs=new File(dir,"blobs");if(!blobs.isDirectory()&&!blobs.mkdirs())throw new IOException("Cannot create image cache");
        total=0;done=0;for(ManagedProfile.Layer layer:profile.layers)total+=layer.size;
        List<File> result=new ArrayList<>();long completed=0;VerifiedTransfer transfer=new VerifiedTransfer();
        for(int index=0;index<profile.layers.size();index++){
            checkCancel();ManagedProfile.Layer layer=profile.layers.get(index);final long base=completed;final int number=index+1;
            URL url=new URL("https://registry-1.docker.io/v2/"+profile.repository+"/blobs/sha256:"+layer.hash);
            transfer.fetch(url,layer.size,layer.hash,new File(blobs,layer.hash),u->Collections.singletonMap("Authorization","Bearer "+token(profile.repository)),ManagedSetupService::allowed,cancelled::get,(n,t)->{done=base+n;update("Downloading layer "+number+" / 6 · "+done/(1024*1024)+" / "+total/(1024*1024)+" MiB");});
            result.add(new File(blobs,layer.hash));completed+=layer.size;
        }
        checkCancel();layers=Collections.unmodifiableList(result);
    }
    private static boolean allowed(URL url){return "https".equals(url.getProtocol())&&url.getUserInfo()==null&&(url.getPort()==-1||url.getPort()==443)&&Arrays.asList("registry-1.docker.io","production.cloudfront.docker.com").contains(url.getHost().toLowerCase(Locale.ROOT));}
    private String accessToken="";private long tokenUntil;
    private String token(String repository)throws IOException{
        if(SystemClock.elapsedRealtime()<tokenUntil)return accessToken;
        checkCancel();HttpsURLConnectionHolder holder=new HttpsURLConnectionHolder(new URL("https://auth.docker.io/token?service=registry.docker.io&scope=repository:"+repository+":pull"));
        HttpURLConnection c=holder.connection;
        try{if(c.getResponseCode()!=200)throw new IOException("Registry authorization unavailable. Check your connection and retry.");ByteArrayOutputStream out=new ByteArrayOutputStream();try(InputStream in=c.getInputStream()){byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1){checkCancel();if(out.size()+n>65536)throw new IOException("Invalid registry authorization response");out.write(b,0,n);}}try{JSONObject json=new JSONObject(out.toString("UTF-8"));accessToken=json.getString("token");if(accessToken.isEmpty()||accessToken.indexOf('\n')>=0||accessToken.indexOf('\r')>=0)throw new IOException("Invalid registry token");tokenUntil=SystemClock.elapsedRealtime()+Math.max(1,Math.min(240,json.optInt("expires_in",300)-30))*1000L;return accessToken;}catch(org.json.JSONException e){throw new IOException("Invalid registry authorization response");}}
        finally{c.disconnect();}
    }
    private static final class HttpsURLConnectionHolder {final HttpURLConnection connection;HttpsURLConnectionHolder(URL url)throws IOException{connection=(HttpURLConnection)url.openConnection();connection.setInstanceFollowRedirects(false);connection.setConnectTimeout(20000);connection.setReadTimeout(20000);}}
    private File copyAsset(String name,String expected,File dir)throws Exception{
        checkCancel();File target=new File(dir,name);MessageDigest md=MessageDigest.getInstance("SHA-256");File stage=File.createTempFile("boot-",".tmp",dir);
        try{try(InputStream in=getAssets().open("managed/"+name);FileOutputStream out=new FileOutputStream(stage)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1){checkCancel();md.update(b,0,n);out.write(b,0,n);}out.getFD().sync();}
            StringBuilder hash=new StringBuilder();for(byte b:md.digest())hash.append(String.format(Locale.ROOT,"%02x",b&255));if(!expected.equals(hash.toString()))throw new IOException("Bundled boot payload integrity mismatch. Reinstall this build.");checkCancel();Files.move(stage.toPath(),target.toPath(),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);return target;
        }finally{Files.deleteIfExists(stage.toPath());}
    }
    private static String safeError(Exception e){String m=e.getMessage();if(e instanceof IOException&&m!=null&&!m.contains("http")&&!m.contains("Bearer"))return m;return "Kali preparation failed. Check connection and storage, then retry. Existing guest data is retained.";}
}
