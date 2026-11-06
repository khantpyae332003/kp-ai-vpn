package com.kp.kali;
import android.net.LocalSocket;import android.net.LocalSocketAddress;
import java.io.*;import java.nio.charset.StandardCharsets;import org.json.JSONObject;
/** Headless, read-only test client run as the app UID; never attaches instrumentation or stops the app. */
public final class QmpStatusProbe {
 private static JSONObject reply(BufferedReader in,int id)throws Exception{
  for(int n=0;n<100;n++){String line=in.readLine();if(line==null)throw new EOFException();JSONObject o=new JSONObject(line);if(o.optInt("id",-1)==id){if(o.has("error"))throw new IOException("QMP rejected test request");return o.getJSONObject("return");}}
  throw new IOException("No matching QMP reply");
 }
 private static void send(BufferedWriter out,String name,int id,JSONObject arguments)throws Exception{
  JSONObject o=new JSONObject().put("execute",name).put("id",id);if(arguments!=null)o.put("arguments",arguments);out.write(o.toString());out.write('\n');out.flush();
 }
 public static void main(String[] args){
  try{
   if(args.length!=1||!args[0].matches("/data/(user/0|data)/com\\.kp\\.kali"))throw new IllegalArgumentException("Unexpected disposable-app directory");
   try(LocalSocket s=new LocalSocket()){
    s.connect(new LocalSocketAddress(args[0]+"/cache/qmpsocket",LocalSocketAddress.Namespace.FILESYSTEM));s.setSoTimeout(8000);
    BufferedReader in=new BufferedReader(new InputStreamReader(s.getInputStream(),StandardCharsets.UTF_8));BufferedWriter out=new BufferedWriter(new OutputStreamWriter(s.getOutputStream(),StandardCharsets.UTF_8));
    String greeting=in.readLine();if(greeting==null||!new JSONObject(greeting).has("QMP"))throw new IOException("No QMP greeting");
    send(out,"qmp_capabilities",1,null);reply(in,1);send(out,"query-status",2,null);JSONObject status=reply(in,2);
    boolean live=status.getBoolean("running")&&"running".equals(status.getString("status"));
    if(live){send(out,"screendump",3,new JSONObject().put("filename",args[0]+"/cache/verification.ppm"));reply(in,3);}
    System.out.println("KP_TEST_QMP="+new JSONObject().put("running",live).put("status",status.getString("status")).put("uid",android.os.Process.myUid()).toString());
    if(!live)System.exit(2);
   }
  }catch(Throwable e){System.out.println("KP_TEST_QMP_FAILURE="+e.getClass().getName());System.exit(2);}
 }
}
