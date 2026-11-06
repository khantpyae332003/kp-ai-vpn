// SPDX-License-Identifier: GPL-2.0-or-later
package com.kp.kali;

import android.app.*;
import android.content.*;
import android.database.Cursor;
import android.graphics.Color;
import android.net.Uri;
import android.os.*;
import android.provider.OpenableColumns;
import android.text.InputType;
import android.text.TextUtils;
import android.view.*;
import android.widget.*;
import androidx.appcompat.app.AppCompatActivity;
import com.kp.kali.core.*;
import com.max2idea.android.limbo.main.LimboSDLActivity;
import java.io.File;

public final class MainActivity extends AppCompatActivity {
    private static final int PICK=100;
    private final Handler handler=new Handler(Looper.getMainLooper());
    private TextView state,detail,diskLabel;
    private EditText memory,cpus;
    private Button choose,start,desktop,shutdown,force,cancel;
    private final Runnable refresh=new Runnable(){public void run(){render();handler.postDelayed(this,1000);}};
    private int defaultMemory(){ActivityManager.MemoryInfo info=new ActivityManager.MemoryInfo();((ActivityManager)getSystemService(ACTIVITY_SERVICE)).getMemoryInfo(info);return (int)Math.max(512,Math.min(1024,info.totalMem/(2*1024*1024)));}
    private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density);}

    @Override public void onCreate(Bundle stateBundle) {
        super.onCreate(stateBundle);
        try{ImportJob.recover(this);}catch(Exception e){ImportJob.result="Cannot recover unfinished imports: "+e.getMessage();}
        ScrollView scroll=new ScrollView(this);LinearLayout page=new LinearLayout(this);page.setOrientation(LinearLayout.VERTICAL);page.setPadding(dp(24),dp(32),dp(24),dp(32));scroll.addView(page);setContentView(scroll);
        text(page,"KP / KALI VM",14,0xff5edbd1);
        text(page,"Your Linux workspace",30,Color.WHITE);
        text(page,"ဖုန်း root မလိုတဲ့ virtual machine",16,0xffc2cfdf);
        state=text(page,"Stopped",20,0xff5edbd1);state.setPadding(0,dp(24),0,dp(8));
        diskLabel=text(page,"No disk imported",14,0xffc2cfdf);
        text(page,"1  Import a Kali disk",20,Color.WHITE);
        text(page,"Use an extracted, standalone amd64 BIOS QCOW2 or bootable raw image. ISO, ARM images, ZIP/7z and NetHunter rootfs files will not boot here. The app copies the full file into private storage.",14,0xffc2cfdf);
        choose=button(page,"Choose disk image",v->pick());
        cancel=button(page,"Cancel import",v->ImportJob.cancel.set(true));
        text(page,"2  Resources",20,Color.WHITE);
        memory=number(page,"RAM (MiB)",getPreferences(0).getInt("memory",defaultMemory()));
        cpus=number(page,"CPU cores",getPreferences(0).getInt("cpus",1));
        text(page,"Software emulation can be slow. Start with 1024–2048 MiB and 1–2 cores. Desktop Kali may need more memory.",14,0xffc2cfdf);
        start=button(page,"Start Kali VM",v->startGuest());
        desktop=button(page,"Open desktop",v->openDesktop());
        shutdown=button(page,"Shut down guest",v->KaliRuntime.requestShutdown());
        force=button(page,"Force stop…",v->new AlertDialog.Builder(this).setTitle("Force stop VM?")
            .setMessage("This is like unplugging a computer. Unsaved work and the guest filesystem may be damaged. The disk file will be retained. Use guest shutdown first.")
            .setNegativeButton("Cancel",null).setPositiveButton("Force stop",(d,w)->KaliRuntime.forceStop(true)).show());
        detail=text(page,"",14,0xffc2cfdf);
        button(page,"Startup diagnostics",v->showDiagnostics());
        button(page,"Help & licenses",v->showHelp());
        text(page,"Guest root ≠ Android root. Phone Wi-Fi monitor mode, packet injection and host kernel access are unavailable. Not affiliated with Kali Linux or Offensive Security.",13,0xffa6b8cc);
    }
    private TextView text(LinearLayout page,String text,int size,int color){TextView t=new TextView(this);t.setText(text);t.setTextSize(size);t.setTextColor(color);t.setPadding(0,dp(8),0,dp(8));page.addView(t);return t;}
    private Button button(LinearLayout page,String title,View.OnClickListener click){Button b=new Button(this);b.setText(title);b.setAllCaps(false);b.setMinHeight(dp(48));b.setOnClickListener(click);page.addView(b,new LinearLayout.LayoutParams(-1,-2));return b;}
    private EditText number(LinearLayout page,String label,int value){text(page,label,14,0xffc2cfdf);EditText e=new EditText(this);e.setTextColor(Color.WHITE);e.setInputType(InputType.TYPE_CLASS_NUMBER);e.setSingleLine(true);e.setText(String.valueOf(value));e.setContentDescription(label);e.setMinHeight(dp(48));page.addView(e);return e;}
    private File disk(){return new File(getFilesDir(),"kali.disk");}
    private boolean active(){VmSession.State s=KaliRuntime.session.state();return s==VmSession.State.STARTING||s==VmSession.State.RUNNING||s==VmSession.State.STOPPING||s==VmSession.State.EXITING;}
    private void pick(){
        if(active()||ImportJob.busy)return;
        if(disk().exists())new AlertDialog.Builder(this).setTitle("Replace the current disk?").setMessage("A successful import replaces this app's current VM disk and its saved guest data. A failed or cancelled import keeps the existing disk. Export important guest data before replacing it.")
            .setNegativeButton("Cancel",null).setPositiveButton("Choose replacement",(d,w)->pickDocument()).show();
        else pickDocument();
    }
    private void pickDocument(){Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.setType("*/*");i.addCategory(Intent.CATEGORY_OPENABLE);startActivityForResult(i,PICK);}
    @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(request!=PICK||result!=RESULT_OK||data==null||data.getData()==null||active())return;
        Uri uri=data.getData();long size=-1;
        try(Cursor c=getContentResolver().query(uri,new String[]{OpenableColumns.SIZE},null,null,null)){if(c!=null&&c.moveToFirst()&&!c.isNull(0))size=c.getLong(0);}catch(Exception ignored){}
        ImportJob.start(this,uri,size,disk().exists());render();
    }
    private void startGuest(){
        if(ImportJob.busy||active()||!disk().exists())return;
        try {
            ActivityManager.MemoryInfo info=new ActivityManager.MemoryInfo();((ActivityManager)getSystemService(ACTIVITY_SERVICE)).getMemoryInfo(info);
            VmConfig config=new VmConfig(Integer.parseInt(memory.getText().toString()),Integer.parseInt(cpus.getText().toString()),info.totalMem/(1024*1024),Runtime.getRuntime().availableProcessors());
            getPreferences(0).edit().putInt("memory",config.memoryMiB).putInt("cpus",config.cpus).apply();
            KaliRuntime.prepare(this,disk(),config);
            if(!KaliRuntime.session.tryStart())return;
            getSharedPreferences("kali",0).edit().putInt("last_pid",android.os.Process.myPid()).putString("last_result","Previous VM was interrupted or is starting. Disk retained. Open Startup diagnostics for native errors; check the disk and BIOS/amd64 compatibility.").commit();
            KaliRuntime.diagnostic="Starting QEMU software emulation…";openDesktop();
        }catch(Exception|LinkageError e){KaliRuntime.session.failed(e.getMessage());render();}
    }
    private void openDesktop(){if(active())try{startActivity(new Intent(this,KaliRuntime.isManaged()?ManagedDesktopActivity.class:LimboSDLActivity.class));}catch(Exception e){KaliRuntime.session.failed("Cannot open desktop: "+e.getMessage());}}
    private void render(){
        boolean busy=ImportJob.busy,active=active();VmSession.State s=KaliRuntime.session.state();
        updateText(state,busy?"Importing disk…":s.name());
        updateText(diskLabel,disk().exists()?"Private disk · "+(disk().length()/(1024*1024))+" MiB":"No disk imported");
        choose.setEnabled(!busy&&!active);start.setEnabled(!busy&&!active&&disk().exists());memory.setEnabled(!busy&&!active);cpus.setEnabled(!busy&&!active);
        desktop.setEnabled(active&&s!=VmSession.State.EXITING);shutdown.setEnabled(s==VmSession.State.RUNNING);force.setEnabled(active&&s!=VmSession.State.EXITING);cancel.setVisibility(busy?View.VISIBLE:View.GONE);
        String message=busy?"Copied "+ImportJob.bytes/(1024*1024)+" MiB. Keep the app open during import.":ImportJob.result;
        if(s==VmSession.State.ERROR)message=KaliRuntime.session.error();
        else if(active)message=KaliRuntime.diagnostic;
        else if(message.isEmpty())message=getSharedPreferences("kali",0).getString("last_result","Import a compatible disk to begin. No Kali operating system is bundled in this APK.");
        if(KaliRuntime.session.shutdownTimedOut(SystemClock.elapsedRealtime()))message+="\nGuest has not powered off after 30 seconds. Shut down inside Kali or choose Force stop after saving work.";
        updateText(detail,message);
    }
    private void updateText(TextView view,String text){if(!TextUtils.equals(view.getText(),text))view.setText(text);}
    private void showDiagnostics(){
        TextView text=new TextView(this);text.setText("Reading recent app-only diagnostics…");text.setTextIsSelectable(true);text.setPadding(dp(16),dp(16),dp(16),dp(16));
        ScrollView scroll=new ScrollView(this);scroll.addView(text);new AlertDialog.Builder(this).setTitle("Startup diagnostics").setView(scroll).setPositiveButton("Close",null).show();
        Context app=getApplicationContext();new Thread(()->{String logs=KaliRuntime.readDiagnostics(app);handler.post(()->text.setText(logs));},"Kali-log-view").start();
    }
    private void showHelp(){new AlertDialog.Builder(this).setTitle("KP Kali VM · development build")
        .setMessage("Android 10+, 64-bit phone. No Termux or Android root required.\n\nThis app emulates an amd64 PC using QEMU 5.1.0 / Limbo 6.0.1. Use a trusted standalone BIOS-compatible disk. Import checks headers, not image authenticity or installed OS. Verify official image signatures separately. Guest root uses the guest's own account/password; use sudo inside Kali.\n\nPhone Wi-Fi hardware, monitor mode and Android root are not exposed. No tool can be guaranteed universally. This older engine is for trusted local guests, not hostile images. Newer 16 KiB-page Android devices are not verified.\n\nShutdown may close the app to unload native libraries; reopen it to start again. Uninstalling deletes the private guest disk.\n\nGPL-2.0-or-later. Based on Limbo (Max Kastanas and contributors), QEMU, SDL2, GLib, Pixman, libffi and bundled firmware. Full notices are available below; corresponding-source build instructions accompany this app.")
        .setNeutralButton("License notices",(d,w)->{
            try(java.io.InputStream in=getAssets().open("LICENSE")){java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1)out.write(b,0,n);
                TextView text=new TextView(this);text.setText(out.toString("UTF-8"));text.setPadding(dp(16),dp(16),dp(16),dp(16));ScrollView scroll=new ScrollView(this);scroll.addView(text);new AlertDialog.Builder(this).setTitle("Third-party licenses").setView(scroll).setPositiveButton("Close",null).show();
            }catch(Exception e){new AlertDialog.Builder(this).setMessage("See COPYING and THIRD_PARTY_NOTICES.md in the accompanying source.").setPositiveButton("Close",null).show();}
        }).setPositiveButton("Close",null).show();}
    @Override protected void onResume(){super.onResume();handler.post(refresh);}
    @Override protected void onPause(){handler.removeCallbacks(refresh);super.onPause();}
}
