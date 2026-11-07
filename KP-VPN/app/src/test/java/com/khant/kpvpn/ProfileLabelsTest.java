package com.khant.kpvpn;
import org.junit.Test;
import static org.junit.Assert.*;
public class ProfileLabelsTest {
 @Test public void infersArchiveFolders(){ProfileLabels p=ProfileLabels.infer("TH/AIS/nopro/server.conf","AUTO","");assertEquals("TH",p.country);assertEquals("AIS",p.operator);assertEquals("nopro",p.plan);}
 @Test public void explicitLabelsWin(){ProfileLabels p=ProfileLabels.infer("AIS.conf","MM","MPT");assertEquals("MM",p.country);assertEquals("MPT",p.operator);}
 @Test public void avoidsSubstringCarrierMatches(){assertEquals("GLOBAL",ProfileLabels.infer("chair.conf","AUTO","").country);}
 @Test public void unknownAndLegacyUseGlobal(){assertEquals("GLOBAL",ProfileLabels.infer("server.conf","OTHER","").country);assertEquals("standard",ProfileLabels.infer("server.conf","AUTO","").plan);}
 @Test public void recognizesMyanmarAndNoPro(){ProfileLabels p=ProfileLabels.infer("MM/ATOM/no-pro.conf","AUTO","");assertEquals("MM",p.country);assertEquals("ATOM",p.operator);assertEquals("nopro",p.plan);}
}
