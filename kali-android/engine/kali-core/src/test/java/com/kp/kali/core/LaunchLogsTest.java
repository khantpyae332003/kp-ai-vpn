package com.kp.kali.core;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import org.junit.*;
import org.junit.rules.TemporaryFolder;
import static org.junit.Assert.*;
public class LaunchLogsTest {
    @Rule public TemporaryFolder temp=new TemporaryFolder();
    @Test public void previousFailureSurvivesNextLaunchAndIsReadable() throws Exception {
        File log=new File(temp.getRoot(),"current.log"),previous=new File(temp.getRoot(),"previous.log");
        Files.write(log.toPath(),"qcow2: Image is corrupt".getBytes(StandardCharsets.UTF_8));
        LaunchLogs.rotate(log,previous);
        assertEquals("qcow2: Image is corrupt",LaunchLogs.tail(previous,64));
        LaunchLogs.append(log,"new launch",64);
        assertEquals("qcow2: Image is corrupt",LaunchLogs.tail(previous,64));
    }
    @Test public void logCaptureAndDisplayHaveBoundedSizeAndKeepRecentError() throws Exception {
        File log=new File(temp.getRoot(),"current.log");
        for(int n=0;n<100;n++)LaunchLogs.append(log,"long diagnostic line\n",64);
        LaunchLogs.append(log,"ERROR_BAD_DISK",64);
        assertTrue(log.length()<=64);assertTrue(LaunchLogs.tail(log,32).endsWith("ERROR_BAD_DISK"));assertTrue(LaunchLogs.tail(log,32).length()<=32);
    }
}
