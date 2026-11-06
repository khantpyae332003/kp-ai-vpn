package com.kp.kali.core;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
public final class LaunchLogs {
    private LaunchLogs() {}
    public static synchronized void rotate(File log,File previous) throws IOException {
        if(log.isFile()&&log.length()>0)Files.move(log.toPath(),previous.toPath(),StandardCopyOption.REPLACE_EXISTING);
    }
    public static synchronized String tail(File log,int bytes) throws IOException {
        if(!log.isFile())return "";
        try(RandomAccessFile file=new RandomAccessFile(log,"r")) {
            int count=(int)Math.min(file.length(),bytes);byte[] data=new byte[count];file.seek(file.length()-count);file.readFully(data);return new String(data,StandardCharsets.UTF_8);
        }
    }
    public static synchronized void append(File log,String text,int maxBytes) throws IOException {
        byte[] data=text.getBytes(StandardCharsets.UTF_8);
        try(RandomAccessFile out=new RandomAccessFile(log,"rw")) {
            if(out.length()+data.length>maxBytes) {
                int count=(int)Math.min(out.length(),Math.max(0,maxBytes/2-data.length));
                byte[] keep=new byte[count];out.seek(out.length()-count);out.readFully(keep);
                out.setLength(0);out.write(keep);
            }else out.seek(out.length());
            int count=Math.min(data.length,maxBytes);out.write(data,data.length-count,count);
            if(out.length()>maxBytes)out.setLength(maxBytes);
        }
    }
}
