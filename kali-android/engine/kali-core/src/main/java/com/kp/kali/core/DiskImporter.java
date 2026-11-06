package com.kp.kali.core;
import java.io.*;
import java.nio.file.*;
import java.util.function.*;
public final class DiskImporter {
    public static int cleanupAbandoned(File directory) throws IOException {
        File[] files=directory.listFiles();if(files==null)throw new IOException("Cannot inspect unfinished disk imports.");
        int removed=0;
        for(File file:files)if(file.getName().startsWith("kali-import-")&&file.getName().endsWith(".partial")
            &&Files.isRegularFile(file.toPath(),LinkOption.NOFOLLOW_LINKS)) {Files.delete(file.toPath());removed++;}
        return removed;
    }
    private static final long RESERVE=64L*1024*1024;
    private final LongSupplier freeSpace;
    public DiskImporter(LongSupplier freeSpace) {this.freeSpace=freeSpace;}
    public String copy(InputStream input,long declared,File destination,boolean replace,BooleanSupplier cancelled,LongConsumer progress) throws IOException {
        if(destination.exists()&&!replace) throw new IOException("Confirm replacement of the existing disk first.");
        if(declared>=0 && declared>freeSpace.getAsLong()-RESERVE) throw new IOException("Not enough storage for a private disk copy.");
        File stage=File.createTempFile("kali-import-",".partial",destination.getParentFile());
        try {
            long copied=0;
            try(FileOutputStream out=new FileOutputStream(stage)) {
                byte[] buffer=new byte[1024*1024];
                while(true) {
                    if(cancelled.getAsBoolean()||Thread.currentThread().isInterrupted()) throw new InterruptedIOException("Import cancelled. Previous disk retained.");
                    int n=input.read(buffer);if(n<0)break;if(n==0)continue;
                    if(freeSpace.getAsLong()-RESERVE<n) throw new IOException("Storage is full. Previous disk retained.");
                    out.write(buffer,0,n);copied+=n;progress.accept(copied);
                }
                out.getFD().sync();
            }
            if(declared>=0 && declared!=copied) throw new IOException("The selected provider returned an incomplete or changed file.");
            String format=inspect(stage);
            if(cancelled.getAsBoolean()) throw new InterruptedIOException("Import cancelled.");
            // Same-filesystem atomic rename ensures readers see either complete old or complete new disk.
            if(!replace && destination.exists()) throw new IOException("Destination already exists.");
            Files.move(stage.toPath(),destination.toPath(),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);
            return format;
        } finally {Files.deleteIfExists(stage.toPath());}
    }
    public static String inspect(File disk) throws IOException {
        try(RandomAccessFile f=new RandomAccessFile(disk,"r")) {
            if(f.length()<512) throw new IOException("Not a VM disk. Choose a standalone amd64 BIOS QCOW2 or bootable raw disk, not an archive or ISO.");
            if(f.readInt()==0x514649fb) {
                int version=f.readInt();long backing=f.readLong();int backingSize=f.readInt();int bits=f.readInt();long size=f.readLong();int encrypted=f.readInt();
                if((version!=2&&version!=3)||backing!=0||backingSize!=0||bits<9||bits>21||size<=0||encrypted!=0)
                    throw new IOException("Unsupported QCOW2: use an unencrypted standalone v2/v3 image without backing files.");
                if(version==3) {f.seek(72);long incompatible=f.readLong();f.seek(100);int headerLength=f.readInt();
                    if(incompatible!=0||headerLength<104||headerLength>f.length()) throw new IOException("QCOW2 features are not supported by the bundled engine; convert to a standalone compatible image first.");}
                return "qcow2";
            }
            f.seek(510);
            if(f.readUnsignedByte()!=0x55||f.readUnsignedByte()!=0xaa) throw new IOException("No PC boot signature found. Rootfs archives, ISOs and compressed images cannot boot here.");
            return "raw";
        }
    }
}
