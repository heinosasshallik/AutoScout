#!/usr/bin/env bash
#
# Install Playwright Chromium dependencies without root access.
# Downloads .deb packages from Debian Bookworm repos and extracts
# shared libraries to /home/claude/lib.
#
# Usage: ./install_playwright_deps.sh
#
set -euo pipefail

LIB_DIR="/home/claude/lib"
WORK_DIR="/tmp/playwright_deps_$$"
CHROME_BIN="/home/claude/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome"
DEB_MIRROR="http://deb.debian.org/debian"
DIST="bookworm"

declare -a PACKAGES=(
    # Core glib stack (includes libglib-2.0, libgobject-2.0, libgio-2.0)
    "libglib2.0-0"
    "libffi8"
    "libpcre2-8-0"
    "libmount1"
    "libselinux1"
    "libblkid1"
    # NSS/NSPR
    "libnspr4"
    "libnss3"
    # ATK
    "libatk1.0-0"
    "libatk-bridge2.0-0"
    # D-Bus
    "libdbus-1-3"
    # CUPS (+ avahi deps)
    "libcups2"
    "libavahi-common3"
    "libavahi-client3"
    # X11 stack
    "libxcb1"
    "libxcb-shm0"
    "libxcb-render0"
    "libxau6"
    "libxdmcp6"
    "libx11-6"
    "libxcomposite1"
    "libxdamage1"
    "libxext6"
    "libxfixes3"
    "libxrandr2"
    "libxrender1"
    "libxi6"
    # XKB
    "libxkbcommon0"
    # AT-SPI
    "libatspi2.0-0"
    # DRM/GBM
    "libdrm2"
    "libgbm1"
    # Cairo
    "libcairo2"
    "libcairo-gobject2"
    "libpixman-1-0"
    # Pango
    "libpango-1.0-0"
    "libpangocairo-1.0-0"
    "libpangoft2-1.0-0"
    "libharfbuzz0b"
    "libfribidi0"
    "libthai0"
    "libdatrie1"
    "libgraphite2-3"
    # Audio
    "libasound2"
    # Font config
    "libfontconfig1"
    "libfreetype6"
    "libpng16-16"
    # Wayland
    "libwayland-client0"
    "libwayland-server0"
    # Additional deps
    "libexpat1"
    "libbsd0"
    "libmd0"
    "libsystemd0"
    "liblzma5"
    "libzstd1"
    "liblz4-1"
    "libcap2"
    "libgcrypt20"
    "libgpg-error0"
    "libbrotli1"
)

echo "=== Playwright Chromium Dependency Installer (no root) ==="
echo "Target lib dir: ${LIB_DIR}"
echo ""

# Create directories
mkdir -p "${LIB_DIR}"
mkdir -p "${WORK_DIR}"

# Step 1: Download the Packages index for bookworm main amd64
echo "[1/4] Downloading package index..."
PACKAGES_FILE="${WORK_DIR}/Packages"
curl -sS "${DEB_MIRROR}/dists/${DIST}/main/binary-amd64/Packages.gz" | gunzip > "${PACKAGES_FILE}"
echo "  Package index downloaded ($(wc -l < "${PACKAGES_FILE}") lines)"

# Step 2: Resolve package filenames from the index
echo "[2/4] Resolving package URLs..."
declare -a DEB_URLS=()

for pkg in "${PACKAGES[@]}"; do
    filename=$(awk -v pkg="$pkg" '
        /^Package: / { current = $2 }
        /^Filename: / { if (current == pkg) { print $2; exit } }
    ' "${PACKAGES_FILE}")

    if [ -z "$filename" ]; then
        echo "  WARNING: Package '${pkg}' not found in index, skipping"
        continue
    fi

    DEB_URLS+=("${DEB_MIRROR}/${filename}")
    echo "  ${pkg} -> $(basename "${filename}")"
done

echo "  Resolved ${#DEB_URLS[@]} packages"

# Step 3: Download and extract
echo "[3/4] Downloading and extracting .deb packages..."
cd "${WORK_DIR}"

for url in "${DEB_URLS[@]}"; do
    deb_name=$(basename "$url")
    echo -n "  ${deb_name}... "

    # Download
    curl -sS -o "${deb_name}" "$url"

    # Extract using dpkg-deb (available without root)
    extract_dir="${WORK_DIR}/extract_${deb_name}"
    mkdir -p "${extract_dir}"
    dpkg-deb -x "${deb_name}" "${extract_dir}" 2>/dev/null

    # Copy all .so files to our lib directory, preserving symlinks
    so_count=0
    while IFS= read -r -d '' sofile; do
        cp -a "$sofile" "${LIB_DIR}/" 2>/dev/null && ((so_count++)) || true
    done < <(find "${extract_dir}" -name "*.so*" -print0 2>/dev/null)

    echo "${so_count} files"

    # Clean up extracted dir and deb
    rm -rf "${extract_dir}" "${deb_name}"
done

# Step 4: Verify
echo "[4/4] Verifying chrome binary..."
echo ""
echo "Libraries in ${LIB_DIR}: $(ls -1 "${LIB_DIR}" | wc -l) files"
echo ""

# Test with ldd
echo "=== ldd check with LD_LIBRARY_PATH=${LIB_DIR} ==="
missing=$(LD_LIBRARY_PATH="${LIB_DIR}" ldd "${CHROME_BIN}" 2>&1 | grep "not found" || true)

if [ -z "$missing" ]; then
    echo "SUCCESS: All libraries resolved!"
else
    echo "Still missing:"
    echo "$missing"
    echo ""
    echo "These may need additional packages."
fi

# Try launching chrome with --version
echo ""
echo "=== Attempting chrome --version ==="
if LD_LIBRARY_PATH="${LIB_DIR}" "${CHROME_BIN}" --version --no-sandbox 2>&1; then
    echo ""
    echo "SUCCESS: Chrome binary works!"
else
    echo ""
    echo "Chrome launch returned non-zero, but may still work for Playwright."
fi

# Cleanup
rm -rf "${WORK_DIR}"

echo ""
echo "=== Done ==="
echo ""
echo "To use, set: export LD_LIBRARY_PATH=${LIB_DIR}"
echo "Or in Python:  os.environ['LD_LIBRARY_PATH'] = '${LIB_DIR}'"
