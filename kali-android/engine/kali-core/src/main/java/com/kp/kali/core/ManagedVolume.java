package com.kp.kali.core;
import java.io.*;import java.nio.file.*;import java.util.*;
/** A private sparse disk and an atomic identity receipt. Never adopts unknown disks. */
public final class ManagedVolume {
 public final File disk;public final String uuid;private final File receipt;private final String profile;private final long bytes;private boolean ready;
 private ManagedVolume(File disk,File receipt,String profile,long bytes,String uuid,boolean ready){this.disk=disk;this.receipt=receipt;this.profile=profile;this.bytes=bytes;this.uuid=uuid;this.ready=ready;}
 public static synchronized ManagedVolume createOrOpen(File dir,String profileDigest,long logicalBytes)throws IOException{
  if(profileDigest==null||!profileDigest.matches("sha256:[0-9a-f]{64}")||logicalBytes<=0||logicalBytes%512!=0)throw new IOException("Invalid managed volume identity or size");
  if(Files.isSymbolicLink(dir.toPath())||(!dir.isDirectory()&&!dir.mkdirs()))throw new IOException("Invalid managed directory");
  File disk=new File(dir,"volume.ext4"),receipt=new File(dir,"volume.properties");check(disk);check(receipt);ManagedVolume v;
  if(receipt.exists()){Properties p=new Properties();try(InputStream in=new FileInputStream(receipt)){p.load(in);}String uuid=p.getProperty("uuid","");if(!profileDigest.equals(p.getProperty("profile"))||!Long.toString(logicalBytes).equals(p.getProperty("bytes"))||!uuid.matches("[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}")||!("true".equals(p.getProperty("ready"))||"false".equals(p.getProperty("ready"))))throw new IOException("Managed volume identity mismatch");v=new ManagedVolume(disk,receipt,profileDigest,logicalBytes,uuid,Boolean.parseBoolean(p.getProperty("ready")));if(!disk.exists()&&v.ready)throw new IOException("Ready volume missing");
  }else{if(disk.exists())throw new IOException("Unrecognized managed disk; preserved");v=new ManagedVolume(disk,receipt,profileDigest,logicalBytes,UUID.randomUUID().toString(),false);v.writeReceipt();}
  if(disk.exists()){if(disk.length()!=logicalBytes)throw new IOException("Managed volume length mismatch; preserved");}else{Files.createFile(disk.toPath());try(RandomAccessFile out=new RandomAccessFile(disk,"rw")){out.setLength(logicalBytes);out.getFD().sync();}}return v;
 }
 private static void check(File f)throws IOException{if(Files.isSymbolicLink(f.toPath())||(f.exists()&&!f.isFile()))throw new IOException("Unsafe managed volume path");}
 public synchronized boolean isReady(){return ready;}
 public synchronized void markReady()throws IOException{check(disk);check(receipt);if(disk.length()!=bytes)throw new IOException("Managed volume changed");boolean old=ready;ready=true;try{writeReceipt();}catch(IOException e){ready=old;throw e;}}
 private void writeReceipt()throws IOException{Properties p=new Properties();p.setProperty("profile",profile);p.setProperty("uuid",uuid);p.setProperty("bytes",Long.toString(bytes));p.setProperty("ready",Boolean.toString(ready));File stage=File.createTempFile("volume-receipt-",".tmp",receipt.getParentFile());try{try(FileOutputStream out=new FileOutputStream(stage)){p.store(out,"Managed Kali volume");out.getFD().sync();}Files.move(stage.toPath(),receipt.toPath(),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}finally{Files.deleteIfExists(stage.toPath());}}
}
