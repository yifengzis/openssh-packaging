#!/usr/bin/env bash
set -euo pipefail

OPENSSH_VERSION=10.3p1
download_url="https://mirrors.iflyhealth.com/OpenBSD/OpenSSH/portable/openssh-${OPENSSH_VERSION}.tar.gz"

echo "🌳 初始化 RPM 构建环境..."
rpmdev-setuptree

SPEC_FILE="openssh.spec"

SRC_TAR="openssh-${OPENSSH_VERSION}.tar.gz"

echo "📥 准备源码包..."
cp "$SPEC_FILE" ~/rpmbuild/SPECS/
wget -O ~/rpmbuild/SOURCES/"${SRC_TAR}" "${download_url}"

echo "🏗️ 开始构建..."
rpmbuild -ba ~/rpmbuild/SPECS/"${SPEC_FILE}" \
    --define "skip_x11_askpass 1"
    --define "skip_gnome_askpass 1"

echo "✅ 构建完成！"
echo "📦 二进制包: ~/rpmbuild/RPMS/$(uname -m)/openssh-custom-*.rpm"
echo "📦 源码包:   ~/rpmbuild/SRPMS/openssh-custom-*.src.rpm"

