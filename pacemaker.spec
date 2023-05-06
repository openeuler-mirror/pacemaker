# Globals and defines to control package behavior (configure these as desired)

## User and group to use for nonprivileged services
%global uname hacluster
%global gname haclient

## Where to install Pacemaker documentation
%global pcmk_docdir %{_docdir}/%{name}

## GitHub entity that distributes source (for ease of using a fork)
%global github_owner ClusterLabs

## What to use as the OCF resource agent root directory
%global ocf_root %{_prefix}/lib/ocf

## Upstream pacemaker version, and its package version (specversion
## can be incremented to build packages reliably considered "newer"
## than previously built packages with the same pcmkversion)
%global pcmkversion 2.1.4
%global specversion 2

## Upstream commit (full commit ID, abbreviated commit ID, or tag) to build
%global commit dc6eb4362e67c1497a413434eba097063bf1ef83

## Since git v2.11, the extent of abbreviation is autoscaled by default
## (used to be constant of 7), so we need to convey it for non-tags, too.
%global commit_abbrev 9

# Define conditionals so that "rpmbuild --with <feature>" and
# "rpmbuild --without <feature>" can enable and disable specific features

## Add option to enable support for stonith/external fencing agents
%bcond_with stonithd

## Add option for whether to support storing sensitive information outside CIB
%bcond_with cibsecrets

## Add option to enable Native Language Support (experimental)
%bcond_with nls

## Add option to create binaries suitable for use with profiling tools
%bcond_with profiling

%bcond_without doc

## Add option to default to start-up synchronization with SBD.
##
## If enabled, SBD *MUST* be built to default similarly, otherwise data
## corruption could occur. Building both Pacemaker and SBD to default
## to synchronization improves safety, without requiring higher-level tools
## to be aware of the setting or requiring users to modify configurations
## after upgrading to versions that support synchronization.
%bcond_without sbd_sync

## Add option to prefix package version with "0."
## (so later "official" packages will be considered updates)
%bcond_without pre_release

## NOTE: skip --with upstart_job

## Add option to turn off hardening of libraries and daemon executables
%bcond_without hardening

## Add option to enable (or disable, on RHEL 8) links for legacy daemon names
%bcond_without legacy_links

## Nagios source control identifiers
%global nagios_name nagios-agents-metadata
%global nagios_hash 105ab8a7b2c16b9a29cf1c1596b80136eeef332b
%global nagios_archive_github_url %{nagios_hash}#/%{nagios_name}-%{nagios_hash}.tar.gz

# Define globals for convenient use later

## Workaround to use parentheses in other globals
%global lparen (
%global rparen )

## Whether this is a tagged release (final or release candidate)
%define tag_release %(c=%{commit}; case ${c} in Pacemaker-*%{rparen} echo 1 ;;
                      *%{rparen} echo 0 ;; esac)

## Portion of export/dist tarball name after "pacemaker-", and release version
%if 0%{tag_release}
%define archive_version %(c=%{commit}; echo ${c:10})
%define archive_github_url %{commit}#/%{name}-%{archive_version}.tar.gz
%else
%define archive_version %(c=%{commit}; echo ${c:0:%{commit_abbrev}})
%define archive_github_url %{archive_version}#/%{name}-%{archive_version}.tar.gz
%endif
### Always use a simple release number
%define pcmk_release %{specversion}

## Base GnuTLS cipher priorities (presumably only the initial, required keyword)
## overridable with "rpmbuild --define 'pcmk_gnutls_priorities PRIORITY-SPEC'"
%define gnutls_priorities %{?pcmk_gnutls_priorities}%{!?pcmk_gnutls_priorities:@SYSTEM}

## Different distros name certain packages differently
## (note: corosync libraries also differ, but all provide corosync-devel)
%global pkgname_libtool_devel libtool-ltdl-devel
%global pkgname_libtool_devel_arch libtool-ltdl-devel
%global pkgname_bzip2_devel bzip2-devel
%global pkgname_docbook_xsl docbook-style-xsl
%global pkgname_gettext gettext-devel
%global pkgname_gnutls_devel gnutls-devel
%global pkgname_shadow_utils shadow-utils
%global pkgname_procps procps-ng
%global pkgname_glue_libs cluster-glue-libs
%global pkgname_pcmk_libs %{name}-libs
%global hacluster_id 189

## Distro-specific configuration choices

