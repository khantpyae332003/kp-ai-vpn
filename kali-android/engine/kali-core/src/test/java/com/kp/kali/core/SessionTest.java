package com.kp.kali.core;
import org.junit.Test;
import static org.junit.Assert.*;
public class SessionTest {
    @Test public void duplicateStartIsRejectedDuringStartupAndRunning() {
        VmSession s=new VmSession();assertTrue(s.tryStart());assertFalse(s.tryStart());s.running();assertFalse(s.tryStart());
    }
    @Test public void startupFailureExposesErrorAndAllowsRetry() {
        VmSession s=new VmSession();s.tryStart();s.failed("Missing firmware");assertEquals(VmSession.State.ERROR,s.state());assertEquals("Missing firmware",s.error());assertTrue(s.tryStart());
    }
    @Test public void activityReattachDoesNotResetSharedSession() {
        VmSession s=new VmSession();s.tryStart();s.running();VmSession secondView=s;assertEquals(VmSession.State.RUNNING,secondView.state());assertFalse(secondView.tryStart());
    }
    @Test public void shutdownTimeoutRequiresExplicitForceStop() {
        VmSession s=new VmSession();s.tryStart();s.running();assertTrue(s.requestShutdown(100));
        assertFalse(s.shutdownTimedOut(30099));assertTrue(s.shutdownTimedOut(30100));assertEquals(VmSession.State.STOPPING,s.state());
        assertFalse(s.tryStart());s.finishing("VM shutdown");assertEquals(VmSession.State.EXITING,s.state());
    }
    @Test public void forceStopRequiresConfirmationAndActiveSession() {
        VmSession s=new VmSession();assertFalse(s.confirmForceStop(true,100));s.tryStart();s.running();assertFalse(s.confirmForceStop(false,100));assertEquals(VmSession.State.RUNNING,s.state());assertTrue(s.confirmForceStop(true,100));assertEquals(VmSession.State.STOPPING,s.state());
    }
    @Test public void failedShutdownDoesNotClaimStopped() {
        VmSession s=new VmSession();s.tryStart();s.running();s.requestShutdown(0);assertTrue(s.shutdownTimedOut(30000));assertEquals(VmSession.State.STOPPING,s.state());
    }
    @Test public void nativeReturnBlocksRestartThroughoutProcessTeardown() {
        VmSession s=new VmSession();s.tryStart();s.running();s.finishing("VM shutdown");
        assertEquals(VmSession.State.EXITING,s.state());assertFalse(s.tryStart());assertFalse(s.confirmForceStop(true,100));
    }
    @Test public void confirmedForceStopEnforcesDeadlineEvenDuringNativeTeardown() {
        VmSession s=new VmSession();s.tryStart();s.running();assertTrue(s.confirmForceStop(true,100));
        assertFalse(s.needsProcessTermination(5099));assertTrue(s.needsProcessTermination(5100));
        s.finishing("VM shutdown");assertTrue(s.needsProcessTermination(6000));
    }
    @Test public void unconfirmedForceStopNeverArmsTermination() {
        VmSession s=new VmSession();s.tryStart();s.running();s.confirmForceStop(false,100);
        assertFalse(s.needsProcessTermination(60000));
    }
    @Test public void gracefulShutdownTimeoutAloneNeverKillsTheProcess() {
        VmSession s=new VmSession();s.tryStart();s.running();s.requestShutdown(100);
        assertTrue(s.shutdownTimedOut(60000));assertFalse(s.needsProcessTermination(60000));
    }
}
