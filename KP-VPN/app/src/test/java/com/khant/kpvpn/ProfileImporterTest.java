package com.khant.kpvpn;
import org.junit.Test;
import static org.junit.Assert.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.zip.*;
public class ProfileImporterTest {
 static final String CONF="[Interface]\nPrivateKey = AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=\nAddress = 10.20.0.2/32\n[Peer]\nPublicKey = AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQE=\nAllowedIPs = 0.0.0.0/0, ::/0\nEndpoint = 192.0.2.1:51820\n";
 @Test public void importsMultipleConfigs(){assertEquals(2,ProfileImporter.split(CONF+"\n"+CONF).size());}
 @Test public void canonicalFingerprintIgnoresComment() throws Exception {
  assertEquals(ProfileImporter.validate(CONF).fingerprint,ProfileImporter.validate("# note\n"+CONF).fingerprint);
 }
 @Test(expected=Exception.class) public void rejectsMissingPeer() throws Exception {ProfileImporter.validate(CONF.substring(0,CONF.indexOf("[Peer]")));}
 @Test(expected=Exception.class) public void rejectsInvalidKey() throws Exception {ProfileImporter.validate(CONF.replace("AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=","not-a-key"));}
 @Test(expected=Exception.class) public void rejectsUnknownProtocol() throws Exception {ProfileImporter.validate("vmess://not-wireguard");}
 @Test public void readsConfFromZipWithoutExtractingPaths() throws Exception {
  ByteArrayOutputStream bytes=new ByteArrayOutputStream();
  try(ZipOutputStream z=new ZipOutputStream(bytes)){z.putNextEntry(new ZipEntry("../remote.conf"));z.write(CONF.getBytes(StandardCharsets.UTF_8));z.closeEntry();}
  assertEquals(1,ProfileImporter.read(new ByteArrayInputStream(bytes.toByteArray()),"bundle.zip").size());
 }
 @Test(expected=IOException.class) public void limitsExpandedInput() throws Exception {
  ProfileImporter.readBounded(new ByteArrayInputStream(new byte[1025]),1024);
 }
}
