package com.khant.kpvpn;

import android.content.Context;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.AtomicFile;
import org.json.*;
import javax.crypto.*;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.SecretKey;
import java.io.*;
import java.security.KeyStore;
import java.util.*;
import java.nio.charset.StandardCharsets;

public final class ProfileStore {
 private final AtomicFile file;private JSONArray profiles;private final SecretKey key;
 ProfileStore(Context context)throws Exception {
  file=new AtomicFile(new File(context.getFilesDir(),"profiles.enc"));
  KeyStore ks=KeyStore.getInstance("AndroidKeyStore");ks.load(null);
  String alias="kpvpn.profiles.v1";
  if(!ks.containsAlias(alias)){
   KeyGenerator gen=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");
   gen.init(new KeyGenParameterSpec.Builder(alias,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build());gen.generateKey();
  }
  key=(SecretKey)ks.getKey(alias,null);
  profiles=new JSONArray();
  // openRead recovers AtomicFile's backup if a previous write was interrupted.
  try(FileInputStream in=file.openRead()){
   byte[] data=ProfileImporter.readBounded(in,32*1024*1024);
   if(data.length<29)throw new IOException("Invalid encrypted profile store");
   Cipher c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.DECRYPT_MODE,key,new GCMParameterSpec(128,Arrays.copyOfRange(data,0,12)));
   profiles=new JSONArray(new String(c.doFinal(Arrays.copyOfRange(data,12,data.length)),StandardCharsets.UTF_8));
  }catch(FileNotFoundException absent){if(file.getBaseFile().exists())throw absent;}
 }
 private void persist(JSONArray next)throws Exception {
  Cipher c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.ENCRYPT_MODE,key);
  byte[] encrypted=c.doFinal(next.toString().getBytes(StandardCharsets.UTF_8));
  FileOutputStream out=null;
  try{out=file.startWrite();out.write(c.getIV());out.write(encrypted);file.finishWrite(out);profiles=next;}
  catch(Exception e){if(out!=null)file.failWrite(out);throw e;}
 }
 synchronized int[] add(List<ProfileImporter.Input> items,String carrier,String operator)throws Exception {
  if(!Arrays.asList("TH","MM","OTHER").contains(carrier))carrier="OTHER";
  JSONArray next=new JSONArray(profiles.toString());Set<String> ids=new HashSet<>();
  for(int i=0;i<next.length();i++)ids.add(next.getJSONObject(i).getString("id"));
  int added=0,duplicate=0,invalid=0,total=0;
  for(int i=0;i<next.length();i++)total+=next.getJSONObject(i).getString("config").getBytes(StandardCharsets.UTF_8).length;
  for(ProfileImporter.Input item:items){
   ProfileImporter.Validated v;
   try{v=ProfileImporter.validate(item.text);}catch(Exception e){invalid++;continue;}
   if(ids.contains(v.fingerprint)){duplicate++;continue;}
   int size=v.config.getBytes(StandardCharsets.UTF_8).length;
   if(next.length()>=ProfileImporter.MAX_PROFILES||total+size>ProfileImporter.MAX_INPUT){invalid++;continue;}
   String name=item.name.replaceAll("(?i)\\.conf$","").trim();if(name.isEmpty())name="WireGuard";
   JSONObject p=new JSONObject().put("id",v.fingerprint).put("name",name.substring(0,Math.min(80,name.length()))).put("carrier",carrier).put("operator",operator.substring(0,Math.min(40,operator.length()))).put("config",v.config).put("favorite",false);
   next.put(p);ids.add(v.fingerprint);total+=size;added++;
  }
  if(added>0)persist(next);return new int[]{added,duplicate,invalid};
 }
 synchronized JSONArray metadata()throws JSONException {
  JSONArray result=new JSONArray();
  for(int i=0;i<profiles.length();i++){JSONObject p=profiles.getJSONObject(i);result.put(new JSONObject().put("id",p.getString("id")).put("name",p.getString("name")).put("carrier",p.getString("carrier")).put("operator",p.optString("operator")).put("favorite",p.optBoolean("favorite")));}return result;
 }
 synchronized String config(String id)throws Exception {for(int i=0;i<profiles.length();i++)if(profiles.getJSONObject(i).getString("id").equals(id))return profiles.getJSONObject(i).getString("config");throw new IOException("Profile not found");}
 synchronized void remove(String id)throws Exception {JSONArray next=new JSONArray();for(int i=0;i<profiles.length();i++)if(!profiles.getJSONObject(i).getString("id").equals(id))next.put(profiles.getJSONObject(i));persist(next);}
 synchronized void favorite(String id)throws Exception {JSONArray next=new JSONArray(profiles.toString());for(int i=0;i<next.length();i++){JSONObject p=next.getJSONObject(i);if(p.getString("id").equals(id))p.put("favorite",!p.optBoolean("favorite"));}persist(next);}
}
