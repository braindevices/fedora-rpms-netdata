# libuv-devel and Judy-devel are not available on el8 s390x
%if 0%{?rhel} && 0%{?rhel} == 8
ExcludeArch: s390x
%endif

# Because libnetfilter_acct-devel is not available in el7
%if 0%{?rhel} && 0%{?rhel} >= 7
%bcond_with netfilteracct
%else
%bcond_without netfilteracct
%endif

# Because cups is too old in el7
%if 0%{?rhel} && 0%{?rhel} <= 7
%bcond_with cups
%else
%bcond_without cups
%endif

%if 0%{?rhel} && 0%{?rhel} <= 7
# This is temporary and should eventually be resolved. This bypasses
# the default rhel __os_install_post which throws a python compile
# error.
%global __os_install_post %{nil}
%endif

# We use some plugins which need suid
%global  _hardened_build 1

# Build release candidate
%global upver        1.26.0
#global rcver        rc0

Name:           netdata
Version:        %{upver}%{?rcver:~%{rcver}}
Release:        3%{?dist}
Summary:        Real-time performance monitoring
# For a breakdown of the licensing, see LICENSE-REDISTRIBUTED.md
License:        GPLv3 and GPLv3+ and ASL 2.0 and CC-BY and MIT and WTFPL 
URL:            https://github.com/%{name}/%{name}/
Source0:        https://github.com/%{name}/%{name}/archive/v%{upver}%{?rcver:-%{rcver}}/%{name}-%{upver}%{?rcver:-%{rcver}}.tar.gz
Source1:        netdata.tmpfiles.conf
Source2:        netdata.init
Source3:        netdata.conf
Patch0:         netdata-fix-shebang-1.23.1.patch
%if 0%{?fedora}
# Remove embedded font
Patch10:        netdata-remove-fonts-1.19.0.patch
%endif

BuildRequires:  zlib-devel
BuildRequires:  git
BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  pkgconfig
BuildRequires:  libuuid-devel
BuildRequires:  freeipmi-devel
BuildRequires:  httpd
BuildRequires:  cppcheck
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  libuv-devel
BuildRequires:  Judy-devel
BuildRequires:  lz4-devel
BuildRequires:  openssl-devel
BuildRequires:  libmnl-devel
BuildRequires:  make
BuildRequires:  libcurl-devel
BuildRequires:  snappy-devel
BuildRequires:  protobuf-devel
BuildRequires:  protobuf-c-devel

# Cloud client
# BuildRequires:  mosquitto-devel
# BuildRequires:  libwebsockets-devel
# BuildRequires:  json-c-devel
# BuildRequires:  libpfm-devel
# BuildRequires:  libcap-devel

%if %{with cups}
BuildRequires:  cups-devel
%endif
%if %{with netfilteracct}
BuildRequires:  libnetfilter_acct-devel
%endif
# Only Fedora
%if 0%{?fedora}
BuildRequires:  python3
BuildRequires:  autoconf-archive
BuildRequires:  autogen
BuildRequires:  findutils
%else
# Only CentOS
BuildRequires:  python2
%endif

BuildRequires:  systemd

Requires:       nodejs
Requires:       curl
Requires:       nc
Requires:       snappy
Requires:       protobuf-c
Requires:       protobuf
%if 0%{?fedora}
Requires:       glyphicons-halflings-fonts
%endif

Requires:       %{name}-data = %{version}-%{release}
Requires:       %{name}-conf = %{version}-%{release}

%description
netdata is the fastest way to visualize metrics. It is a resource
efficient, highly optimized system for collecting and visualizing any
type of realtime time-series data, from CPU usage, disk activity, SQL
queries, API calls, web site visitors, etc.

netdata tries to visualize the truth of now, in its greatest detail,
so that you can get insights of what is happening now and what just
happened, on your systems and applications.

%package data
BuildArch:      noarch
Summary:        Data files for netdata

%description data
Data files for netdata

%package conf
BuildArch:      noarch
Summary:        Configuration files for netdata

%description conf
Configuration files for netdata

%package freeipmi
Summary:        FreeIPMI plugin for netdata
Requires:       %{name}%{?_isa} = %{version}-%{release}
License:        GPLv3

%description freeipmi
freeipmi plugin for netdata

%prep
%setup -qn %{name}-%{upver}%{?rcver:-%{rcver}}
%patch0 -p1
%if 0%{?fedora}
# Remove embedded font(added in requires)
%patch10 -p1
rm -rf web/fonts
%endif

