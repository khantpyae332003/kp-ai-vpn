package com.khant.kpvpn;

import android.app.*;
import android.content.*;
import android.content.pm.ServiceInfo;
import android.os.*;
import com.wireguard.android.backend.*;
import com.wireguard.config.Config;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;

public final class TunnelService extends Service {
 static final String CONNECT="com.khant.kpvpn.CONNECT",DISCONNECT="com.khant.kpvpn.DISCONNECT";
 static final int NOTIFY=77;
 private KpApp app;private final Handler timer=new Handler(Looper.getMainLooper());
 private final Runnable meter=new Runnable(){public void run(){
  app.work.execute(()->{try{if(app.backend!=null&&app.state.equals("UP")){Statistics s=app.backend.getStatistics(app.tunnel);app.rx=s.totalRx();app.tx=s.totalTx();app.emit();}}catch(Exception ignored){}});
  timer.postDelayed(this,3000);
 }};
 @Override public void onCreate(){super.onCreate();app=(KpApp)getApplication();
  NotificationManager nm=getSystemService(NotificationManager.class);
  nm.createNotificationChannel(new NotificationChannel("vpn","VPN connection",NotificationManager.IMPORTANCE_LOW));
  Notification n=notification("ချိတ်ဆက်နေသည်…");
  if(Build.VERSION.SDK_INT>=34)startForeground(NOTIFY,n,ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);else startForeground(NOTIFY,n);
  timer.post(meter);
 }
 private Notification notification(String text){
  PendingIntent open=PendingIntent.getActivity(this,0,new Intent(this,MainActivity.class),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
  PendingIntent stop=PendingIntent.getService(this,1,new Intent(this,TunnelService.class).setAction(DISCONNECT),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
  return new Notification.Builder(this,"vpn").setSmallIcon(com.khant.kpvpn.R.drawable.ic_shield).setContentTitle("KP VPN").setContentText(text).setContentIntent(open).setOngoing(true).addAction(new Notification.Action.Builder(null,"ဖြုတ်မယ်",stop).build()).build();
 }
 @Override public int onStartCommand(Intent intent,int flags,int startId){
  if(intent==null||DISCONNECT.equals(intent.getAction())){disconnect(startId);return START_NOT_STICKY;}
  String id=intent.getStringExtra("id");
  app.work.execute(()->{
   try{
    if(app.store==null||id==null)throw new IllegalStateException();
    app.state="STARTING";app.error="";app.emit();
    if(app.backend==null)app.backend=new GoBackend(app);
    Config cfg=Config.parse(new ByteArrayInputStream(app.store.config(id).getBytes(StandardCharsets.UTF_8)));
    app.backend.setState(app.tunnel,Tunnel.State.UP,cfg);app.activeId=id;app.state="UP";app.emit();
    getSystemService(NotificationManager.class).notify(NOTIFY,notification("Tunnel ဖွင့်ထားသည် · Server အလုပ်လုပ်မှုကို စမ်းသုံးပါ"));
   }catch(Exception e){
    // Never show backend exception text, endpoints or private configuration.
    boolean stillUp=app.backend!=null&&app.backend.getState(app.tunnel)==Tunnel.State.UP;
    app.state=stillUp?"UP":"DOWN";if(!stillUp)app.activeId="";
    app.fail("ချိတ်ဆက်မရပါ။ Config၊ server နဲ့ အင်တာနက်ကို စစ်ပါ။");
    if(!stillUp)stopSelfResult(startId);
   }
  });return START_NOT_STICKY;
 }
 private void disconnect(int startId){app.work.execute(()->{
  try{app.state="STOPPING";app.emit();if(app.backend!=null)app.backend.setState(app.tunnel,Tunnel.State.DOWN,null);app.state="DOWN";app.activeId="";app.rx=app.tx=0;app.emit();stopSelfResult(startId);}
  catch(Exception e){
   boolean up=app.backend!=null&&app.backend.getState(app.tunnel)==Tunnel.State.UP;
   app.state=up?"UP":"DOWN";if(!up){app.activeId="";stopSelfResult(startId);}
   app.fail("VPN ဖြုတ်မရပါ။ Android VPN settings မှ ဖြုတ်ပါ။");
  }
 });}
 @Override public void onDestroy(){timer.removeCallbacksAndMessages(null);app.work.execute(()->{try{if(app.backend!=null)app.backend.setState(app.tunnel,Tunnel.State.DOWN,null);}catch(Exception ignored){}app.emit();});super.onDestroy();}
 @Override public IBinder onBind(Intent i){return null;}
}
