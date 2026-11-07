package com.khant.kpvpn;

import java.util.Locale;
import java.util.regex.Pattern;

/** Filename labels are organizational hints, never carrier compatibility claims. */
public final class ProfileLabels {
 public final String country,operator,plan;
 private ProfileLabels(String c,String o,String p){country=c;operator=o;plan=p;}
 private static boolean word(String s,String words){return Pattern.compile("(^|[^a-z0-9])("+words+")([^a-z0-9]|$)").matcher(s).find();}
 public static ProfileLabels infer(String filename,String selectedCountry,String selectedOperator){
  String s=filename.toLowerCase(Locale.ROOT),c=selectedCountry,o=selectedOperator;
  if(c.equals("AUTO")){
   if(word(s,"ais|true|dtac|th|thailand")){c="TH";o=word(s,"ais")?"AIS":word(s,"true")?"True":word(s,"dtac")?"dtac":"";}
   else if(word(s,"mpt|atom|telenor|mytel|ooredoo|mm|myanmar")){c="MM";o=word(s,"mpt")?"MPT":word(s,"atom|telenor")?"ATOM":word(s,"mytel")?"Mytel":word(s,"ooredoo")?"Ooredoo":"";}
   else{c="GLOBAL";o="";}
  }
  if(!c.equals("TH")&&!c.equals("MM"))c="GLOBAL";
  return new ProfileLabels(c,o,word(s,"nopro|no[ _-]?pro")?"nopro":"standard");
 }
 private ProfileLabels(){this("GLOBAL","","standard");}
}
