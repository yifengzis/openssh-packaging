#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# openssh 
OPENSSH_VERSION=10.3p1
OPENSSH_DOWNLOAD_URL="https://mirrors.iflyhealth.com/OpenBSD/OpenSSH/portable/openssh-${OPENSSH_VERSION}.tar.gz"
OPENSSH_SHA256="56682a36bb92dcf4b4f016fd8ec8e74059b79a8de25c15d670d731e7d18e45f4"

# openssl
OPENSSL_VERSION=3.5.6
# OPENSSL_DOWNLOAD_URL="https://www.openssl.org/source/openssl-${OPENSSL_VERSION}.tar.gz"
OPENSSL_DOWNLOAD_URL="https://mirrors.iflyhealth.com/github-release/openssl/openssl/openssl-${OPENSSL_VERSION}.tar.gz"
OPENSSL_SHA256_URL="https://mirrors.iflyhealth.com/github-release/openssl/openssl/openssl-${OPENSSL_VERSION}.tar.gz.sha256"
# zlib
ZLIB_VERSION=1.3.2
ZLIB_DOWNLOAD_URL="https://mirrors.iflyhealth.com/github-release/madler/zlib/zlib-${ZLIB_VERSION}.tar.gz"
ZLIB_SHA256_URL="https://mirrors.iflyhealth.com/github-release/madler/zlib/zlib-${ZLIB_VERSION}.tar.gz.sha256"

RPM_TOPDIR="$SCRIPT_PATH/rpmbuild"
DEPS_PREFIX="$SCRIPT_PATH/openssh-deps"
BUILD_DIR="$SCRIPT_PATH/openssh-deps-build"

/bin/rm -rf "$RPM_TOPDIR" "$DEPS_PREFIX" "$BUILD_DIR"

get_openssl_target() {
    case "$(uname -m)" in
        x86_64)      echo "linux-x86_64" ;;
        aarch64)     echo "linux-aarch64" ;;
        ppc64le)     echo "linux-ppc64le" ;;
        s390x)       echo "linux64-s390x" ;;
        loongarch64) echo "linux64-loongarch64" ;;
        riscv64)     echo "linux64-riscv64" ;;
        *) echo "unsupported arch: $(uname -m)" >&2; exit 1 ;;
    esac
}

build_static_deps() {
    local build_dir="$BUILD_DIR"
    local deps_prefix="$DEPS_PREFIX"
    echo "构建静态 OpenSSL + zlib (DEPS_PREFIX=$deps_prefix)..."
    mkdir -p "$build_dir" "$deps_prefix"

    echo "==> zlib $ZLIB_VERSION"
    cd "$build_dir"
    [ -f "zlib-${ZLIB_VERSION}.tar.gz" ] || wget -O "zlib-${ZLIB_VERSION}.tar.gz" "$ZLIB_DOWNLOAD_URL"
    curl -fsSL "$ZLIB_SHA256_URL" | sha256sum -c
    rm -rf "zlib-${ZLIB_VERSION}"
    tar xzf "zlib-${ZLIB_VERSION}.tar.gz"
    cd "zlib-${ZLIB_VERSION}"
    CFLAGS="-fPIC -O2" ./configure --static --prefix="$deps_prefix"
    make -j$(nproc)
    make install
    # Drop any shared libs that might exist so OpenSSH can't accidentally link dynamic.
    rm -f "$deps_prefix/lib/"libz.so*

    echo "==> openssl $OPENSSL_VERSION"
    cd "$build_dir"
    [ -f "openssl-${OPENSSL_VERSION}.tar.gz" ] || wget -O "openssl-${OPENSSL_VERSION}.tar.gz" "$OPENSSL_DOWNLOAD_URL"
    curl -fsSL "$OPENSSL_SHA256_URL" | sha256sum -c
    rm -rf "openssl-${OPENSSL_VERSION}"
    tar xzf "openssl-${OPENSSL_VERSION}.tar.gz"
    cd "openssl-${OPENSSL_VERSION}"
    ./Configure "$(get_openssl_target)" no-shared no-tests -fPIC \
        --prefix="$deps_prefix" \
        --openssldir="$deps_prefix/ssl" \
        --libdir=lib
    make -j$(nproc)
    make install_sw

    echo "==> done"
    ls -lh "$deps_prefix/lib/libcrypto.a" "$deps_prefix/lib/libssl.a" "$deps_prefix/lib/libz.a"

}

build_rpm() {
    echo "🌳 初始化 RPM 构建环境..."
    mkdir -p "$RPM_TOPDIR"/{SPECS,SOURCES}

    local spec_file="$SCRIPT_PATH/openssh.spec"
    local src_tar="openssh-${OPENSSH_VERSION}.tar.gz"

    echo "📥 准备源码包..."
    cp "$spec_file" "$RPM_TOPDIR/SPECS/"
    cp "$SCRIPT_PATH/sshd.service" "$RPM_TOPDIR/SOURCES/"
    cp "$SCRIPT_PATH/sshd-keygen@.service" "$RPM_TOPDIR/SOURCES/"
    cp "$SCRIPT_PATH/sshd.pam" "$RPM_TOPDIR/SOURCES/"
    wget -O "$RPM_TOPDIR/SOURCES/${src_tar}" "${OPENSSH_DOWNLOAD_URL}"
    sha256sum -c <(echo "${OPENSSH_SHA256}  ${RPM_TOPDIR}/SOURCES/${src_tar}")

    echo "🏗️ 开始构建..."
    rpmbuild -bb "$RPM_TOPDIR/SPECS/openssh.spec" \
        --define "_topdir $RPM_TOPDIR" \
        --define "static_deps 1" \
        --define "deps_prefix $DEPS_PREFIX"

    echo "✅ 构建完成！"
    echo "📦 二进制包: $RPM_TOPDIR/RPMS/$(uname -m)/openssh-*.rpm"
}

main() {
    build_static_deps
    build_rpm
}

main "$@"