### Use 2.0-style output when other distro packages don't support current output
%global compat20 --enable-compat-2.0

### Default concurrent-fencing to true when distro prefers that
%global concurrent_fencing --with-concurrent-fencing-default=true

### Default resource-stickiness to 1 when distro prefers that
%global resource_stickiness --with-resource-stickiness-default=1

# Python-related definitions

## Turn off auto-compilation of Python files outside Python specific paths,
## so there's no risk that unexpected "__python" macro gets picked to do the
## RPM-native byte-compiling there (only "{_datadir}/pacemaker/tests" affected)
## -- distro-dependent tricks or automake's fallback to be applied there
%if %{defined _python_bytecompile_extra}
%global _python_bytecompile_extra 0
%else
### the statement effectively means no RPM-native byte-compiling will occur at
### all, so distro-dependent tricks for Python-specific packages to be applied
%global __os_install_post %(echo '%{__os_install_post}' | {
                            sed -e 's!/usr/lib[^[:space:]]*/brp-python-bytecompile[[:space:]].*$!!g'; })
%endif

## Prefer Python 3 definitions explicitly, in case 2 is also available
%global python_name python3
%global python_path %{__python3}
%define python_site %{?python3_sitelib}%{!?python3_sitelib:%(
  %{python_path} -c 'from distutils.sysconfig import get_python_lib as gpl; print(gpl(1))' 2>/dev/null)}

# Keep sane profiling data if requested
%if %{with profiling}

## Disable -debuginfo package and stripping binaries/libraries
%define debug_package %{nil}

%endif



Name:          pacemaker
Summary:       Scalable High-Availability cluster resource manager
Version:       %{pcmkversion}
Release:       %{pcmk_release}
License:       GPLv2+ and LGPLv2+
Url:           https://www.clusterlabs.org

# You can use "spectool -s 0 pacemaker.spec" (rpmdevtools) to show final URL.
Source0:       https://codeload.github.com/%{github_owner}/%{name}/tar.gz/%{archive_github_url}
Source1:       https://codeload.github.com/%{github_owner}/%{nagios_name}/tar.gz/%{nagios_archive_github_url}

# upstream commits
Patch0:        0001-Fix-tools-Don-t-output-null-in-crm_attribute-s-quiet.patch

Requires:      resource-agents
Requires:      %{pkgname_pcmk_libs} = %{version}-%{release}
Requires:      %{name}-cluster-libs = %{version}-%{release}
Requires:      %{name}-cli = %{version}-%{release}
%{?systemd_requires}

Requires:      %{python_path}
BuildRequires: %{python_name}-devel

# Pacemaker requires a minimum libqb functionality
Requires:      libqb >= 0.17.0
BuildRequires: libqb-devel >= 0.17.0

# Required basic build tools
BuildRequires: autoconf
BuildRequires: automake
BuildRequires: coreutils
BuildRequires: findutils
BuildRequires: gcc
BuildRequires: grep
BuildRequires: libtool
%if %{defined pkgname_libtool_devel}
BuildRequires: %{?pkgname_libtool_devel}
%endif
BuildRequires: make
BuildRequires: pkgconfig
BuildRequires: sed

# Required for core functionality
BuildRequires: pkgconfig(glib-2.0) >= 2.42
BuildRequires: libxml2-devel
BuildRequires: libxslt-devel
BuildRequires: libuuid-devel
BuildRequires: %{pkgname_bzip2_devel}

# Enables optional functionality
BuildRequires: pkgconfig(dbus-1)
BuildRequires: %{pkgname_docbook_xsl}
BuildRequires: %{pkgname_gnutls_devel}
BuildRequires: help2man
BuildRequires: ncurses-devel
BuildRequires: pam-devel
BuildRequires: %{pkgname_gettext} >= 0.18

# Required for "make check"
BuildRequires: libcmocka-devel

BuildRequires: pkgconfig(systemd)

# RH patches are created by git, so we need git to apply them
BuildRequires: git

Requires:      corosync >= 2.0.0
BuildRequires: corosync-devel >= 2.0.0

%if %{with stonithd}
BuildRequires: %{pkgname_glue_libs}-devel
%endif

Provides:      pcmk-cluster-manager = %{version}-%{release}
Provides:      pcmk-cluster-manager = %{version}-%{release}

# Bundled bits
## Pacemaker uses the crypto/md5-buffer module from gnulib
Provides:      bundled(gnulib) = 20200404

