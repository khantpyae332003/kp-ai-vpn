# KP VPN — Android 0.1.0

**စမ်းသပ်ဗားရှင်း။ APK build နှင့် unit tests အောင်ထားသည်။ ဖုန်းပေါ် VPN ချိတ်ဆက်စမ်းသပ်မှု ကျန်သေးသည်။**

ဖုန်းမှာ WireGuard config များကို စုစည်းပြီး ချိတ်ဆက်သုံးနိုင်ရန် Android project အသစ်ဖြစ်သည်။ Android 8.0 နှင့်အထက်အတွက် ရေးထားသည်။

## ပါဝင်သော code

- WireGuard tunnel library နဲ့ VPN connect / disconnect
- Android VPN consent နှင့် foreground notification မှ disconnect
- QR မှ WireGuard config ဖတ်ခြင်း
- .conf ဖိုင်အများအပြား၊ .conf ပါသော ZIP နဲ့ စာသားအများအပြား ထည့်ခြင်း
- Config အများဆုံး 2,000; စုစုပေါင်း config စာသား 16 MiB; တစ်ခု 128 KiB
- ထပ်နေသော canonical config များ SHA-256 နဲ့ဖယ်ခြင်း
- ထိုင်း / မြန်မာ / အခြား နိုင်ငံခွဲခြင်း; carrier label ကို ကိုယ်တိုင်ရွေးရန်
- ရှာဖွေခြင်း၊ အကြိုက်ဆုံး၊ ဖျက်ခြင်း၊ စာရင်းအပိုင်းလိုက်ပြခြင်း
- Android Keystore + AES-GCM ဖြင့် config သိမ်းခြင်း; atomic writes; cloud backup ပိတ်ထားခြင်း
- Config private key ကို WebView state/notifications/error messages ထဲ မပို့ခြင်း
- Traffic byte counters; tunnel UP သည် internet reachability သို့မဟုတ် handshake success ဟုမဆိုလို
- Offline bundled Burmese UI; no advertising, analytics, login or subscription fetch

## သိထားရန်

Server သို့မဟုတ် အသုံးပြုနိုင်သော config မပါသေးပါ။ မိမိယုံကြည်သော provider/server ထံမှ WireGuard config လိုအပ်သည်။ SIM ပေါ်မူတည်ပြီး အခမဲ့ဒေတာ ရမည်ဟု မဆိုလိုပါ။ Carrier labels သည် compatibility testing မဟုတ်ပါ။

WireGuard တစ်မျိုးသာ ချိတ်ဆက်နိုင်သည်။ VMess, VLESS, Shadowsocks, Trojan, OpenVPN, subscription URLs, automatic server collection, automatic failover, QR export နှင့် always-on/killswitch သည် ဤဗားရှင်းတွင် မပါသေးပါ။ Config ကို raw .conf format အဖြစ် QR ထဲ ထည့်ထားရမည်။

Config များဖုန်းထဲတွင် သိမ်းသော်လည်း VPN သုံးချိန် network traffic သည် မိမိရွေးထားသော remote VPN server မှတစ်ဆင့် သွားမည်။ Uninstall / Clear data လုပ်လျှင် သိမ်းထားသော config ဆုံးရှုံးမည်။ မူရင်း config ကို ကိုယ်တိုင်လုံခြုံစွာ ထိန်းသိမ်းပါ။

## APK ထုတ်ရန် — ဖုန်းကနေ GitHub

1. Project root ထဲက ဖိုင်များနှင့် `.github/workflows/android.yml` ကို repo ထဲ ထည့်ပါ။ ZIP ဖိုင်တစ်ခုတည်း upload လုပ်ခြင်းက build မလုပ်နိုင်ပါ။
2. GitHub → Actions → **Build KP VPN APK** → Run workflow။ Push လုပ်လျှင်လည်း စတင်မည်။
3. အောင်မြင်ပြီးလျှင် **KP-VPN-APK** artifact ZIP ကို ဒေါင်းလုဒ်ဆွဲပါ။
4. ZIP ဖြည်ပြီး `KP-VPN-0.1.0-debug.apk` ကို install လုပ်ပါ။
5. App → ထည့်မယ် → config ဖိုင်/QR ထည့်ပါ → config ရွေးပါ → ချိတ်ဆက်ခလုတ် → Android VPN ခွင့်ပြုပါ။

Debug APK သည် စမ်းသပ်ရန်ဖြစ်သည်။ Build တစ်ခါနှင့်တစ်ခါ debug signing key ပြောင်းနိုင်သည်။ အဆက်မပြတ် update ထုတ်ရန် stable release keystore ကို သီးသန့်စီစဉ်ရမည်။

## Local build

JDK 17, Gradle 8.13, Android SDK platform 36 / build-tools 35.0.0. Myanmar font အတွက် Debian/Ubuntu `fonts-noto-core` package ကို install လုပ်ပြီး project root မှ `bash scripts/prepare-font.sh` run ပါ။ CI က အလိုအလျောက် လုပ်ပေးသည်။

```sh
node --test tests/*.cjs
gradle testDebugUnitTest lintDebug assembleDebug
```

Gradle wrapper binary မပါ။ CI က pinned Gradle version ကို setup လုပ်ပေးသည်။ Native dependencies are resolved from Maven Central / Google Maven; binaries are not vendored.

## Validation

See `docs/VALIDATION.md` for actual checks and remaining device tests. A UI preview is not a VPN connection test.

## Official references

- https://www.wireguard.com/embedding/
- https://central.sonatype.com/artifact/com.wireguard.android/tunnel/1.0.20260102
- https://developer.android.com/develop/connectivity/vpn
- https://github.com/journeyapps/zxing-android-embedded

This project is an independent app; it is not the official WireGuard app. Dependency licenses remain with their authors. See `NOTICE.md`.
