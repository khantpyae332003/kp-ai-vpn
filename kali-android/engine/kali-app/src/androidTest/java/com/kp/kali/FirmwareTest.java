package com.kp.kali;
import android.app.Instrumentation;import android.os.Bundle;import android.content.Context;
import java.io.*;
/** Direct-kernel boot must have the matching PCI option ROMs, not just a disk BIOS. */
public final class FirmwareTest extends Instrumentation {
 @Override public void onCreate(Bundle args){super.onCreate(args);start();}
 @Override public void onStart(){Bundle result=new Bundle();try{
  runOnMainSync(()->{});
  for(String name:new String[]{"linuxboot.bin","linuxboot_dma.bin"}){
   byte[] bytes;
   try(InputStream in=getTargetContext().getAssets().open("roms/"+name);ByteArrayOutputStream out=new ByteArrayOutputStream()){
    byte[] b=new byte[1024];int n;while((n=in.read(b))!=-1){if(out.size()+n>65536)throw new AssertionError("Oversized boot ROM");out.write(b,0,n);}bytes=out.toByteArray();
   }catch(FileNotFoundException e){throw new AssertionError("Required direct-kernel boot ROM absent from installed APK: "+name);}
   int sum=0;for(byte b:bytes)sum=(sum+(b&255))&255;
   if(bytes.length<512||(bytes[0]&255)!=0x55||(bytes[1]&255)!=0xaa||bytes.length!=(bytes[2]&255)*512||sum!=0)throw new AssertionError("Invalid PCI boot ROM: "+name);
  }
  // The new runtime preflight is shared by preparation and engine startup.
  KaliRuntime.class.getMethod("verifyBootAssets",Context.class).invoke(null,getTargetContext());
  result.putString("stream","PASS installed APK contains valid direct-kernel boot ROMs and runtime preflight succeeds\n");finish(0,result);
 }catch(Throwable e){result.putString("stream","FAIL "+android.util.Log.getStackTraceString(e)+"\n");finish(1,result);}}
}
