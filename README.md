# openssh-packaging

为多种 RPM 系发行版构建**通用** OpenSSH 二进制包的脚本，OpenSSL 与 zlib 静态链接进二进制，避免运行时依赖宿主机的版本。

## 用法

```bash
bash rpm/build_rpm.sh
```

构建产物：`rpm/rpmbuild/RPMS/$(uname -m)/openssh-*.rpm`

每次运行都从零构建，不复用缓存。

## 适用范围

- RPM 系发行版：RHEL/AlmaLinux/Rocky 8+、Fedora、openSUSE、Anolis、UOS、Kylin 等
- 架构：x86_64、aarch64、ppc64le、s390x、loongarch64、riscv64
- `Release` 不带 `%{?dist}`，单一构建产物可在多发行版安装

## 已知限制

- 不带 libedit：`sftp` 与 `ssh` 客户端没有命令行编辑/历史功能
- 不带 GSSAPI/Kerberos、SELinux、X11 forward client、LDAP
- 静态链 OpenSSL 后无法跟随宿主 OpenSSL 安全更新，请关注上游 advisory 后重新构建

## 主机依赖

构建机需要：`gcc`、`make`、`perl`、`wget`、`curl`、`tar`、`rpm-build`、`pam-devel`、`systemd-rpm-macros`。