%build
autoreconf -ivf
%configure \
    --enable-plugin-freeipmi \
%if %{with netfilteracct}
    --enable-plugin-nfacct \
%endif
%if %{with cups}
    --enable-plugin-cups \
%endif
    --with-zlib \
    --with-math \
    --with-user=netdata
    
%make_build

%install
%make_install
find %{buildroot} -name '.keep' -delete
# Unit file
mkdir -p %{buildroot}%{_unitdir}
mkdir -p %{buildroot}%{_tmpfilesdir}
mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d
install -Dp -m 0644 system/netdata.service %{buildroot}%{_unitdir}/%{name}.service
install -p -m 0644 %{SOURCE1} %{buildroot}%{_tmpfilesdir}/%{name}.conf
install -Dp -m 0644 system/netdata.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/netdata

mkdir -p %{buildroot}%{_localstatedir}/lib/%{name}
mkdir -p %{buildroot}%{_localstatedir}/log/%{name}
mkdir -p %{buildroot}%{_localstatedir}/cache/%{name}

mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d
install -p -m 0644 %{SOURCE3} %{buildroot}%{_sysconfdir}/%{name}/
install -p -m 0644 system/netdata.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
# Conf files must be in /etc, dixit FHS 
mv %{buildroot}%{_libdir}/%{name}/conf.d %{buildroot}%{_sysconfdir}/%{name}/
# Scripts must not be in /etc
mv %{buildroot}%{_sysconfdir}/%{name}/edit-config %{buildroot}%{_libexecdir}/%{name}/edit-config
# Fix EOL
sed -i -e 's/\r//' %{buildroot}%{_datadir}/%{name}/web/lib/tableExport-1.6.0.min.js
# Delete useless hidden dir
rm -rf %{buildroot}%{_datadir}/%{name}/web/.well-known
# Delete useless file (ubuntu)
rm -f %{buildroot}%{_sysconfdir}/%{name}/conf.d/ebpf_kernel_reject_list.txt

%check
./cppcheck.sh

%pre
getent group netdata > /dev/null || groupadd -r netdata
getent passwd netdata > /dev/null || useradd -r -g netdata -c "NetData User" -s /sbin/nologin -d /var/log/%{name} netdata

%post
%systemd_post %{name}.service
echo "The current config file can be downloaded with the following command"
echo "curl -o /etc/netdata/netdata.conf http://localhost:19999/netdata.conf"

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

%files
%doc README.md CHANGELOG.md CODE_OF_CONDUCT.md CONTRIBUTORS.md HISTORICAL_CHANGELOG.md
%license LICENSE REDISTRIBUTED.md
%{_sbindir}/%{name}
%{_sbindir}/%{name}-claim.sh
%{_sbindir}/%{name}cli
%{_libexecdir}/%{name}
%{_unitdir}/%{name}.service
%{_tmpfilesdir}/%{name}.conf
%caps(cap_dac_read_search,cap_sys_ptrace=ep) %attr(0750,root,netdata) %{_libexecdir}/%{name}/plugins.d/apps.plugin
%caps(cap_setuid=ep) %attr(4750,root,netdata) %{_libexecdir}/%{name}/plugins.d/cgroup-network
%attr(0750,root,netdata) %{_libexecdir}/%{name}/plugins.d/cgroup-network-helper.sh
%caps(cap_setuid=ep) %attr(4750,root,netdata) %{_libexecdir}/%{name}/plugins.d/perf.plugin
%caps(cap_setuid=ep) %attr(4750,root,netdata) %{_libexecdir}/%{name}/plugins.d/slabinfo.plugin
%if %{with cups}
%attr(0750,root,netdata) %{_libexecdir}/%{name}/plugins.d/cups.plugin
%endif
%exclude %{_libexecdir}/%{name}/plugins.d/freeipmi.plugin
%attr(0755, netdata, netdata) %{_localstatedir}/lib/%{name}
%attr(0755, netdata, netdata) %dir %{_localstatedir}/cache/%{name}
%attr(0755, netdata, netdata) %dir %{_localstatedir}/log/%{name}
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}

