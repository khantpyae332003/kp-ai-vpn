#!/usr/bin/env bash
set -euo pipefail
# Run from the KP-VPN project root after installing Debian/Ubuntu fonts-noto-core.
font_file=/usr/share/fonts/truetype/noto/NotoSansMyanmar-Regular.ttf
test -f "$font_file"
mkdir -p app/src/main/assets/fonts
cp "$font_file" app/src/main/assets/fonts/Myanmar.ttf
cp /usr/share/doc/fonts-noto-core/copyright app/src/main/assets/fonts/NOTICE.txt
