# Source and licenses

This is an independent modified Limbo-based application, not an official Kali product.

- Limbo6.0.1: Max Kastanas and contributors, GPL-2.0-or-later. Upstream `https://github.com/limboemu/limbo`, commit `887c6a68cd6b414377d7f8071bc12bbc16e59809`. Source and patches in `engine/`. `COPYING` is the upstream GPLv2 text. Existing copyright and license headers are retained.
- QEMU5.1.0: QEMU contributors, GPLv2 and component-specific compatible licenses. Full source archive and matching submodule source in `sources/`.
- GLib2.56.1: GNOME contributors, LGPL-2.1-or-later and component-specific notices.
- SDL2 2.0.8: SDL contributors, zlib license.
- Pixman0.40.0: Pixman contributors, MIT-family licenses; source from the matching Aseprite mirror release tag.
- libffi3.3: libffi contributors, MIT license.
- SeaBIOS and VGA BIOS: matching QEMU5.1.0 source revision, LGPLv3-family/component-specific notices.
- iPXE e1000 firmware: matching QEMU5.1.0 source revision, GPLv2 and component-specific notices.
- capstone, libslirp and keycodemapdb: included matching QEMU source revisions, with their own embedded license texts.
- AndroidX/Material libraries: Apache-2.0, notices retained through the Android build dependency metadata.
- Included upstream Android artwork: GNOME/Limbo contributors, GPLv2 as described in the original developer README.

The exact original native artifact URL and SHA256 are in `toolchain-lock.json`; libraries are unmodified and loaded from the APK's normal native-library installation directory. Source-archive URLs, commits and hashes are in `sources/manifest.json`. The source archives and native-build makefiles/patches accompany the app; see `BUILDING.md` for build details and the unverified native-rebuild limitation. Preserve this source package and these notices when redistributing. No third-party license is replaced by this summary; consult the license texts inside each source archive and `engine/limbo-android-lib/src/main/assets/LICENSE`.

New Kali-specific Java code is provided under GPL-2.0-or-later. No Kali disk image or Kali package is redistributed here.

## Automatic desktop boot payload (0.2.0)

Debian Linux6.1.190 (GPL-2.0 with component exceptions), BusyBox1.35 (GPL-2.0), e2fsprogs1.47 (GPL/LGPL component licenses), util-linux2.38 (component licenses) and glibc2.36 (LGPL-2.1 and component exceptions) supply the boot payload. Matching Debian source packages and SHA256SUMS are in `sources/guest/`; each archive includes its authoritative licenses and package build rules. Debian package rebuild suffixes are recorded in docs/automatic-setup-build.md.

Kasm Technologies publishes the pinned Kali-based desktop layers downloaded directly by the app. These layers are not redistributed inside this APK or source archive. The vendor and Kali trademarks remain their owners'. The app is unaffiliated with Kasm Technologies, Kali Linux and Offensive Security. See docs/automatic-setup-build.md for immutable producer identity and kernel provenance.
