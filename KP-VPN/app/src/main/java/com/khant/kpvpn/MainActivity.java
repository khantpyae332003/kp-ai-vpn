package com.khant.kpvpn;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.*;
import android.content.*;
import android.database.Cursor;
import android.net.*;
import android.os.*;
import android.provider.OpenableColumns;
import android.view.WindowManager;
import android.webkit.*;
import android.widget.Toast;
import androidx.webkit.WebViewAssetLoader;
import com.google.zxing.integration.android.IntentIntegrator;
import com.google.zxing.integration.android.IntentResult;
import org.json.*;
import java.io.*;
import java.util.*;

public final class MainActivity extends Activity {
 private static final int FILES=41,VPN=42;
 private KpApp app;private WebView web;private boolean loaded;
 private String pendingId="",carrier="OTHER",operator="";
 @Override @SuppressLint("SetJavaScriptEnabled") public void onCreate(Bundle saved){
  super.onCreate(saved);app=(KpApp)getApplication();app.screen=new java.lang.ref.WeakReference<>(this);
  getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
  if(saved!=null){pendingId=saved.getString("pending","");carrier=saved.getString("carrier","OTHER");operator=saved.getString("operator","");}
  web=new WebView(this);setContentView(web);
  if(Build.VERSION.SDK_INT>=30){
   getWindow().setDecorFitsSystemWindows(false);
   web.setOnApplyWindowInsetsListener((v,insets)->{android.graphics.Insets bars=insets.getInsets(android.view.WindowInsets.Type.systemBars()|android.view.WindowInsets.Type.ime());v.setPadding(bars.left,bars.top,bars.right,bars.bottom);return insets;});
  }
  WebSettings s=web.getSettings();s.setJavaScriptEnabled(true);s.setAllowFileAccess(false);s.setAllowContentAccess(false);s.setDomStorageEnabled(false);s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);s.setSupportMultipleWindows(false);s.setJavaScriptCanOpenWindowsAutomatically(false);
  WebView.setWebContentsDebuggingEnabled(false);
  final WebViewAssetLoader loader=new WebViewAssetLoader.Builder().addPathHandler("/assets/",new WebViewAssetLoader.AssetsPathHandler(this)).build();
  web.setWebViewClient(new WebViewClient(){
   @Override public WebResourceResponse shouldInterceptRequest(WebView view,WebResourceRequest req){WebResourceResponse r=loader.shouldInterceptRequest(req.getUrl());return r!=null?r:new WebResourceResponse("text/plain","UTF-8",new ByteArrayInputStream(new byte[0]));}
   @Override public boolean shouldOverrideUrlLoading(WebView view,WebResourceRequest request){return true;}
   @Override public void onPageFinished(WebView view,String url){if(url.equals("https://appassets.androidplatform.net/assets/index.html")){loaded=true;render();}}
  });
  web.addJavascriptInterface(new Bridge(),"Native");web.loadUrl("https://appassets.androidplatform.net/assets/index.html");
 }
 @Override protected void onSaveInstanceState(Bundle b){super.onSaveInstanceState(b);b.putString("pending",pendingId);b.putString("carrier",carrier);b.putString("operator",operator);}
 @Override protected void onResume(){super.onResume();app.screen=new java.lang.ref.WeakReference<>(this);render();}
 @Override protected void onDestroy(){if(app.screen.get()==this)app.screen.clear();web.removeJavascriptInterface("Native");web.destroy();super.onDestroy();}
 void render(){if(loaded&&!isFinishing())web.evaluateJavascript("window.receive("+app.snapshot()+")",null);}
 void message(String text){Toast.makeText(this,text,Toast.LENGTH_LONG).show();if(loaded)web.evaluateJavascript("window.showMessage("+JSONObject.quote(text)+")",null);}
 private void importItems(List<ProfileImporter.Input> items,String c,String o){
  try{if(app.store==null)throw new IOException();int[] n=app.store.add(items,c,o);app.refreshProfiles();app.message("ထည့်ပြီး "+n[0]+" · ထပ်နေ "+n[1]+" · မထည့်နိုင် "+n[2]);app.emit();}
  catch(Exception e){app.fail("Config သိမ်းမရပါ။ ဖိုင်အရွယ်အစားနှင့် ဖုန်းနေရာလွတ်ကို စစ်ပါ။");}
 }
 private void connect(String id){
  if(!app.state.equals("DOWN")){message("လက်ရှိ VPN ကို အရင်ဖြုတ်ပါ။");return;}
  pendingId=id;Intent consent=android.net.VpnService.prepare(this);
  if(consent!=null)startActivityForResult(consent,VPN);else begin();
 }
 private void begin(){
  if(pendingId.isEmpty())return;
  if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=android.content.pm.PackageManager.PERMISSION_GRANTED)requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},43);
  try{startForegroundService(new Intent(this,TunnelService.class).setAction(TunnelService.CONNECT).putExtra("id",pendingId));app.state="STARTING";app.emit();}
  catch(Exception e){app.state="DOWN";app.fail("VPN စတင်မရပါ။ App ကိုပြန်ဖွင့်ပြီး စမ်းပါ။");}
  pendingId="";
 }
 final class Bridge {
  @JavascriptInterface public void action(String name,String payload){
   if(payload==null||payload.length()>ProfileImporter.MAX_INPUT){app.message("Input အလွန်များနေသည်။");return;}
   runOnUiThread(()->{
    try{
     if(app.store==null){message(app.error);return;}
     JSONObject p=new JSONObject(payload);String id=p.optString("id");
     switch(name){
      case "refresh":render();break;
      case "connect":if(id.matches("[a-f0-9]{64}"))connect(id);break;
      case "disconnect":if(!app.state.equals("DOWN"))startService(new Intent(MainActivity.this,TunnelService.class).setAction(TunnelService.DISCONNECT));break;
      case "favorite":app.work.execute(()->{try{app.store.favorite(id);app.refreshProfiles();app.emit();}catch(Exception e){app.message("သိမ်းမရပါ။");}});break;
      case "delete":
       if(!app.state.equals("DOWN")){message("ဖျက်ရန် VPN ကို အရင်ဖြုတ်ပါ။");break;}
       new AlertDialog.Builder(MainActivity.this).setMessage("ဒီ config ကို ဖျက်မလား။").setNegativeButton("မဖျက်ပါ",null).setPositiveButton("ဖျက်မယ်",(d,w)->app.work.execute(()->{try{if(!app.state.equals("DOWN")){app.message("VPN ကို အရင်ဖြုတ်ပါ။");return;}app.store.remove(id);app.refreshProfiles();app.emit();}catch(Exception e){app.message("ဖျက်မရပါ။");}})).show();break;
      case "importText":{
       String c=p.optString("carrier","OTHER"),o=p.optString("operator",""),title=p.optString("name","WireGuard"),text=p.optString("text");
       app.work.execute(()->{List<ProfileImporter.Input> items=new ArrayList<>();int n=0;for(String part:ProfileImporter.split(text)){if(items.size()>=ProfileImporter.MAX_PROFILES){app.message("Config အများဆုံး 2000 ဖြစ်သည်။");return;}items.add(new ProfileImporter.Input(title+" "+(++n),part));}importItems(items,c,o);});break;
      }
      case "files":
       carrier=p.optString("carrier","OTHER");operator=p.optString("operator","");
       Intent picker=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE).putExtra(Intent.EXTRA_ALLOW_MULTIPLE,true);startActivityForResult(picker,FILES);break;
      case "scan":
       carrier=p.optString("carrier","OTHER");operator=p.optString("operator","");
       new IntentIntegrator(MainActivity.this).setDesiredBarcodeFormats(IntentIntegrator.QR_CODE).setPrompt("WireGuard config QR ကို ဖတ်ပါ").setBeepEnabled(false).setOrientationLocked(false).initiateScan();break;
     }
    }catch(Exception e){message("လုပ်ဆောင်မရပါ။ ထပ်စမ်းပါ။");}
   });
  }
 }
 private String filename(Uri uri){
  try(Cursor c=getContentResolver().query(uri,new String[]{OpenableColumns.DISPLAY_NAME},null,null,null)){if(c!=null&&c.moveToFirst())return c.getString(0);}catch(Exception ignored){}return "WireGuard.conf";
 }
 @Override protected void onActivityResult(int request,int result,Intent data){
  super.onActivityResult(request,result,data);
  if(request==VPN){if(result==RESULT_OK)begin();else{pendingId="";message("VPN ခွင့်ပြုချက် မပေးထားပါ။");}return;}
  if(request==FILES&&result==RESULT_OK&&data!=null){
   List<Uri> uris=new ArrayList<>();
   if(data.getClipData()!=null){int n=data.getClipData().getItemCount();if(n>200){message("ဖိုင် 200 ထက်များလျှင် ZIP နဲ့ထည့်ပါ။");return;}for(int i=0;i<n;i++)uris.add(data.getClipData().getItemAt(i).getUri());}else if(data.getData()!=null)uris.add(data.getData());
   String c=carrier,o=operator;
   app.work.execute(()->{try{
    List<ProfileImporter.Input> items=new ArrayList<>();int total=0;
    for(Uri u:uris){try(InputStream input=getContentResolver().openInputStream(u)){
     if(input==null)throw new IOException();List<ProfileImporter.Input> next=ProfileImporter.read(input,filename(u));
     for(ProfileImporter.Input item:next){total+=item.text.getBytes(java.nio.charset.StandardCharsets.UTF_8).length;if(total>ProfileImporter.MAX_INPUT||items.size()>=ProfileImporter.MAX_PROFILES)throw new IOException();items.add(item);}
    }}importItems(items,c,o);
   }catch(Exception e){app.message("ဖိုင်ဖတ်မရပါ။ WireGuard .conf / ZIP၊ 16 MB အောက်နဲ့ ပြန်ထည့်ပါ။");}});return;
  }
  IntentResult scan=IntentIntegrator.parseActivityResult(request,result,data);
  if(scan!=null&&scan.getContents()!=null){String text=scan.getContents(),c=carrier,o=operator;app.work.execute(()->importItems(Collections.singletonList(new ProfileImporter.Input("QR config",text)),c,o));}
 }
}
