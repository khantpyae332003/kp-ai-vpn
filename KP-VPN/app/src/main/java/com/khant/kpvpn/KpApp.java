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
 ProfileStore store;GoBackend backend;
 volatile String state="DOWN",activeId="",error="";
 volatile long rx=0,tx=0;
 WeakReference<MainActivity> screen=new WeakReference<>(null);
 final Tunnel tunnel=new Tunnel(){
  public String getName(){return "kpvpn";}
  public void onStateChange(Tunnel.State s){state=s==Tunnel.State.UP?"UP":"DOWN";if(s==Tunnel.State.DOWN){activeId="";rx=tx=0;}emit();}
 };
 @Override public void onCreate(){super.onCreate();try{store=new ProfileStore(this);}catch(Exception e){error="သိမ်းထားသော config ကို ဖတ်မရပါ။ App data ကို မဖျက်ဘဲ အကူအညီရယူပါ။";}}
 String snapshot(){
  JSONObject j=new JSONObject();try{j.put("profiles",store==null?new JSONArray():store.metadata()).put("state",state).put("activeId",activeId).put("error",error).put("rx",rx).put("tx",tx).put("ready",store!=null);}catch(Exception ignored){}return j.toString();
 }
 void emit(){main.post(()->{MainActivity a=screen.get();if(a!=null)a.render();});}
 void message(String text){main.post(()->{MainActivity a=screen.get();if(a!=null)a.message(text);});}
 void fail(String text){error=text;message(text);emit();}
}
