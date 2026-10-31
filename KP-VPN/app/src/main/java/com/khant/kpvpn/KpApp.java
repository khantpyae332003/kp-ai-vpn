package com.khant.kpvpn;

import android.app.Application;
import android.os.Handler;
import android.os.Looper;
import com.wireguard.android.backend.*;
import org.json.*;
import java.lang.ref.WeakReference;
import java.util.concurrent.*;

public final class KpApp extends Application {
 final ExecutorService work=Executors.newSingleThreadExecutor();
 final Handler main=new Handler(Looper.getMainLooper());
 volatile ProfileStore store;GoBackend backend;
 volatile String profileSnapshot="[]";
 volatile String state="DOWN",activeId="",error="";
 volatile long rx=0,tx=0;
 WeakReference<MainActivity> screen=new WeakReference<>(null);
 final Tunnel tunnel=new Tunnel(){
  public String getName(){return "kpvpn";}
  public void onStateChange(Tunnel.State s){
   boolean externalDown=s==Tunnel.State.DOWN&&state.equals("UP");
   state=s==Tunnel.State.UP?"UP":"DOWN";
   if(s==Tunnel.State.DOWN){activeId="";rx=tx=0;}
   if(externalDown)main.post(()->{if(state.equals("DOWN"))stopService(new android.content.Intent(KpApp.this,TunnelService.class));});
   emit();
  }
 };
 @Override public void onCreate(){super.onCreate();work.execute(()->{
  try{store=new ProfileStore(this);refreshProfiles();}catch(Exception e){store=null;error="သိမ်းထားသော config ကို ဖတ်မရပါ။ App data ကို မဖျက်ဘဲ အကူအညီရယူပါ။";}emit();
 });}
 // Called only on the serial worker after a profile mutation.
 void refreshProfiles()throws JSONException {profileSnapshot=store.metadata().toString();}
 String snapshot(){
  return "{\"profiles\":"+profileSnapshot+",\"state\":"+JSONObject.quote(state)+",\"activeId\":"+JSONObject.quote(activeId)+",\"error\":"+JSONObject.quote(error)+",\"rx\":"+rx+",\"tx\":"+tx+",\"ready\":"+(store!=null)+"}";
 }
 void emit(){main.post(()->{MainActivity a=screen.get();if(a!=null)a.render();});}
 void message(String text){main.post(()->{MainActivity a=screen.get();if(a!=null)a.message(text);});}
 void fail(String text){error=text;message(text);emit();}
}