%files conf
%doc README.md
%license LICENSE REDISTRIBUTED.md
%dir %{_sysconfdir}/%{name}
%dir %{_sysconfdir}/%{name}/conf.d
%dir %{_sysconfdir}/%{name}/conf.d/charts.d
%dir %{_sysconfdir}/%{name}/conf.d/health.d
%dir %{_sysconfdir}/%{name}/conf.d/python.d
%dir %{_sysconfdir}/%{name}/conf.d/statsd.d
%config(noreplace) %{_sysconfdir}/%{name}/%{name}.conf
%config(noreplace) %{_sysconfdir}/%{name}/conf.d/*.conf
%config(noreplace) %{_sysconfdir}/%{name}/conf.d/charts.d/*.conf
%config(noreplace) %{_sysconfdir}/%{name}/conf.d/health.d/*.conf
%config(noreplace) %{_sysconfdir}/%{name}/conf.d/python.d/*.conf
%config(noreplace) %{_sysconfdir}/%{name}/conf.d/statsd.d/*.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/netdata

%files data
%doc README.md
%license LICENSE REDISTRIBUTED.md
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/web
%attr(-, root, netdata) %{_datadir}/%{name}/web


%files freeipmi
%doc README.md
%license LICENSE REDISTRIBUTED.md
%caps(cap_setuid=ep) %attr(4750,root,netdata) %{_libexecdir}/%{name}/plugins.d/freeipmi.plugin

%changelog
* Fri Dec 11 2020  Ling Wang <LingWangNeuralEng@gmail.com> 1.26.0-3
- fix Bug 1906930: change /usr/share/netdata/web group to netdata

* Mon Nov 02 2020 Didier Fabert <didier.fabert@gmail.com> 1.26.0-2
- Fix wrong drop for el6 support
- Fix tmpfiles (from /var/run to /run)
- Minors changes in netdata.conf

* Sun Nov 01 2020 Didier Fabert <didier.fabert@gmail.com> 1.26.0-1
- Update from upstream

* Tue Sep 22 2020 Didier Fabert <didier.fabert@gmail.com> 1.25.0-1
- Update from upstream
- Drop el6 support

* Thu Aug 13 2020 Didier Fabert <didier.fabert@gmail.com> 1.24.0-1
- Update from upstream

* Tue Jul 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.23.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Fri Jul 17 2020 Didier Fabert <didier.fabert@gmail.com> 1.23.2-1
- Update from upstream

* Thu Jul 02 2020 Didier Fabert <didier.fabert@gmail.com> 1.23.1-1
- Update from upstream

* Sun May 17 2020 Didier Fabert <didier.fabert@gmail.com> 1.22.1-3
- Exclude arch s390x on el8

* Fri May 15 2020 Didier Fabert <didier.fabert@gmail.com> 1.22.1-2
- Conditionnaly build netfilteracct and cups plugins (disabed in epel7)

* Wed May 13 2020 Didier Fabert <didier.fabert@gmail.com> 1.22.1-1
- Update from upstream

* Sat Apr 18 2020 Juan Orti Alcaine <jortialc@redhat.com> 1.21.1-2
- Sync /usr/libexec/netdata/plugins.d/ binaries permissions with upstream

* Tue Apr 14 2020 Didier Fabert <didier.fabert@gmail.com> 1.21.1-1
- Update from upstream

* Tue Apr 07 2020 Didier Fabert <didier.fabert@gmail.com> 1.21.0-1
- Update from upstream

* Sun Mar 01 2020 Didier Fabert <didier.fabert@gmail.com> 1.20.0-1
- Update from upstream

* Wed Jan 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.18.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Sun Oct 20 2019 Didier Fabert <didier.fabert@gmail.com> 1.18.1-1
- Update from upstream

* Thu Oct 17 2019 Didier Fabert <didier.fabert@gmail.com> 1.18.0-1
- Update from upstream

* Fri Sep 13 2019 Didier Fabert <didier.fabert@gmail.com> 1.17.1-1
- Update from upstream

* Sat Sep 07 2019 Didier Fabert <didier.fabert@gmail.com> 1.17.0-1
- Update from upstream

* Thu Jul 25 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.16.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Mon Jul 08 2019 Didier Fabert <didier.fabert@gmail.com> 1.16.0-1
- Update from upstream

* Tue May 21 2019 Didier Fabert <didier.fabert@gmail.com> 1.15.0-1
- Update from upstream

* Fri Apr 19 2019 Didier Fabert <didier.fabert@gmail.com> 1.14.0-1
- Update from upstream

* Fri Apr 05 2019 Didier Fabert <didier.fabert@gmail.com> 1.14.0~rc0-2
- Remove condition for patch (SRPM must embedded all)

* Thu Apr 04 2019 Didier Fabert <didier.fabert@gmail.com> 1.14.0~rc0-1
- Update from upstream

* Fri Mar 22 2019 Didier Fabert <didier.fabert@gmail.com> 1.13.0-2
- Fix bash and sh path on el6

* Wed Mar 20 2019 Didier Fabert <didier.fabert@gmail.com> 1.13.0-1
- Update from upstream
- Bind to localhost

* Sun Mar 03 2019 Didier Fabert <didier.fabert@gmail.com> 1.12.2-3
- Fix upstream archive name (source0)

* Sat Mar 02 2019 Didier Fabert <didier.fabert@gmail.com> 1.12.2-2
- Fix spec file according to https://bugzilla.redhat.com/show_bug.cgi?id=1684719

* Fri Mar 01 2019 Didier Fabert <didier.fabert@gmail.com> 1.12.2-1
- Update from upstream

* Sat Feb 23 2019 Didier Fabert <didier.fabert@gmail.com> 1.12.1-3
- Fix rpmlint errors

* Sat Feb 23 2019 Didier Fabert <didier.fabert@gmail.com> 1.12.1-2
- /usr/share/netdata/web must be owned by netdata user for now

* Sat Feb 23 2019 Didier Fabert <didier.fabert@gmail.com> 1.12.1-1
- Update from upstream

* Tue Feb 19 2019 Didier Fabert <didier.fabert@gmail.com> 1.12.0-2
- Don't remove embedded font for el6 and el7, again

* Mon Feb 18 2019 Didier Fabert <didier.fabert@gmail.com> 1.12.0-1
- Update from upstream

* Tue Nov 20 2018 Didier Fabert <didier.fabert@gmail.com> 1.11.0-4
- Don't remove embedded font for el6 and el7, package is not exist

* Sun Nov 18 2018 Didier Fabert <didier.fabert@gmail.com> 1.11.0-3
- Disable tests for el6

* Sun Nov 18 2018 Didier Fabert <didier.fabert@gmail.com> 1.11.0-2
- Re-enable el6 and el7

* Sat Nov 17 2018 Didier Fabert <didier.fabert@gmail.com> 1.11.0-1
- Update from upstream

* Mon May 14 2018 Didier Fabert <didier.fabert@gmail.com> 1.10.0-2
- Remove embedded font files
- Add data (noarch) subpackage
- Remove deprecated instructions

* Wed Mar 28 2018 Didier Fabert <didier.fabert@gmail.com> 1.10.0-1
- Update from upstream

* Wed Dec 20 2017 Didier Fabert <didier.fabert@gmail.com> 1.9.0-1
- Update from upstream
- Move freeipmi plugin to sub package (avoid freeipmi dependency)

* Tue Sep 19 2017 Didier Fabert <didier.fabert@gmail.com> 1.8.0-1
- Update from upstream

* Thu Aug 31 2017 Didier Fabert <didier.fabert@gmail.com> 1.7.0-1
- Update from upstream

* Thu Mar 23 2017 Didier Fabert <didier.fabert@gmail.com> 1.6.0-3
- Fix freeipmi plugin permisions: must be suid to root

* Thu Mar 23 2017 Didier Fabert <didier.fabert@gmail.com> 1.6.0-2
- Enable freeipmi plugin

* Thu Mar 23 2017 Didier Fabert <didier.fabert@gmail.com> 1.6.0-1
- Update from upstream

* Mon Jan 23 2017 Didier Fabert <didier.fabert@gmail.com> 1.5.0-1
- Update from upstream

* Thu Dec 01 2016 Didier Fabert <didier.fabert@gmail.com> 1.4.0-1
- Update from upstream

* Wed Sep 07 2016 Didier Fabert <didier.fabert@gmail.com> 1.3.0-1
- Update from upstream

* Wed Jun 15 2016 Didier Fabert <didier.fabert@gmail.com> 1.2.0-2
- Create missing dir: /var/lib/netdata (useful for registry)

* Wed Jun 15 2016 Didier Fabert <didier.fabert@gmail.com> 1.2.0-1
- Update from upstream

* Fri Apr 01 2016 Didier Fabert <didier.fabert@gmail.com> 1.0.0-1
- First Release
