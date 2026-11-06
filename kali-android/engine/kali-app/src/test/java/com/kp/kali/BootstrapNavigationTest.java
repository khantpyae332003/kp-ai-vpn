package com.kp.kali;

import android.app.Application;
import android.content.Intent;
import android.os.Looper;
import java.lang.reflect.Field;
import org.junit.After;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.LooperMode;
import org.robolectric.RobolectricTestRunner;
import static org.junit.Assert.*;
import static org.robolectric.Shadows.shadowOf;

/** Navigation-only STARTING fixture; never boots a VM or simulates guest readiness. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=29,manifest=Config.NONE,application=Application.class)
@LooperMode(LooperMode.Mode.PAUSED)
public class BootstrapNavigationTest {
    private void managedArguments(Object value)throws Exception {
        Field field=KaliRuntime.class.getDeclaredField("managedArguments");field.setAccessible(true);field.set(null,value);
    }
    @After public void cleanup()throws Exception {
        KaliRuntime.session.failed("Navigation-only fixture ended");managedArguments(null);
    }
    @Test public void firstLaunchOpensDesktopButReturningLeavesLauncherControlsAccessible()throws Exception {
        managedArguments(new String[0]);assertTrue(KaliRuntime.session.tryStart());
        ActivityController<BootstrapActivity> controller=Robolectric.buildActivity(BootstrapActivity.class).create().start().resume();
        BootstrapActivity activity=controller.get();shadowOf(Looper.getMainLooper()).idle();
        Intent first=shadowOf(activity).getNextStartedActivity();assertNotNull(first);
        assertEquals(ManagedDesktopActivity.class.getName(),first.getComponent().getClassName());
        controller.pause().resume();shadowOf(Looper.getMainLooper()).idle();
        assertNull("Returning from the managed desktop must leave the launcher and its Advanced control accessible",shadowOf(activity).getNextStartedActivity());
        controller.pause().stop().destroy();
        ActivityController<BootstrapActivity> fresh=Robolectric.buildActivity(BootstrapActivity.class).create().start().resume();
        shadowOf(Looper.getMainLooper()).idle();assertNotNull("A fresh app launch must still open the running desktop automatically",shadowOf(fresh.get()).getNextStartedActivity());
        fresh.pause().stop().destroy();
    }
}
