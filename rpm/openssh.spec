%global ver 10.3p1
%global rel 1
%global debug_package %{nil}

# OpenSSH privilege separation requires a user & group ID
%global sshd_uid    74
%global sshd_gid    74

# Portable build: link OpenSSL + zlib statically from a prebuilt prefix.
# rpmbuild --define "static_deps 1" --define "deps_prefix /path/to/prefix"
%global use_static_deps 0
%{?static_deps:%global use_static_deps 1}

# Release intentionally omits %%{?dist} — this package targets multiple
# RPM-based distros from a single static build.

Summary: The OpenSSH implementation of SSH protocol version 2.
Name: openssh
Version: %{ver}
Release: %{rel}
URL: https://www.openssh.com/portable.html
Source0: https://cdn.openbsd.org/pub/OpenBSD/OpenSSH/portable/openssh-%{version}.tar.gz
Source1: sshd.service
Source2: sshd-keygen@.service
Source3: sshd.pam
License: BSD
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Obsoletes: ssh < %{version}-%{release}
BuildRequires: perl
BuildRequires: systemd-rpm-macros
%if ! %{use_static_deps}
BuildRequires: openssl-devel >= 1.1.1
BuildRequires: zlib-devel
%endif
BuildRequires: glibc-devel, pam, pam-devel

%package clients
Summary: OpenSSH clients.
Requires: openssh = %{version}-%{release}
Obsoletes: ssh-clients < %{version}-%{release}

%package server
Summary: The OpenSSH server daemon.
Obsoletes: ssh-server < %{version}-%{release}
Requires: openssh = %{version}-%{release}
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
SSH (Secure SHell) is a program for logging into and executing
commands on a remote machine. SSH is intended to replace rlogin and
rsh, and to provide secure encrypted communications between two
untrusted hosts over an insecure network. X11 connections and
arbitrary TCP/IP ports can also be forwarded over the secure channel.

OpenSSH is OpenBSD's version of the last free version of SSH, bringing
it up to date in terms of security and features, as well as removing
all patented algorithms to separate libraries.

This package includes the core files necessary for both the OpenSSH
client and server. To make this package useful, you should also
install openssh-clients, openssh-server, or both.

%description clients
OpenSSH is a free version of SSH (Secure SHell), a program for logging
into and executing commands on a remote machine. This package includes
the clients necessary to make encrypted connections to SSH servers.
You'll also need to install the openssh package on OpenSSH clients.

%description server
OpenSSH is a free version of SSH (Secure SHell), a program for logging
into and executing commands on a remote machine. This package contains
the secure shell daemon (sshd). The sshd daemon allows SSH clients to
securely connect to your SSH server. You also need to have the openssh
package installed.

%prep
%setup -q

%build

%configure \
	--sysconfdir=%{_sysconfdir}/ssh \
	--libexecdir=%{_libexecdir}/openssh \
	--datadir=%{_datadir}/openssh \
	--with-default-path=/usr/local/bin:/bin:/usr/bin \
	--with-superuser-path=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin \
	--with-privsep-path=%{_var}/empty/sshd \
%if %{use_static_deps}
	--with-ssl-dir=%{deps_prefix} \
	--with-zlib=%{deps_prefix} \
%endif
	--with-pam


%if %{use_static_deps}
perl -pi -e "s|-lcrypto\b|%{deps_prefix}/lib/libcrypto.a|g" Makefile
perl -pi -e "s|-lssl\b|%{deps_prefix}/lib/libssl.a|g" Makefile
perl -pi -e "s|-lz\b|%{deps_prefix}/lib/libz.a|g" Makefile
%endif

make

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p -m755 $RPM_BUILD_ROOT%{_sysconfdir}/ssh
mkdir -p -m755 $RPM_BUILD_ROOT%{_libexecdir}/openssh
mkdir -p -m755 $RPM_BUILD_ROOT%{_var}/empty/sshd

make install DESTDIR=$RPM_BUILD_ROOT

install -d $RPM_BUILD_ROOT/etc/pam.d/
install -d $RPM_BUILD_ROOT%{_libexecdir}/openssh
install -m644 %{_sourcedir}/sshd.pam $RPM_BUILD_ROOT/etc/pam.d/sshd
install -d $RPM_BUILD_ROOT%{_unitdir}
install -m644 %{_sourcedir}/sshd.service $RPM_BUILD_ROOT%{_unitdir}/sshd.service
install -m644 %{_sourcedir}/sshd-keygen@.service $RPM_BUILD_ROOT%{_unitdir}/sshd-keygen@.service

rm -rf $RPM_BUILD_ROOT%{_mandir}

%clean
rm -rf $RPM_BUILD_ROOT

%pre server
getent group sshd >/dev/null || \
    %{_sbindir}/groupadd -r -g %{sshd_gid} sshd 2>/dev/null || \
    %{_sbindir}/groupadd -r sshd
getent passwd sshd >/dev/null || \
    %{_sbindir}/useradd -r -u %{sshd_uid} -g sshd \
        -d /var/empty/sshd -s /sbin/nologin \
        -c "Privilege-separated SSH" sshd 2>/dev/null || \
    %{_sbindir}/useradd -r -g sshd \
        -d /var/empty/sshd -s /sbin/nologin \
        -c "Privilege-separated SSH" sshd

%post server
%systemd_post sshd.service

%preun server
%systemd_preun sshd.service

%postun server
%systemd_postun_with_restart sshd.service

%files
%defattr(-,root,root)
%attr(0755,root,root) %{_bindir}/scp
%attr(0755,root,root) %dir %{_sysconfdir}/ssh
%attr(0600,root,root) %config(noreplace) %{_sysconfdir}/ssh/moduli
%attr(0755,root,root) %{_bindir}/ssh-keygen
%attr(0755,root,root) %dir %{_libexecdir}/openssh
%attr(4711,root,root) %{_libexecdir}/openssh/ssh-keysign
%attr(0755,root,root) %{_libexecdir}/openssh/ssh-pkcs11-helper
%attr(0755,root,root) %{_libexecdir}/openssh/ssh-sk-helper

%files clients
%defattr(-,root,root)
%attr(0755,root,root) %{_bindir}/ssh
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/ssh/ssh_config
%attr(0755,root,root) %{_bindir}/ssh-agent
%attr(0755,root,root) %{_bindir}/ssh-add
%attr(0755,root,root) %{_bindir}/ssh-keyscan
%attr(0755,root,root) %{_bindir}/sftp

%files server
%defattr(-,root,root)
%dir %attr(0111,root,root) %{_var}/empty/sshd
%attr(0755,root,root) %{_sbindir}/sshd
%attr(0755,root,root) %{_libexecdir}/openssh/sshd-auth
%attr(0755,root,root) %{_libexecdir}/openssh/sshd-session
%attr(0755,root,root) %{_libexecdir}/openssh/sftp-server
%attr(0755,root,root) %dir %{_sysconfdir}/ssh
%attr(0600,root,root) %config(noreplace) %{_sysconfdir}/ssh/sshd_config
%attr(0644,root,root) %config(noreplace) /etc/pam.d/sshd
%attr(0644,root,root) %{_unitdir}/sshd.service
%attr(0644,root,root) %{_unitdir}/sshd-keygen@.service