%description
Pacemaker is an advanced, scalable High-Availability cluster resource
manager.

It supports more than 16 node clusters with significant capabilities
for managing resources and dependencies.

It will run scripts at initialization, when machines go up or down,
when related resources fail and can be configured to periodically check
resource health.

Available rpmbuild rebuild options:
  --with(out) : cibsecrets coverage doc hardening pre_release profiling

%package cli
License:       GPLv2+ and LGPLv2+
Summary:       Command line tools for controlling Pacemaker clusters
Requires:      %{pkgname_pcmk_libs} = %{version}-%{release}
Recommends:    pcmk-cluster-manager = %{version}-%{release}
# For crm_report
Recommends:    tar
Recommends:    bzip2
Requires:      perl-TimeDate
Requires:      %{pkgname_procps}
Requires:      psmisc
Requires(post):coreutils

%description cli
Pacemaker is an advanced, scalable High-Availability cluster resource
manager.

The %{name}-cli package contains command line tools that can be used
to query and control the cluster from machines that may, or may not,
be part of the cluster.

%package -n %{pkgname_pcmk_libs}
License:       GPLv2+ and LGPLv2+
Summary:       Core Pacemaker libraries
Requires(pre): %{pkgname_shadow_utils}
Requires:      %{name}-schemas = %{version}-%{release}
# sbd 1.4.0+ supports the libpe_status API for pe_working_set_t
# sbd 1.4.2+ supports startup/shutdown handshake via pacemakerd-api
#            and handshake defaults to enabled for rhel builds
# sbd 1.5.0+ handshake defaults to enabled with upstream sbd-release
#            implicitly supports handshake defaults to enabled in this spec
Conflicts:     sbd < 1.5.0

%description -n %{pkgname_pcmk_libs}
Pacemaker is an advanced, scalable High-Availability cluster resource
manager.

The %{pkgname_pcmk_libs} package contains shared libraries needed for cluster
nodes and those just running the CLI tools.

%package cluster-libs
License:       GPLv2+ and LGPLv2+
Summary:       Cluster Libraries used by Pacemaker
Requires:      %{pkgname_pcmk_libs} = %{version}-%{release}

%description cluster-libs
Pacemaker is an advanced, scalable High-Availability cluster resource
manager.

The %{name}-cluster-libs package contains cluster-aware shared
libraries needed for nodes that will form part of the cluster nodes.

%package remote
License:       GPLv2+ and LGPLv2+
Summary:       Pacemaker remote executor daemon for non-cluster nodes
Requires:      %{pkgname_pcmk_libs} = %{version}-%{release}
Requires:      %{name}-cli = %{version}-%{release}
Requires:      resource-agents
# -remote can be fully independent of systemd
%{?systemd_ordering}%{!?systemd_ordering:%{?systemd_requires}}
Provides:      pcmk-cluster-manager = %{version}-%{release}
Provides:      pcmk-cluster-manager = %{version}-%{release}

%description remote
Pacemaker is an advanced, scalable High-Availability cluster resource
manager.

The %{name}-remote package contains the Pacemaker Remote daemon
which is capable of extending pacemaker functionality to remote
nodes not running the full corosync/cluster stack.

%package -n %{pkgname_pcmk_libs}-devel
License:       GPLv2+ and LGPLv2+
Summary:       Pacemaker development package
Requires:      %{pkgname_pcmk_libs} = %{version}-%{release}
Requires:      %{name}-cluster-libs = %{version}-%{release}
Requires:      %{pkgname_bzip2_devel}
Requires:      corosync-devel >= 2.0.0
Requires:      glib2-devel
Requires:      libqb-devel
%if %{defined pkgname_libtool_devel_arch}
Requires:      %{?pkgname_libtool_devel_arch}
%endif
Requires:      libuuid-devel
Requires:      libxml2-devel
Requires:      libxslt-devel

%description -n %{pkgname_pcmk_libs}-devel
Pacemaker is an advanced, scalable High-Availability cluster resource
manager.

The %{pkgname_pcmk_libs}-devel package contains headers and shared libraries
for developing tools for Pacemaker.

%package       cts
License:       GPLv2+ and LGPLv2+
Summary:       Test framework for cluster-related technologies like Pacemaker
Requires:      %{python_path}
Requires:      %{pkgname_pcmk_libs} = %{version}-%{release}
Requires:      %{name}-cli = %{version}-%{release}
Requires:      %{pkgname_procps}
Requires:      psmisc
BuildArch:     noarch

