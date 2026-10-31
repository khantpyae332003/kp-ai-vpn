package com.khant.kpvpn;

import com.wireguard.config.Config;
import com.wireguard.config.Peer;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.zip.*;

public final class ProfileImporter {
 public static final int MAX_PROFILES=2000, MAX_CONFIG=128*1024, MAX_INPUT=16*1024*1024;
 public static final class Validated {
  public final String config,fingerprint;
  Validated(String c,String f){config=c;fingerprint=f;}
 }
 public static final class Input {
  public final String name,text;
  Input(String n,String t){name=n;text=t;}
 }
 public static List<String> split(String text){
  String normalized=text.replace("\uFEFF","").replace("\r\n","\n").trim();
  List<String> out=new ArrayList<>();
  for(String part:normalized.split("(?m)(?=^\\s*\\[Interface\\]\\s*$)")){
   if(part.contains("[Interface]"))out.add(part.trim());
  }
  if(out.isEmpty()&&!normalized.isEmpty())out.add(normalized);
  return out;
 }
 public static Validated validate(String text) throws Exception {
  byte[] bytes=text.getBytes(StandardCharsets.UTF_8);
  if(bytes.length>MAX_CONFIG)throw new IOException("Config too large");
  Config config=Config.parse(new ByteArrayInputStream(bytes));
  if(config.getInterface().getAddresses().isEmpty()||config.getPeers().isEmpty())throw new IOException("Address and peer required");
  for(Peer peer:config.getPeers())if(!peer.getEndpoint().isPresent()||peer.getAllowedIps().isEmpty())throw new IOException("Endpoint and routes required");
  String canonical=config.toWgQuickString();
  byte[] digest=MessageDigest.getInstance("SHA-256").digest(canonical.getBytes(StandardCharsets.UTF_8));
  StringBuilder id=new StringBuilder();for(byte b:digest)id.append(String.format(Locale.ROOT,"%02x",b&255));
  return new Validated(canonical,id.toString());
 }
 public static byte[] readBounded(InputStream in,int limit) throws IOException {
  ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[8192];int count;
  while((count=in.read(b))!=-1){if(out.size()+count>limit)throw new IOException("Input limit exceeded");out.write(b,0,count);}
  return out.toByteArray();
 }
 public static List<Input> read(InputStream input,String filename)throws IOException {
  byte[] bytes=readBounded(input,MAX_INPUT);
  List<Input> out=new ArrayList<>();
  boolean zip=bytes.length>=4&&bytes[0]=='P'&&bytes[1]=='K';
  if(zip){
   int total=0,entries=0;
   try(ZipInputStream z=new ZipInputStream(new ByteArrayInputStream(bytes))){
    ZipEntry e;while((e=z.getNextEntry())!=null){
     if(++entries>MAX_PROFILES*2)throw new IOException("Too many archive entries");
     // Every entry consumes the same expansion budget, including ignored files.
     byte[] item=readBounded(z,Math.min(MAX_INPUT-total,MAX_CONFIG));total+=item.length;
     if(!e.isDirectory()&&e.getName().toLowerCase(Locale.ROOT).endsWith(".conf")){
      String name=e.getName().replace('\\','/');name=name.substring(name.lastIndexOf('/')+1);
      append(out,name,new String(item,StandardCharsets.UTF_8));
     }
     z.closeEntry();
    }
   }
  }else append(out,filename,new String(bytes,StandardCharsets.UTF_8));
  if(out.isEmpty())throw new IOException("No WireGuard configs");return out;
 }
 private static void append(List<Input> out,String name,String text)throws IOException {
  List<String> parts=split(text);int n=0;
  for(String part:parts){if(out.size()>=MAX_PROFILES)throw new IOException("Too many configs");out.add(new Input(name+(parts.size()>1?" "+(++n):""),part));}
 }
 private ProfileImporter(){}
}
