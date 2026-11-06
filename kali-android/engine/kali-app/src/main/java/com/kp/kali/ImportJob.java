// SPDX-License-Identifier: GPL-2.0-or-later
package com.kp.kali;
import android.content.Context;
import android.net.Uri;
import com.kp.kali.core.DiskImporter;
import java.io.*;
import java.util.concurrent.atomic.AtomicBoolean;

final class ImportJob {
    static volatile boolean busy;
    static volatile long bytes;
    static volatile String result="";
    static final AtomicBoolean cancel=new AtomicBoolean();
    private static boolean recovered;
    static synchronized void recover(Context context) throws IOException {
        if(recovered||busy)return;
        int removed=DiskImporter.cleanupAbandoned(context.getFilesDir());recovered=true;
        if(removed>0)result="Recovered "+removed+" unfinished import(s). The existing disk was retained.";
    }
    static synchronized void start(Context context,Uri uri,long size,boolean replace) {
        if(busy)return;
        try{recover(context);}catch(IOException e){result=e.getMessage();return;}
        busy=true;bytes=0;result="";cancel.set(false);
        Context app=context.getApplicationContext();
        new Thread(()->{
            try(InputStream input=app.getContentResolver().openInputStream(uri)) {
                if(input==null)throw new IOException("Cannot open the selected document.");
                File disk=new File(app.getFilesDir(),"kali.disk");
                String format=new DiskImporter(()->app.getFilesDir().getUsableSpace()).copy(input,size,disk,replace,cancel::get,n->bytes=n);
                result="Imported "+format+" disk. Its OS, architecture and BIOS bootability will be checked when it boots.";
            }catch(Exception e){result=e.getMessage()==null?e.toString():e.getMessage();}
            finally{busy=false;}
        },"Kali-import").start();
    }
}