# systemd Python bindings are a separate package in some distros
Requires:      %{python_name}-systemd

%description   cts
Test framework for cluster-related technologies like Pacemaker

%package       doc
License:       CC-BY-SA-4.0
Summary:       Documentation for Pacemaker
BuildArch:     noarch
Conflicts:     %{name}-libs > %{version}-%{release}
Conflicts:     %{name}-libs < %{version}-%{release}

%description   doc
Documentation for Pacemaker.

Pacemaker is an advanced, scalable High-Availability cluster resource
manager.

%package       schemas
License:       GPLv2+
Summary:       Schemas and upgrade stylesheets for Pacemaker
BuildArch:     noarch

%description   schemas
Schemas and upgrade stylesheets for Pacemaker

Pacemaker is an advanced, scalable High-Availability cluster resource
manager.

%package       nagios-plugins-metadata
License:       GPLv3
Summary:       Pacemaker Nagios Metadata
BuildArch:     noarch
# NOTE below are the plugins this metadata uses.
# Requires:      nagios-plugins-http
# Requires:      nagios-plugins-ldap
# Requires:      nagios-plugins-mysql
# Requires:      nagios-plugins-pgsql
# Requires:      nagios-plugins-tcp
Requires:      pcmk-cluster-manager

%description  nagios-plugins-metadata
The metadata files required for Pacemaker to execute the nagios plugin
monitor resources.

%prep
%autosetup -a 1 -n %{name}-%{archive_version} -S git_am -p 1
# in f33 s390x complains but shouldn't hurt globally
# as configure.ac is checking for support
sed -i configure.ac -e "s/-Wall/-Wall -Wno-format-truncation/"

%build

%if "%toolchain" == "clang"
	export CFLAGS="$CFLAGS -Wno-error=strict-prototypes -Wno-error=unused-but-set-variable"
	export CXXFLAGS="$CXXFLAGS -wno-error=strict-prototypes -Wno-error=unused-but-set-variable"
%endif
export systemdsystemunitdir=%{?_unitdir}%{!?_unitdir:no}

%if %{with hardening}
# prefer distro-provided hardening flags in case they are defined
# through _hardening_{c,ld}flags macros, configure script will
# use its own defaults otherwise; if such hardenings are completely
# undesired, rpmbuild using "--without hardening"
# (or "--define '_without_hardening 1'")
export CFLAGS_HARDENED_EXE="%{?_hardening_cflags}"
export CFLAGS_HARDENED_LIB="%{?_hardening_cflags}"
export LDFLAGS_HARDENED_EXE="%{?_hardening_ldflags}"
export LDFLAGS_HARDENED_LIB="%{?_hardening_ldflags}"
%endif

./autogen.sh

%{configure}                                                                    \
        PYTHON=%{python_path}                                                   \
        %{!?with_hardening:    --disable-hardening}                             \
        %{?with_legacy_links:  --enable-legacy-links}                           \
        %{?with_profiling:     --with-profiling}                                \
        %{?with_cibsecrets:    --with-cibsecrets}                               \
        %{?with_nls:           --enable-nls}                                    \
        %{?with_sbd_sync:      --with-sbd-sync-default="true"}                  \
        %{?gnutls_priorities:  --with-gnutls-priorities="%{gnutls_priorities}"} \
        %{?bug_url:            --with-bug-url=%{bug_url}}                       \
        %{?ocf_root:           --with-ocfdir=%{ocf_root}}                       \
        %{?concurrent_fencing}                                                  \
        %{?resource_stickiness}                                                 \
        %{?compat20}                                                            \
        --disable-static                                                        \
        --with-initdir=%{_initrddir}                                            \
        --with-runstatedir=%{_rundir}                                           \
        --localstatedir=%{_var}                                                 \
        --with-nagios                                                             \
        --with-nagios-metadata-dir=%{_datadir}/pacemaker/nagios/plugins-metadata/ \
        --with-nagios-plugin-dir=%{_libdir}/nagios/plugins/                       \
        --with-version=%{version}-%{release}

make %{_smp_mflags} V=1

%check
make %{_smp_mflags} check
{ cts/cts-scheduler --run load-stopped-loop \
  && cts/cts-cli \
  && touch .CHECKED
} 2>&1 | sed 's/[fF]ail/faiil/g'  # prevent false positives in rpmlint
[ -f .CHECKED ] && rm -f -- .CHECKED

