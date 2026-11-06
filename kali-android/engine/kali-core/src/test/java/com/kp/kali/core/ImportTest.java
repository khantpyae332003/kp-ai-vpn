package com.kp.kali.core;

import org.junit.Test;
import org.junit.Rule;
import org.junit.rules.TemporaryFolder;
import java.io.*;
import java.nio.ByteBuffer;
import java.nio.file.Files;
import static org.junit.Assert.*;

public class ImportTest {
    @Rule public TemporaryFolder temp = new TemporaryFolder();
    private byte[] raw() { byte[] a=new byte[512]; a[510]=0x55; a[511]=(byte)0xaa; return a; }
    private byte[] qcow() {
        ByteBuffer b=ByteBuffer.allocate(512); b.putInt(0,0x514649fb); b.putInt(4,3);
        b.putInt(20,16); b.putLong(24,1024*1024); b.putInt(100,104); return b.array();
    }
    private File dest() { return new File(temp.getRoot(), "kali.disk"); }
    private DiskImporter importer(long space) { return new DiskImporter(()->space); }
    @Test public void importsRawDiskWithExplicitFormat() throws Exception {
        File d=dest(); assertEquals("raw",importer(Long.MAX_VALUE).copy(new ByteArrayInputStream(raw()),512,d,false,()->false,n->{}));
        assertArrayEquals(raw(),Files.readAllBytes(d.toPath()));
    }
    @Test public void detectsQcowInsteadOfTrustingFilename() throws Exception {
        assertEquals("qcow2",importer(Long.MAX_VALUE).copy(new ByteArrayInputStream(qcow()),512,dest(),false,()->false,n->{}));
    }
    @Test public void rejectsRootfsTarAndOtherNonDisks() throws Exception {
        assertThrows(IOException.class,()->importer(Long.MAX_VALUE).copy(new ByteArrayInputStream(new byte[512]),512,dest(),false,()->false,n->{})); assertFalse(dest().exists());
    }
    @Test public void rejectsQcowBackingFile() throws Exception {
        byte[] a=qcow();ByteBuffer.wrap(a).putLong(8,104).putInt(16,9);
        assertThrows(IOException.class,()->importer(Long.MAX_VALUE).copy(new ByteArrayInputStream(a),512,dest(),false,()->false,n->{}));
    }
    @Test public void rejectsUnsupportedQcowFeatures() throws Exception {
        byte[] a=qcow();ByteBuffer.wrap(a).putLong(72,16);
        assertThrows(IOException.class,()->importer(Long.MAX_VALUE).copy(new ByteArrayInputStream(a),512,dest(),false,()->false,n->{}));
    }
    @Test public void refusesReplacementWithoutConfirmation() throws Exception {
        Files.write(dest().toPath(),new byte[]{7});
        assertThrows(IOException.class,()->importer(Long.MAX_VALUE).copy(new ByteArrayInputStream(raw()),512,dest(),false,()->false,n->{}));
        assertArrayEquals(new byte[]{7},Files.readAllBytes(dest().toPath()));
    }
    @Test public void invalidReplacementPreservesOldDisk() throws Exception {
        Files.write(dest().toPath(),new byte[]{7});
        assertThrows(IOException.class,()->importer(Long.MAX_VALUE).copy(new ByteArrayInputStream(new byte[512]),512,dest(),true,()->false,n->{}));
        assertArrayEquals(new byte[]{7},Files.readAllBytes(dest().toPath()));
        assertEquals(1,temp.getRoot().list().length);
    }
    @Test public void handlesLowStorageWithoutReplacingDisk() throws Exception {
        assertThrows(IOException.class,()->importer(1).copy(new ByteArrayInputStream(raw()),512,dest(),false,()->false,n->{}));assertFalse(dest().exists());
    }
    @Test public void interruptedImportCleansStagingFile() throws Exception {
        assertThrows(InterruptedIOException.class,()->importer(Long.MAX_VALUE).copy(new ByteArrayInputStream(raw()),512,dest(),false,()->true,n->{}));
        assertEquals(0,temp.getRoot().list().length);
    }
    @Test public void truncatedProviderStreamIsNotCommitted() throws Exception {
        assertThrows(IOException.class,()->importer(Long.MAX_VALUE).copy(new ByteArrayInputStream(raw()),1024,dest(),false,()->false,n->{}));assertFalse(dest().exists());
    }
    @Test public void confirmedReplacementCommitsNewBytes() throws Exception {
        Files.write(dest().toPath(),new byte[]{7});
        importer(Long.MAX_VALUE).copy(new ByteArrayInputStream(raw()),512,dest(),true,()->false,n->{});
        assertArrayEquals(raw(),Files.readAllBytes(dest().toPath()));
    }
    @Test public void resourceLimitsRejectImpossibleAllocations() {
        assertThrows(IllegalArgumentException.class,()->new VmConfig(4096,2,2048,8));
        assertThrows(IllegalArgumentException.class,()->new VmConfig(1024,8,8192,4));
        assertThrows(IllegalArgumentException.class,()->new VmConfig(0,1,8192,4));
        VmConfig c=new VmConfig(1024,2,8192,4);assertEquals(1024,c.memoryMiB);assertEquals(2,c.cpus);
    }
    @Test public void recoversKilledImportWithoutDeletingDiskOrOtherFiles() throws Exception {
        Files.write(dest().toPath(),new byte[]{7});
        Files.write(new File(temp.getRoot(),"kali-import-abcd.partial").toPath(),new byte[4096]);
        File unrelated=new File(temp.getRoot(),"other.partial");Files.write(unrelated.toPath(),new byte[]{3});
        assertEquals(1,DiskImporter.cleanupAbandoned(temp.getRoot()));
        assertArrayEquals(new byte[]{7},Files.readAllBytes(dest().toPath()));assertTrue(unrelated.exists());
        assertEquals(0,DiskImporter.cleanupAbandoned(temp.getRoot()));
    }
}
