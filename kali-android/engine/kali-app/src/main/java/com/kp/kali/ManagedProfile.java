package com.kp.kali;

import android.content.Context;
import org.json.*;
import java.io.*;
import java.util.*;

/** APK-pinned producer identity; no mutable tags or remote profile discovery. */
final class ManagedProfile {
    static final String MANIFEST="sha256:e1734859c9c508c41c0f30cb33cfa56c9d9a7044a4250dc9ae0be078792623d4";
    final String repository,kernelHash,initrdHash;
    final List<Layer> layers=new ArrayList<>();
    static final class Layer { final String hash; final long size; Layer(String hash,long size){this.hash=hash;this.size=size;} }
    ManagedProfile(Context context) throws Exception {
        JSONObject json;
        try(InputStream in=context.getAssets().open("managed/profile.json")) {
            ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[8192];int n;
            while((n=in.read(b))!=-1){if(out.size()+n>1024*1024)throw new IOException("Managed profile too large");out.write(b,0,n);}
            json=new JSONObject(out.toString("UTF-8"));
        }
        if(!MANIFEST.equals(json.getString("manifestDigest")))throw new IOException("Unexpected managed image identity");
        repository=json.getString("repository");
        if(!repository.matches("[a-z0-9._-]+/[a-z0-9._-]+"))throw new IOException("Invalid image repository");
        kernelHash=sha(json.getString("kernelSha256"));initrdHash=sha(json.getString("initrdSha256"));
        JSONArray list=json.getJSONArray("layers");if(list.length()!=6)throw new IOException("Unexpected managed image layer count");
        for(int i=0;i<list.length();i++){JSONObject l=list.getJSONObject(i);String d=l.getString("digest");if(!d.startsWith("sha256:"))throw new IOException("Unsupported image digest");long size=l.getLong("size");if(size<=0||size>16L*1024*1024*1024)throw new IOException("Invalid image layer size");layers.add(new Layer(sha(d.substring(7)),size));}
    }
    private static String sha(String value)throws IOException{if(!value.matches("[0-9a-f]{64}"))throw new IOException("Invalid pinned payload hash");return value;}
}