%install
# skip automake-native Python byte-compilation, since RPM-native one (possibly
# distro-confined to Python-specific directories, which is currently the only
# relevant place, anyway) assures proper intrinsic alignment with wider system
# (such as with py_byte_compile macro, which is concurrent Fedora/EL specific)
make install \
  DESTDIR=%{buildroot} V=1 docdir=%{pcmk_docdir} \
  %{?_python_bytecompile_extra:%{?py_byte_compile:am__py_compile=true}}

mkdir -p %{buildroot}%{_datadir}/pacemaker/nagios/plugins-metadata
for file in $(find %{nagios_name}-%{nagios_hash}/metadata -type f); do
    install -m 644 $file %{buildroot}%{_datadir}/pacemaker/nagios/plugins-metadata
done


mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/lib/rpm-state/%{name}

# Don't package libtool archives
find %{buildroot} -name '*.la' -type f -print0 | xargs -0 rm -f

# Do not package these either
rm -f %{buildroot}/%{_sbindir}/fence_legacy
rm -f %{buildroot}/%{_mandir}/man8/fence_legacy.*

# For now, don't package the servicelog-related binaries built only for
# ppc64le when certain dependencies are installed. If they get more exercise by
# advanced users, we can reconsider.
rm -f %{buildroot}/%{_sbindir}/notifyServicelogEvent
rm -f %{buildroot}/%{_sbindir}/ipmiservicelogd

# Byte-compile Python sources where suitable and the distro procedures known
%if %{defined py_byte_compile}
%{py_byte_compile %{python_path} %{buildroot}%{_datadir}/pacemaker/tests}
%if !%{defined _python_bytecompile_extra}
%{py_byte_compile %{python_path} %{buildroot}%{python_site}/cts}
%endif
%endif

%post
%systemd_post pacemaker.service

%preun
%systemd_preun pacemaker.service

%postun
%systemd_postun_with_restart pacemaker.service

%pre remote
# Stop the service before anything is touched, and remember to restart
# it as one of the last actions (compared to using systemd_postun_with_restart,
# this avoids suicide when sbd is in use)
systemctl --quiet is-active pacemaker_remote
if [ $? -eq 0 ] ; then
    mkdir -p %{_localstatedir}/lib/rpm-state/%{name}
    touch %{_localstatedir}/lib/rpm-state/%{name}/restart_pacemaker_remote
    systemctl stop pacemaker_remote >/dev/null 2>&1
else
    rm -f %{_localstatedir}/lib/rpm-state/%{name}/restart_pacemaker_remote
fi

%post remote
%systemd_post pacemaker_remote.service

%preun remote
%systemd_preun pacemaker_remote.service

%postun remote
# This next line is a no-op, because we stopped the service earlier, but
# we leave it here because it allows us to revert to the standard behavior
# in the future if desired
%systemd_postun_with_restart pacemaker_remote.service
# Explicitly take care of removing the flag-file(s) upon final removal
if [ "$1" -eq 0 ] ; then
    rm -f %{_localstatedir}/lib/rpm-state/%{name}/restart_pacemaker_remote
fi

%posttrans remote
if [ -e %{_localstatedir}/lib/rpm-state/%{name}/restart_pacemaker_remote ] ; then
    systemctl start pacemaker_remote >/dev/null 2>&1
    rm -f %{_localstatedir}/lib/rpm-state/%{name}/restart_pacemaker_remote
fi

%post cli
%systemd_post crm_mon.service
if [ "$1" -eq 2 ]; then
    # Package upgrade, not initial install:
    # Move any pre-2.0 logs to new location to ensure they get rotated
    { mv -fbS.rpmsave %{_var}/log/pacemaker.log* %{_var}/log/pacemaker \
      || mv -f %{_var}/log/pacemaker.log* %{_var}/log/pacemaker
    } >/dev/null 2>/dev/null || :
fi

%preun cli
%systemd_preun crm_mon.service

%postun cli
%systemd_postun_with_restart crm_mon.service

%pre -n %{pkgname_pcmk_libs}
# @TODO Use sysusers.d:
# https://fedoraproject.org/wiki/Changes/Adopting_sysusers.d_format
getent group %{gname} >/dev/null || groupadd -r %{gname} -g %{hacluster_id}
getent passwd %{uname} >/dev/null || useradd -r -g %{gname} -u %{hacluster_id} -s /sbin/nologin -c "cluster user" %{uname}
exit 0

