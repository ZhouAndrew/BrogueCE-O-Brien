#!/usr/bin/env bash
set -euo pipefail

SDL2_VERSION=2.32.10
SDL2_SHA256=5f5993c530f084535c65a6879e9b26ad441169b3e25d789d83287040a9ca5165
SDL2_IMAGE_VERSION=2.8.12
SDL2_IMAGE_SHA256=393f5efb50536ec13ca4f4affb69cc9966d3c3f969e6c5e701faddf9f9785381

PREFIX="${BROGUE_SDL_PREFIX:-${RUNNER_TEMP:-/tmp}/brogue-sdl2}"
WORK="${RUNNER_TEMP:-/tmp}/brogue-sdl2-build"

case "$(uname -m)" in
  arm64)
    TARGET="${MACOSX_DEPLOYMENT_TARGET:-11.0}"
    ;;
  x86_64)
    TARGET="${MACOSX_DEPLOYMENT_TARGET:-10.13}"
    ;;
  *)
    echo "Unsupported macOS architecture: $(uname -m)" >&2
    exit 2
    ;;
esac

export MACOSX_DEPLOYMENT_TARGET="$TARGET"
export PATH="$PREFIX/bin:$PATH"
export PKG_CONFIG_PATH="$PREFIX/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"

rm -rf "$WORK" "$PREFIX"
mkdir -p "$WORK" "$PREFIX"
cd "$WORK"

download_verify() {
  local url="$1" out="$2" sha="$3"
  curl --retry 3 --retry-delay 2 -fL "$url" -o "$out"
  printf '%s  %s\n' "$sha" "$out" | shasum -a 256 -c -
}

download_verify   "https://github.com/libsdl-org/SDL/releases/download/release-${SDL2_VERSION}/SDL2-${SDL2_VERSION}.tar.gz"   "SDL2-${SDL2_VERSION}.tar.gz"   "$SDL2_SHA256"
tar -xzf "SDL2-${SDL2_VERSION}.tar.gz"
cd "SDL2-${SDL2_VERSION}"
./configure --prefix="$PREFIX" --without-x
make -j"$(sysctl -n hw.ncpu)"
make install

cd "$WORK"
download_verify   "https://github.com/libsdl-org/SDL_image/releases/download/release-${SDL2_IMAGE_VERSION}/SDL2_image-${SDL2_IMAGE_VERSION}.tar.gz"   "SDL2_image-${SDL2_IMAGE_VERSION}.tar.gz"   "$SDL2_IMAGE_SHA256"
tar -xzf "SDL2_image-${SDL2_IMAGE_VERSION}.tar.gz"
cd "SDL2_image-${SDL2_IMAGE_VERSION}"
./configure   --prefix="$PREFIX"   --enable-stb-image   --disable-avif   --disable-jxl   --disable-tif   --disable-webp   --disable-tests
make -j"$(sysctl -n hw.ncpu)"
make install

"$PREFIX/bin/sdl2-config" --version
test -f "$PREFIX/lib/libSDL2.dylib" -o -f "$PREFIX/lib/libSDL2-2.0.0.dylib"
ls -l "$PREFIX/lib"/libSDL2* "$PREFIX/lib"/libSDL2_image*

if [[ -n "${GITHUB_ENV:-}" ]]; then
  {
    echo "BROGUE_SDL_PREFIX=$PREFIX"
    echo "MACOSX_DEPLOYMENT_TARGET=$TARGET"
  } >> "$GITHUB_ENV"
fi

echo "Built native SDL2 $SDL2_VERSION + SDL2_image $SDL2_IMAGE_VERSION"
echo "prefix=$PREFIX"
echo "MACOSX_DEPLOYMENT_TARGET=$TARGET"
