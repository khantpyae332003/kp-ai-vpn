package com.kp.kali.core;
public final class VmSession {
    public enum State {STOPPED,STARTING,RUNNING,STOPPING,EXITING,ERROR}
    public synchronized void finishing(String result) {current=State.EXITING;lastError=result;}
    private State current=State.STOPPED;
    private String lastError="";
    private long shutdownAt;
    private long forcedAt=-1;
    public synchronized boolean tryStart(){if(current!=State.STOPPED&&current!=State.ERROR)return false;current=State.STARTING;forcedAt=-1;lastError="";return true;}
    public synchronized void running(){if(current==State.STARTING)current=State.RUNNING;}
    public synchronized void failed(String error){current=State.ERROR;lastError=error==null?"Unknown VM startup error":error;}
    public synchronized boolean needsProcessTermination(long now){return forcedAt>=0&&now-forcedAt>=5000&&(current==State.STOPPING||current==State.EXITING);}
    public synchronized State state(){return current;}
    public synchronized String error(){return lastError;}
    public synchronized boolean requestShutdown(long now){if(current!=State.RUNNING)return false;current=State.STOPPING;shutdownAt=now;return true;}
    public synchronized boolean shutdownTimedOut(long now){return current==State.STOPPING&&now-shutdownAt>=30000;}
    public synchronized boolean confirmForceStop(boolean confirmed,long now){if(!confirmed||current==State.STOPPED||current==State.ERROR||current==State.EXITING)return false;current=State.STOPPING;if(forcedAt<0)forcedAt=now;return true;}
}