%ldconfig_scriptlets -n %{pkgname_pcmk_libs}
%ldconfig_scriptlets cluster-libs

%files
###########################################################
%config(noreplace) %{_sysconfdir}/sysconfig/pacemaker
%{_sbindir}/pacemakerd

%{_unitdir}/pacemaker.service

%exclude %{_datadir}/pacemaker/nagios/plugins-metadata/*

%exclude %{_libexecdir}/pacemaker/cts-log-watcher
%exclude %{_libexecdir}/pacemaker/cts-support
%exclude %{_sbindir}/pacemaker-remoted
%exclude %{_sbindir}/pacemaker_remoted
%{_libexecdir}/pacemaker/*

%{_sbindir}/crm_master
%{_sbindir}/fence_watchdog

%doc %{_mandir}/man7/pacemaker-controld.*
%doc %{_mandir}/man7/pacemaker-schedulerd.*
%doc %{_mandir}/man7/pacemaker-fenced.*
%doc %{_mandir}/man7/ocf_pacemaker_controld.*
%doc %{_mandir}/man7/ocf_pacemaker_remote.*
%doc %{_mandir}/man8/crm_master.*
%doc %{_mandir}/man8/fence_watchdog.*
%doc %{_mandir}/man8/pacemakerd.*

%doc %{_datadir}/pacemaker/alerts

%license licenses/GPLv2
%doc COPYING
%doc ChangeLog

%dir %attr (750, %{uname}, %{gname}) %{_var}/lib/pacemaker/cib
%dir %attr (750, %{uname}, %{gname}) %{_var}/lib/pacemaker/pengine
%{ocf_root}/resource.d/pacemaker/controld
%{ocf_root}/resource.d/pacemaker/remote

%files cli
%dir %attr (750, root, %{gname}) %{_sysconfdir}/pacemaker
%config(noreplace) %{_sysconfdir}/logrotate.d/pacemaker
%config(noreplace) %{_sysconfdir}/sysconfig/crm_mon

%{_unitdir}/crm_mon.service

%{_sbindir}/attrd_updater
%{_sbindir}/cibadmin
%if %{with cibsecrets}
%{_sbindir}/cibsecret
%endif
%{_sbindir}/crm_attribute
%{_sbindir}/crm_diff
%{_sbindir}/crm_error
%{_sbindir}/crm_failcount
%{_sbindir}/crm_mon
%{_sbindir}/crm_node
%{_sbindir}/crm_resource
%{_sbindir}/crm_rule
%{_sbindir}/crm_standby
%{_sbindir}/crm_verify
%{_sbindir}/crmadmin
%{_sbindir}/iso8601
%{_sbindir}/crm_shadow
%{_sbindir}/crm_simulate
%{_sbindir}/crm_report
%{_sbindir}/crm_ticket
%{_sbindir}/stonith_admin
# "dirname" is owned by -schemas, which is a prerequisite
%{_datadir}/pacemaker/report.collector
%{_datadir}/pacemaker/report.common
# XXX "dirname" is not owned by any prerequisite
%{_datadir}/snmp/mibs/PCMK-MIB.txt

%exclude %{ocf_root}/resource.d/pacemaker/controld
%exclude %{ocf_root}/resource.d/pacemaker/o2cb
%exclude %{ocf_root}/resource.d/pacemaker/remote

%dir %{ocf_root}
%dir %{ocf_root}/resource.d
%{ocf_root}/resource.d/pacemaker

%doc %{_mandir}/man7/*
%exclude %{_mandir}/man7/pacemaker-controld.*
%exclude %{_mandir}/man7/pacemaker-schedulerd.*
%exclude %{_mandir}/man7/pacemaker-fenced.*
%exclude %{_mandir}/man7/ocf_pacemaker_controld.*
%exclude %{_mandir}/man7/ocf_pacemaker_o2cb.*
%exclude %{_mandir}/man7/ocf_pacemaker_remote.*
%doc %{_mandir}/man8/*
%exclude %{_mandir}/man8/crm_master.*
%exclude %{_mandir}/man8/fence_watchdog.*
%exclude %{_mandir}/man8/pacemakerd.*
%exclude %{_mandir}/man8/pacemaker-remoted.*

%license licenses/GPLv2
%doc COPYING
%doc ChangeLog

%dir %attr (750, %{uname}, %{gname}) %{_var}/lib/pacemaker
%dir %attr (750, %{uname}, %{gname}) %{_var}/lib/pacemaker/blackbox
%dir %attr (750, %{uname}, %{gname}) %{_var}/lib/pacemaker/cores
%dir %attr (770, %{uname}, %{gname}) %{_var}/log/pacemaker
%dir %attr (770, %{uname}, %{gname}) %{_var}/log/pacemaker/bundles

%files -n %{pkgname_pcmk_libs} %{?with_nls:-f %{name}.lang}
%{_libdir}/libcib.so.*
%{_libdir}/liblrmd.so.*
%{_libdir}/libcrmservice.so.*
%{_libdir}/libcrmcommon.so.*
%{_libdir}/libpe_status.so.*
%{_libdir}/libpe_rules.so.*
%{_libdir}/libpacemaker.so.*
%{_libdir}/libstonithd.so.*
%license licenses/LGPLv2.1
%doc COPYING
%doc ChangeLog

%files cluster-libs
%{_libdir}/libcrmcluster.so.*
%license licenses/LGPLv2.1
%doc COPYING
%doc ChangeLog

%files remote
%config(noreplace) %{_sysconfdir}/sysconfig/pacemaker
# state directory is shared between the subpackets
# let rpm take care of removing it once it isn't
# referenced anymore and empty
%ghost %dir %{_localstatedir}/lib/rpm-state/%{name}
%{_unitdir}/pacemaker_remote.service

%{_sbindir}/pacemaker-remoted
%{_sbindir}/pacemaker_remoted
%{_mandir}/man8/pacemaker-remoted.*
%license licenses/GPLv2
%doc COPYING
%doc ChangeLog

%files doc
%doc %{pcmk_docdir}
%license licenses/CC-BY-SA-4.0

%files cts
%{python_site}/cts
%{_datadir}/pacemaker/tests

%{_libexecdir}/pacemaker/cts-log-watcher
%{_libexecdir}/pacemaker/cts-support

%license licenses/GPLv2
%doc COPYING
%doc ChangeLog

%files -n %{pkgname_pcmk_libs}-devel
%{_includedir}/pacemaker
%{_libdir}/*.so
%{_libdir}/pkgconfig/*.pc
%license licenses/LGPLv2.1
%doc COPYING
%doc ChangeLog

%files schemas
%license licenses/GPLv2
%dir %{_datadir}/pacemaker
%{_datadir}/pacemaker/*.rng
%{_datadir}/pacemaker/*.xsl
%{_datadir}/pacemaker/api
%{_datadir}/pacemaker/base
%{_datadir}/pkgconfig/pacemaker-schemas.pc

%files nagios-plugins-metadata
%dir %{_datadir}/pacemaker/nagios
%dir %{_datadir}/pacemaker/nagios/plugins-metadata
%attr(0644,root,root) %{_datadir}/pacemaker/nagios/plugins-metadata/*
%license %{nagios_name}-%{nagios_hash}/COPYING

%changelog
* Sat May 06 2023 yoo <sunyuechi@iscas.ac.cn> - 2.1.4-2
- fix clang build error

* Mon Feb 06 2023 jiangxinyu <jiangxinyu@kylinos.cn> - 2.1.4-1
- Update package to version 2.1.4

* Tue Jul 26 2022 Bixiaoyan <bixiaoyan@kylinos.cn> - 2.1.2-1
- upgrade to 2.1.2

* Wed Feb 16 2022 jiangxinyu <jiangxinyu@kylinos.cn> - 2.0.5-1
- upgrade to 2.0.5

* Sat Aug 07 2021 wangyue <wangyue92@huawei.com> - 2.0.3-3
- fix build error with gcc 10

* Tue Mar 23 2021 jiangxinyu <jiangxinyu@kylinos.cn> - 2.0.3-2
- Add 'Resolve-the-failure-of-time-matching-in-test-cases.patch' file 2.0.3-2

* Thu Nov 05 2020 jiangxinyu <jiangxinyu@kylinos.cn> - 2.0.3-1
- Upgrade the pacemaker package version to 2.0.3-1

* Wed Apr 15 2020 houjian<houjian@kylinos.cn> - 2.0.2-3.2
- Init pacemaker project
