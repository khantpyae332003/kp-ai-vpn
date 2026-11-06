# Build KP Kali VM

Linux x86_64, Python 3.12+, curl/unzip, and about 5 GB free are required for the Java/APK build. Native recompilation needs considerably more space. All work belongs in this separate project, not the website checkout.

```
python3 scripts/bootstrap.py --accept-sdk-license
python3 scripts/gradle.py :kali-core:test :kali-app:assembleDebug
```

Read Google's Android SDK terms before accepting the flag. The bootstrap pins JDK17.0.17+10, Gradle7.6.4, SDK33 revision3, build-tools33.0.2 and the official Limbo6.0.1 runtime in `toolchain-lock.json`. It checks upstream checksums over verified HTTPS. The runtime hash records the fetched official artifact; it is not an independently published upstream checksum. Proxy trust uses the machine's installed CA certificates, never disabled TLS checks. Gradle dependencies are pinned in the module build files. The script respects inherited proxy routing.

Output: `engine/kali-app/build/outputs/apk/debug/kali-app-debug.apk`. This is a development APK signed with a local debug key, not a store release. Do not reuse that key for production. `:kali-core:test` runs the complete project-owned unit suite. The inherited Limbo modules do not include a unit suite. `tests/android/boot-proof.S` is a BIOS boot-sector fixture for proving native guest execution; it is explicitly not Kali.

## Original native engine and corresponding source

The Java UI and integration are built from source. The initial build packages unmodified native libraries from the official `limbo-android-x86-6.0.1-qemu-5.1.0.apk`, not binaries downloaded at Android runtime. Native source recompilation and byte-for-byte reproducibility have not been verified. The native engine is old; this is a development build for trusted local guests. It has not been verified on 16 KiB-page Android devices.

Limbo upstream commit: `887c6a68cd6b414377d7f8071bc12bbc16e59809`. Limbo's native build sources, compatibility code, makefiles and patches are in `engine/limbo-android-lib/src/main/jni/`. Original full instructions: `engine/README.developers`. External source archives, exact source revisions and SHA256 values are in `sources/`. Pixman is obtained from the Aseprite mirror at its matching release tag; other top-level libraries use their upstream GitHub repositories. The x86 firmware retained by this app matches QEMU5.1.0's checked-in firmware byte-for-byte. The matching SeaBIOS and iPXE source revisions are included.

To attempt a native rebuild on a Linux development machine:

1. Install Android NDK r23b (`23.1.7779620`), make, autoconf, automake, libtool, pkg-config, flex, bison, gettext, texinfo and rsync as described upstream. Host package and NDK installation are separate from the APK bootstrap.
2. Verify `sources/manifest.json` hashes. Extract QEMU, GLib, libffi, Pixman and SDL archives into the native JNI directory as `qemu/`, `glib/`, `libffi/`, `pixman/`, `SDL2/`. Git source archives may need their upstream autogen/autoreconf steps to generate configure/build helpers; use the release versions documented in `engine/README.developers`.
3. Extract the included `slirp`, `capstone`, `keycodemapdb`, `seabios`, `ipxe` archives into their QEMU subdirectories (`slirp`, `capstone`, `ui/keycodemapdb`, `roms/seabios`, `roms/ipxe`). x86 runtime uses SeaBIOS/VGA BIOS and iPXE only. Other architecture firmware is excluded from the app.
4. Apply the provided `qemu-5.1.0.patch`, `glib-2.56.1.patch`, and `sdl2-2.0.8.patch` with `patch -p1` in their respective source directories.
5. In the JNI directory run `make limbo NDK_ROOT=/path/to/android-ndk-r23b BUILD_HOST=arm64-v8a BUILD_GUEST=x86_64-softmmu BUILD_THREADS=4`. Inspect any required toolchain adjustments rather than disabling verification. This command is the upstream documented path and has not been run successfully in this session.
6. Rebuild the APK and verify its native contents and guest startup on a real ARM64 device. Avoid rerunning the bootstrap after a native rebuild, since it intentionally reinstalls the pinned upstream runtime.

All local modifications are identified by the separate Kali modules, `KaliMachineBridge`, `KaliRuntime`, and the service/startup-error changes. Source is provided under the original licenses. See `COPYING`, `THIRD_PARTY_NOTICES.md` and source-archive license files. This app does not include Kali OS packages or an operating-system disk.
