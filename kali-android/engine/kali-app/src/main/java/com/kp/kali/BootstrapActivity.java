package com.kp.kali;

import android.app.*;
import android.content.*;
import android.os.*;
import android.graphics.Color;
import android.view.*;
import android.widget.*;
import com.kp.kali.core.*;

/** Ordinary launch automatically resumes preparation or opens the process-owned desktop. */
public final class BootstrapActivity extends Activity {
    private final Handler handler=new Handler(Looper.getMainLooper());
    private TextView status,detail;private ProgressBar progress;private Button retry,cancel;private boolean opened;
    private final Runnable refresh=new Runnable(){public void run(){render();handler.postDelayed(this,500);}};
    @Override public void onCreate(Bundle state){
        super.onCreate(state);LinearLayout page=new LinearLayout(this);page.setOrientation(LinearLayout.VERTICAL);page.setPadding(32,48,32,32);page.setBackgroundColor(0xff101a28);setContentView(page);
        label(page,"KP / KALI DESKTOP",24);label(page,"Kasm Technologies’ Kali-based desktop · Debian Linux kernel",15);
        label(page,"ပထမအကြိမ် ပြင်ဆင်နေသည် · Automatic setup",18);
        status=label(page,"Preparing…",20);progress=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);progress.setMax(1000);page.addView(progress,new LinearLayout.LayoutParams(-1,-2));detail=label(page,"",15);
        retry=button(page,"Retry / resume",v->{ManagedSetupService.error="";startSetup();});
        cancel=button(page,"Cancel download",v->startService(new Intent(this,ManagedSetupService.class).setAction("cancel")));
        button(page,"Advanced · manual disk & diagnostics",v->startActivity(new Intent(this,MainActivity.class)));
        label(page,"First setup downloads about 4.75 GB and needs at least 18 GiB free storage and 4 GiB RAM. Software emulation and installation can take a long time. Guest files remain private to this app; uninstalling deletes them.",14);
        if(!active()&&!ManagedSetupService.prepared&&ManagedSetupService.error.isEmpty())startSetup();
    }
    private void setText(TextView view,String value){if(!android.text.TextUtils.equals(view.getText(),value))view.setText(value);}
    private TextView label(LinearLayout page,String value,int size){TextView t=new TextView(this);t.setText(value);t.setTextColor(Color.WHITE);t.setTextSize(size);t.setPadding(0,12,0,12);page.addView(t);return t;}
    private Button button(LinearLayout page,String value,View.OnClickListener listener){Button b=new Button(this);b.setText(value);b.setAllCaps(false);b.setOnClickListener(listener);page.addView(b,new LinearLayout.LayoutParams(-1,-2));return b;}
    private void startSetup(){startForegroundService(new Intent(this,ManagedSetupService.class));}
    private boolean active(){VmSession.State s=KaliRuntime.session.state();return s==VmSession.State.STARTING||s==VmSession.State.RUNNING||s==VmSession.State.STOPPING||s==VmSession.State.EXITING;}
    private void render(){
        if(active()){if(!opened&&KaliRuntime.session.state()!=VmSession.State.EXITING){opened=true;startActivity(new Intent(this,KaliRuntime.isManaged()?ManagedDesktopActivity.class:com.max2idea.android.limbo.main.LimboSDLActivity.class));}setText(status,KaliRuntime.diagnostic);return;}
        if(ManagedSetupService.prepared&&!opened){
            try{ActivityManager.MemoryInfo info=new ActivityManager.MemoryInfo();getSystemService(ActivityManager.class).getMemoryInfo(info);VmConfig config=new VmConfig(2048,Math.min(2,Runtime.getRuntime().availableProcessors()),info.totalMem/(1024*1024),Runtime.getRuntime().availableProcessors());
                KaliRuntime.prepareManaged(this,ManagedSetupService.volume,ManagedSetupService.kernel,ManagedSetupService.initrd,ManagedSetupService.layers,config,ManagedProfile.MANIFEST);
                if(KaliRuntime.session.tryStart()){getSharedPreferences("kali",0).edit().putInt("last_pid",android.os.Process.myPid()).putString("last_result","Managed guest interrupted; private data retained. See serial diagnostics.").commit();opened=true;startActivity(new Intent(this,ManagedDesktopActivity.class));}
            }catch(Exception|LinkageError e){ManagedSetupService.error="Cannot start Kali engine: "+String.valueOf(e.getMessage());ManagedSetupService.prepared=false;KaliRuntime.session.failed(ManagedSetupService.error);}
        }
        setText(status,ManagedSetupService.status);setText(detail,ManagedSetupService.error.isEmpty()?"Verified downloads can resume after interruption. Keep the phone powered and connected.":ManagedSetupService.error);
        long total=ManagedSetupService.total;progress.setIndeterminate(total<=0);if(total>0)progress.setProgress((int)Math.min(1000,ManagedSetupService.done*1000/total));
        retry.setVisibility(ManagedSetupService.busy?View.GONE:View.VISIBLE);cancel.setVisibility(ManagedSetupService.busy?View.VISIBLE:View.GONE);
    }
    @Override protected void onResume(){super.onResume();handler.post(refresh);}
    @Override protected void onPause(){handler.removeCallbacks(refresh);super.onPause();}
}
