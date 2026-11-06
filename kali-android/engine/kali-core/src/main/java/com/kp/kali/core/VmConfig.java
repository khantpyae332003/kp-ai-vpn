package com.kp.kali.core;
public final class VmConfig {
    public final int memoryMiB,cpus;
    public VmConfig(int memoryMiB,int cpus,long hostMemoryMiB,int hostCpus) {
        long max=Math.min(4096,hostMemoryMiB/2);
        if(memoryMiB<512 || memoryMiB>max)
            throw new IllegalArgumentException("RAM must be 512–"+max+" MiB (at most half of phone RAM).");
        if(cpus<1 || cpus>Math.min(4,hostCpus))
            throw new IllegalArgumentException("Choose 1–"+Math.min(4,hostCpus)+" CPUs.");
        this.memoryMiB=memoryMiB;this.cpus=cpus;
    }
}
