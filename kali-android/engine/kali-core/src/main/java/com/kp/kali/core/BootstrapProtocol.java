package com.kp.kali.core;
/** Strict guest serial status; CPU execution alone never signals desktop readiness. */
public final class BootstrapProtocol {
 public enum Event { IGNORED, PHASE, ROOT, SUDO, READY, ERROR }
 private final String digest; private boolean root,sudo,ready; private String phase="",error;
 public BootstrapProtocol(String expectedManifestDigest){if(expectedManifestDigest==null||!expectedManifestDigest.matches("sha256:[0-9a-f]{64}"))throw new IllegalArgumentException("Invalid manifest digest");digest=expectedManifestDigest;}
 public synchronized Event accept(String line){if(line==null||!line.startsWith("KP:"))return Event.IGNORED;if(error!=null)return Event.IGNORED;if(line.length()>1024)return fail("Oversized guest status");
  if(line.startsWith("KP:ERROR:"))return fail("Guest setup failed: "+clean(line.substring(9)));
  if(line.startsWith("KP:PHASE:")){String value=line.substring(9);if(!value.matches("[A-Za-z0-9 _.-]{1,100}"))return fail("Malformed guest phase");phase=value;return Event.PHASE;}
  if(line.equals("KP:ROOT_UID:0")){root=true;return Event.ROOT;}if(line.equals("KP:SUDO_UID:0")){sudo=true;return Event.SUDO;}
  if(line.startsWith("KP:DESKTOP_READY:")){if(!line.substring(17).equals(digest))return fail("Guest image identity mismatch");if(root&&sudo){ready=true;return Event.READY;}return Event.IGNORED;}
  return fail("Malformed guest status");
 }
 private Event fail(String reason){error=reason;ready=false;return Event.ERROR;}private static String clean(String s){return s.replaceAll("[^A-Za-z0-9 _.-]","?");}
 public synchronized boolean isReady(){return ready&&error==null;}public synchronized String phase(){return phase;}public synchronized String error(){return error;}
}
