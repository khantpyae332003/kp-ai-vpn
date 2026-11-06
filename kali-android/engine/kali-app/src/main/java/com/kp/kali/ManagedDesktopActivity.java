package com.kp.kali;

import android.os.*;
import android.graphics.Color;
import android.view.*;
import android.widget.*;
import com.max2idea.android.limbo.main.LimboSDLActivity;

/** Keeps the native SDL surface alive while genuine guest provisioning is in progress. */
public final class ManagedDesktopActivity extends LimboSDLActivity {
    private final Handler handler=new Handler(Looper.getMainLooper());private LinearLayout overlay;private TextView status;
    private final Runnable update=new Runnable(){public void run(){if(overlay!=null){overlay.setVisibility(KaliRuntime.desktopReady()?View.GONE:View.VISIBLE);if(!android.text.TextUtils.equals(status.getText(),KaliRuntime.diagnostic))status.setText(KaliRuntime.diagnostic);}handler.postDelayed(this,500);}};
    @Override protected void onCreate(Bundle state){
        if(!KaliRuntime.isManaged()){skipNativeInitialization=true;super.onCreate(state);startActivity(new android.content.Intent(this,BootstrapActivity.class).addFlags(android.content.Intent.FLAG_ACTIVITY_CLEAR_TOP));finish();return;}
        super.onCreate(state);overlay=new LinearLayout(this);overlay.setOrientation(LinearLayout.VERTICAL);overlay.setGravity(Gravity.CENTER);overlay.setPadding(32,32,32,32);overlay.setBackgroundColor(0xf5101a28);overlay.setClickable(true);
        TextView title=new TextView(this);title.setText("Preparing your Kali desktop");title.setTextColor(Color.WHITE);title.setTextSize(24);overlay.addView(title);
        ProgressBar spinner=new ProgressBar(this);overlay.addView(spinner);
        status=new TextView(this);status.setTextColor(Color.WHITE);status.setTextSize(17);status.setPadding(0,24,0,24);overlay.addView(status);
        TextView note=new TextView(this);note.setText("First installation may take a long time. This screen closes when the guest confirms root, sudo and the XFCE desktop are ready.");note.setTextColor(Color.WHITE);overlay.addView(note);
        Button advanced=new Button(this);advanced.setText("Diagnostics / shutdown controls");advanced.setOnClickListener(v->startActivity(new android.content.Intent(this,MainActivity.class)));overlay.addView(advanced);
        addContentView(overlay,new ViewGroup.LayoutParams(-1,-1));
    }
    @Override protected void onResume(){super.onResume();handler.post(update);}
    @Override protected void onPause(){handler.removeCallbacks(update);super.onPause();}
}
