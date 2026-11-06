-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA512

Format: 3.0 (quilt)
Source: busybox
Binary: busybox, busybox-static, busybox-udeb, busybox-syslogd, udhcpc, udhcpd
Architecture: any all
Version: 1:1.35.0-4+deb12u1
Maintainer: Debian Install System Team <debian-boot@lists.debian.org>
Uploaders: Chris Boot <bootc@debian.org>, Christoph Biedl <debian.axhn@manchmal.in-ulm.de>, Michael Tokarev <mjt@tls.msk.ru>
Homepage: http://www.busybox.net
Standards-Version: 4.1.5
Vcs-Browser: https://salsa.debian.org/installer-team/busybox
Vcs-Git: https://salsa.debian.org/installer-team/busybox.git
Build-Depends: debhelper-compat (= 13), zip <!nocheck>
Package-List:
 busybox deb utils optional arch=any
 busybox-static deb shells optional arch=any
 busybox-syslogd deb utils optional arch=all
 busybox-udeb udeb debian-installer optional arch=any
 udhcpc deb net optional arch=linux-any
 udhcpd deb net optional arch=linux-any
Checksums-Sha1:
 36a1766206c8148bc06aca4e1f134016d40912d0 2480624 busybox_1.35.0.orig.tar.bz2
 b84e16f4477288383bfd5e03517337e72db7868f 68028 busybox_1.35.0-4+deb12u1.debian.tar.xz
Checksums-Sha256:
 faeeb244c35a348a334f4a59e44626ee870fb07b6884d68c10ae8bc19f83a694 2480624 busybox_1.35.0.orig.tar.bz2
 1cacbe095ef4880ea7879933c8e3c5075d1527cd6fbcb626a9b41e5daefd1a46 68028 busybox_1.35.0-4+deb12u1.debian.tar.xz
Files:
 585949b1dd4292b604b7d199866e9913 2480624 busybox_1.35.0.orig.tar.bz2
 b04ec1db694262281d93433c5184c9bb 68028 busybox_1.35.0-4+deb12u1.debian.tar.xz

-----BEGIN PGP SIGNATURE-----

iQIzBAEBCgAdFiEE/d0M/zhkJ3YwohhskWT6HRe9XTYFAmmlR3QACgkQkWT6HRe9
XTYWKA//ZmVF3+lExPCcTMl++OImAIaj1rvidu5NRCaxuYuL4S2PZJqYs14pQE8W
kNyVPzNyJTKgQHzVfDFh4pNbq6uOV+T60WHAzMr9ERnubye2AQ1SN2hPK/XhPIio
89jxA29sJtjNuXLMAu9M0RIeC79c2UIi26aALUI9p96ul0BN79LGbHBPzEtZeXjb
6LNLcf1rLDq6IlfTEz7StRt4d1qKzfj2QqOdJzQ+RhLV5f0c9nbgt0g1ocoBjlEP
xUws4BM6kKhYCMl1amm+yoJNTmJGQs9/GkO644mQgl78x3v72Tozqya6EEjlfR2Z
+dn8+UkN3gM/E+d8ehxaLaBXrw+tU+cqcrj9iR3ELnlUCcpcp/q6Yw73hmkgNEmX
5QbYm4iNC2W0VwSGRa96tOa7VBK5E+bMW6nbC/0cpznrlbdQpDmifuK9MvB9QCIk
8sxkEiaty+6z+ABHfLeOfaclWZYt4pp+MuthJGXCpdh7tS7n2bZ7nHiLgSgLf3wL
uK6LToMdQiQ0zx5InzfT5PsKR4UWJ0aiAHHEL3+s0+iyTGUFW2oPr871b9rvnx6w
XevAdXGKei/PFykaTQMaRcm/j3jle7qCV0yHtzkEy5n9LZJZsEnTKCfkjaW32c6h
IxNQQlU1r8O0kbT4pz9fYthneOLpVRQgDdbnpA/nN8J/7JAyEK0=
=Cl6j
-----END PGP SIGNATURE-----
