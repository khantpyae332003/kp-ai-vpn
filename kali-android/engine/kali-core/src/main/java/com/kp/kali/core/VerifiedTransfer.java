package com.kp.kali.core;
import java.io.*;import java.net.*;import java.nio.file.*;import java.security.*;import java.util.*;
/** Exact-size SHA256 transfer, with verified cache and resumable private staging. */
public final class VerifiedTransfer {
 public interface Headers{Map<String,String> forUrl(URL url)throws IOException;}public interface RedirectPolicy{boolean allows(URL url);}public interface Cancel{boolean cancelled();}public interface Progress{void bytes(long done,long total);default void phase(String name){}}
 public File fetch(URL source,long expectedBytes,String sha256Hex,File target,Headers headers,RedirectPolicy redirects,Cancel cancel,Progress progress)throws IOException{
  if(expectedBytes<=0||expectedBytes>Long.MAX_VALUE-511||sha256Hex==null||!sha256Hex.matches("[0-9a-f]{64}"))throw new IOException("Invalid payload metadata");
  checkUrl(source);File part=new File(target.getPath()+".part");safe(target);safe(part);cancel(cancel);
  if(verified(target,expectedBytes,sha256Hex,true)){progress.bytes(expectedBytes,expectedBytes);return target;}
  if(part.exists()&&part.length()>expectedBytes)Files.delete(part.toPath());
  if(part.length()==expectedBytes&&!verified(part,expectedBytes,sha256Hex,false))Files.delete(part.toPath());
  try{
   if(part.length()!=expectedBytes)download(source,expectedBytes,part,headers,redirects,cancel,progress);
   cancel(cancel);progress.phase("Verifying");if(!verified(part,expectedBytes,sha256Hex,false)){Files.deleteIfExists(part.toPath());throw new IOException("Payload integrity verification failed");}
   try(RandomAccessFile out=new RandomAccessFile(part,"rw")){out.seek(expectedBytes);int padding=(int)((512-expectedBytes%512)%512);out.write(new byte[padding]);out.getFD().sync();}
   cancel(cancel);Files.move(part.toPath(),target.toPath(),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);progress.bytes(expectedBytes,expectedBytes);return target;
  }catch(InterruptedIOException e){throw e;}catch(IOException e){throw new IOException("Verified payload transfer failed");}
 }
 private void download(URL original,long size,File part,Headers headers,RedirectPolicy policy,Cancel cancel,Progress progress)throws IOException{
  long start=part.length();URL url=original;HttpURLConnection connection=null;
  try{for(int hops=0;;hops++){cancel(cancel);checkUrl(url);connection=(HttpURLConnection)url.openConnection();connection.setInstanceFollowRedirects(false);connection.setConnectTimeout(20000);connection.setReadTimeout(20000);connection.setRequestProperty("Accept-Encoding","identity");if(sameOrigin(original,url)){Map<String,String> values=headers.forUrl(url);if(values!=null)for(Map.Entry<String,String> e:values.entrySet())connection.setRequestProperty(e.getKey(),e.getValue());}if(start>0)connection.setRequestProperty("Range","bytes="+start+"-");int status=connection.getResponseCode();
   if(status==301||status==302||status==303||status==307||status==308){String location=connection.getHeaderField("Location");if(hops>=5||location==null)throw new IOException("Redirect rejected");URL next=new URL(url,location);checkUrl(next);if(!policy.allows(next))throw new IOException("Redirect rejected");connection.disconnect();url=next;continue;}
   if(status==200){start=0;}else if(status==206){String range=connection.getHeaderField("Content-Range");if(!("bytes "+start+"-"+(size-1)+"/"+size).equals(range))throw new IOException("Invalid range response");}else throw new IOException("Unexpected response");
   String encoding=connection.getHeaderField("Content-Encoding");if(encoding!=null&&!encoding.equalsIgnoreCase("identity"))throw new IOException("Encoded payload rejected");long length=connection.getContentLengthLong();if(length>=0&&length!=size-start)throw new IOException("Invalid response size");
   try(InputStream in=connection.getInputStream();RandomAccessFile out=new RandomAccessFile(part,"rw")){out.setLength(start);out.seek(start);byte[] buffer=new byte[65536];long done=start;progress.bytes(done,size);while(true){cancel(cancel);int n=in.read(buffer);if(n<0)break;if(n==0)continue;if(n>size-done){out.setLength(0);throw new IOException("Oversized payload");}out.write(buffer,0,n);done+=n;progress.bytes(done,size);}if(done!=size)throw new IOException("Incomplete payload");out.getFD().sync();}return;
  }}finally{if(connection!=null)connection.disconnect();}
 }
 private static boolean sameOrigin(URL a,URL b){return a.getProtocol().equalsIgnoreCase(b.getProtocol())&&a.getHost().equalsIgnoreCase(b.getHost())&&port(a)==port(b);}private static int port(URL u){return u.getPort()<0?u.getDefaultPort():u.getPort();}
 private static void checkUrl(URL u)throws IOException{if(u==null||!(u.getProtocol().equals("http")||u.getProtocol().equals("https"))||u.getUserInfo()!=null)throw new IOException("Invalid payload endpoint");}
 private static void safe(File f)throws IOException{if(Files.isSymbolicLink(f.toPath())||(f.exists()&&!f.isFile()))throw new IOException("Unsafe payload path");}
 private static void cancel(Cancel c)throws InterruptedIOException{if(c.cancelled()||Thread.currentThread().isInterrupted())throw new InterruptedIOException("Transfer cancelled");}
 private static boolean verified(File f,long size,String hash,boolean padded)throws IOException{if(!f.isFile()||f.length()!=(padded?size+(512-size%512)%512:size))return false;try{MessageDigest digest=MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(f)){byte[] b=new byte[65536];long left=size;while(left>0){int n=in.read(b,0,(int)Math.min(left,b.length));if(n<0)return false;digest.update(b,0,n);left-=n;}for(int v;(v=in.read())>=0;)if(v!=0)return false;}StringBuilder s=new StringBuilder();for(byte v:digest.digest())s.append(String.format(Locale.ROOT,"%02x",v&255));return s.toString().equals(hash);}catch(NoSuchAlgorithmException e){throw new IOException("SHA256 unavailable");}}
}
