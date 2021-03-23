# Globals and defines to control package behavior (configure these as desired)

## User and group to use for nonprivileged services
%global uname hacluster
%global gname haclient

## Where to install Pacemaker documentation
%global pcmk_docdir %{_docdir}/%{name}

## GitHub entity that distributes source (for ease of using a fork)
%global github_owner ClusterLabs

## Upstream pacemaker version, and its package version (specversion
## can be incremented to build packages reliably considered "newer"
## than previously built packages with the same pcmkversion)
%global pcmkversion 2.0.3
%global specversion 2

## Upstream commit (or git tag, such as "Pacemaker-" plus the
## {pcmkversion} macro for an official release) to use for this package
%global commit Pacemaker-2.0.3
## Since git v2.11, the extent of abbreviation is autoscaled by default
## (used to be constant of 7), so we need to convey it for non-tags, too.
%global commit_abbrev 9

## Nagios source control identifiers
%global nagios_name nagios-agents-metadata
%global nagios_hash 105ab8a7b2c16b9a29cf1c1596b80136eeef332b


# Define globals for convenient use later

## Workaround to use parentheses in other globals
%global lparen (
%global rparen )

## Short version of git commit
%define shortcommit %(c=%{commit}; case ${c} in
                      Pacemaker-*%{rparen} echo ${c:10};;
                      *%{rparen} echo ${c:0:%{commit_abbrev}};; esac)

## Whether this is a tagged release
%define tag_release %([ %{commit} != Pacemaker-%{shortcommit} ]; echo $?)

## Whether this is a release candidate (in case of a tagged release)
%define pre_release %([ "%{tag_release}" -eq 0 ] || {
                      case "%{shortcommit}" in *-rc[[:digit:]]*%{rparen} false;;
                      esac; }; echo $?)

## Heuristic used to infer bleeding-edge deployments that are
## less likely to have working versions of the documentation tools
%define bleeding %(test ! -e /etc/yum.repos.d/fedora-rawhide.repo; echo $?)

## Base GnuTLS cipher priorities (presumably only the initial, required keyword)
## overridable with "rpmbuild --define 'pcmk_gnutls_priorities PRIORITY-SPEC'"
%define gnutls_priorities %{?pcmk_gnutls_priorities}%{!?pcmk_gnutls_priorities:@SYSTEM}

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

## Values that differ by Python major version
%global python_path /usr/bin/python%{?python3_pkgversion}%{!?python3_pkgversion:3}
%global python_pkg python3
%global python_min 3.2
%define py_site %{?python3_sitelib}%{!?python3_sitelib:%(
  python3 -c 'from distutils.sysconfig import get_python_lib as gpl; print(gpl(1))' 2>/dev/null)}


# Define conditionals so that "rpmbuild --with <feature>" and
# "rpmbuild --without <feature>" can enable and disable specific features

## NOTE: skip --with stonith

## Add option to create binaries suitable for use with profiling tools
%bcond_with profiling

## Add option to create binaries with coverage analysis
%bcond_with coverage

## Add option to skip generating documentation
## (the build tools aren't available everywhere)
%bcond_without doc

## Add option to prefix package version with "0."
## (so later "official" packages will be considered updates)
%bcond_with pre_release

## NOTE: skip --with upstart_job

## Add option to turn off hardening of libraries and daemon executables
%bcond_without hardening

## Add option to disable links for legacy daemon names
%bcond_without legacy_links


# Keep sane profiling data if requested
%if %{with profiling}

## Disable -debuginfo package and stripping binaries/libraries
%define debug_package %{nil}

%endif


%define pcmk_release %{specversion}


Name:          pacemaker
Summary:       Scalable High-Availability cluster resource manager
Version:       %{pcmkversion}
Release:       %{pcmk_release}
License:       GPLv2+ and LGPLv2+
Url:           http://www.clusterlabs.org

# Hint: use "spectool -s 0 pacemaker.spec" (rpmdevtools) to check the final URL
Source0:       https://github.com/%{github_owner}/%{name}/archive/%{commit}/%{name}-%{shortcommit}.tar.gz
Source1:       https://github.com/%{github_owner}/%{nagios_name}/archive/%{nagios_hash}/%{nagios_name}-%{nagios_hash}.tar.gz
# ---
Patch0:        Build-fix-unability-to-build-with-Inkscape-1.0-beta-.patch
Patch1:        Resolve-the-failure-of-time-matching-in-test-cases.patch

Requires:      resource-agents
Requires:      %{name}-libs%{?_isa} = %{version}-%{release}
Requires:      %{name}-cluster-libs%{?_isa} = %{version}-%{release}
Requires:      %{name}-cli = %{version}-%{release}
%{?systemd_requires}

# Pacemaker requires a minimum Python functionality
Requires:      %{python_pkg} >= %{python_min}
BuildRequires: %{python_pkg}-devel >= %{python_min}

# Pacemaker requires a minimum libqb functionality
Requires:      libqb >= 0.13.0
BuildRequires: libqb-devel >= 0.13.0

# Basics required for the build (even if usually satisfied through other BRs)
BuildRequires: coreutils findutils grep sed

# Required for core functionality
BuildRequires: automake autoconf gcc libtool pkgconfig libtool-ltdl-devel
BuildRequires: pkgconfig(glib-2.0) >= 2.16
BuildRequires: libxml2-devel libxslt-devel libuuid-devel
BuildRequires: bzip2-devel

# Enables optional functionality
BuildRequires: ncurses-devel docbook-style-xsl
BuildRequires: help2man gnutls-devel pam-devel pkgconfig(dbus-1)

BuildRequires: pkgconfig(systemd)

Requires:      corosync >= 2.0.0
BuildRequires: corosynclib-devel >= 2.0.0
#XXX
#BuildRequires: pkgconfig(libcpg)
#BuildRequires: pkgconfig(libcfg)

## (note no avoiding effect when building through non-customized mock)
#%%if !%%{bleeding}
#%%if %%{with doc}
#BuildRequires: asciidoc inkscape publican
#%%endif
#%%endif

# git-style patch application
BuildRequires: git

Provides:      pcmk-cluster-manager = %{version}-%{release}
Provides:      pcmk-cluster-manager%{?_isa} = %{version}-%{release}

# Pacemaker uses the crypto/md5 module from gnulib
Provides:      bundled(gnulib)

%description
Pacemaker is an advanced, scalable High-Availability cluster resource
manager.

It supports more than 16 node clusters with significant capabilities
for managing resources and dependencies.

It will run scripts at initialization, when machines go up or down,
when related resources fail and can be configured to periodically check
resource health.

Available rpmbuild rebuild options:
  --with(out) : coverage doc hardening pre_release profiling

%package cli
License:       GPLv2+ and LGPLv2+
Summary:       Command line tools for controlling Pacemaker clusters
Requires:      %{name}-libs%{?_isa} = %{version}-%{release}
%if 0%{?fedora} > 22 || 0%{?rhel} > 7
Recommends:    pcmk-cluster-manager = %{version}-%{release}
%endif
Requires:      perl-TimeDate
Requires:      procps-ng
Requires:      psmisc
Requires(post):coreutils

%description cli
Pacemaker is an advanced, scalable High-Availability cluster resource
manager.

The %{name}-cli package contains command line tools that can be used
to query and control the cluster from machines that may, or may not,
be part of the cluster.

%package libs
License:       GPLv2+ and LGPLv2+
Summary:       Core Pacemaker libraries
Requires(pre): shadow-utils
Requires:      %{name}-schemas = %{version}-%{release}
# sbd 1.4.0+ supports the libpe_status API for pe_working_set_t
Conflicts:     sbd < 1.4.0

%description libs
Pacemaker is an advanced, scalable High-Availability cluster resource
manager.

The %{name}-libs package contains shared libraries needed for cluster
nodes and those just running the CLI tools.

%package cluster-libs
License:       GPLv2+ and LGPLv2+
Summary:       Cluster Libraries used by Pacemaker
Requires:      %{name}-libs%{?_isa} = %{version}-%{release}

%description cluster-libs
Pacemaker is an advanced, scalable High-Availability cluster resource
manager.

The %{name}-cluster-libs package contains cluster-aware shared
libraries needed for nodes that will form part of the cluster nodes.

%package remote
License:       GPLv2+ and LGPLv2+
Summary:       Pacemaker remote daemon for non-cluster nodes
Requires:      %{name}-libs%{?_isa} = %{version}-%{release}
Requires:      %{name}-cli = %{version}-%{release}
Requires:      resource-agents
# -remote can be fully independent of systemd
%{?systemd_ordering}%{!?systemd_ordering:%{?systemd_requires}}
Provides:      pcmk-cluster-manager = %{version}-%{release}
Provides:      pcmk-cluster-manager%{?_isa} = %{version}-%{release}

%description remote
Pacemaker is an advanced, scalable High-Availability cluster resource
manager.

The %{name}-remote package contains the Pacemaker Remote daemon
which is capable of extending pacemaker functionality to remote
nodes not running the full corosync/cluster stack.

%package libs-devel
License:       GPLv2+ and LGPLv2+
Summary:       Pacemaker development package
Requires:      %{name}-libs%{?_isa} = %{version}-%{release}
Requires:      %{name}-cluster-libs%{?_isa} = %{version}-%{release}
Requires:      libtool-ltdl-devel libuuid-devel
Requires:      libxml2-devel%{?_isa} libxslt-devel%{?_isa}
Requires:      bzip2-devel%{?_isa} glib2-devel%{?_isa}
Requires:      libqb-devel%{?_isa}
Requires:      corosynclib-devel%{?_isa} >= 2.0.0

%description libs-devel
Pacemaker is an advanced, scalable High-Availability cluster resource
manager.

The %{name}-libs-devel package contains headers and shared libraries
for developing tools for Pacemaker.

%package       cts
License:       GPLv2+ and LGPLv2+
Summary:       Test framework for cluster-related technologies like Pacemaker
Requires:      %{python_pkg} >= %{python_min}
Requires:      %{name}-libs = %{version}-%{release}
Requires:      procps-ng
Requires:      psmisc
BuildArch:     noarch

Requires:      %{python_pkg}-systemd

%description   cts
Test framework for cluster-related technologies like Pacemaker

%package       doc
License:       CC-BY-SA
Summary:       Documentation for Pacemaker
BuildArch:     noarch

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
Requires:      nagios-plugins-http
Requires:      nagios-plugins-ldap
Requires:      nagios-plugins-mysql
Requires:      nagios-plugins-pgsql
Requires:      nagios-plugins-tcp
Requires:      pcmk-cluster-manager

%description  nagios-plugins-metadata
The metadata files required for Pacemaker to execute the nagios plugin
monitor resources.

%prep
%setup -q -a 1 -n %{name}-%{commit}
%global __scm git_am
%__scm_setup_git
%patch0 -p1
%patch1 -p1

%build

# Early versions of autotools (e.g. RHEL <= 5) do not support --docdir
export docdir=%{pcmk_docdir}

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

# Rawhide glibc doesn't like ftime at all
export CPPFLAGS="-UPCMK_TIME_EMERGENCY_CGT $CPPFLAGS"

%{configure}                                                                    \
        PYTHON=%{python_path}                                                   \
        %{!?with_hardening:    --disable-hardening}                             \
        %{!?with_legacy_links: --disable-legacy-links}                          \
        %{?with_profiling:     --with-profiling}                                \
        %{?with_coverage:      --with-coverage}                                 \
        %{!?with_doc:          --with-brand=}                                   \
        %{?gnutls_priorities:  --with-gnutls-priorities="%{gnutls_priorities}"} \
        --with-initdir=%{_initrddir}                                            \
        --with-runstatedir=%{_rundir}                                           \
        --localstatedir=%{_var}                                                 \
        --with-version=%{version}-%{release}                                    \
        --with-bug-url=https://bugz.fedoraproject.org/%{name}                   \
        --with-nagios                                                           \
        --with-nagios-metadata-dir=%{_datadir}/pacemaker/nagios/plugins-metadata/  \
        --with-nagios-plugin-dir=%{_libdir}/nagios/plugins/

make %{_smp_mflags} V=1

%check
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

mkdir -p ${RPM_BUILD_ROOT}%{_sysconfdir}/sysconfig
install -m 644 daemons/pacemakerd/pacemaker.sysconfig ${RPM_BUILD_ROOT}%{_sysconfdir}/sysconfig/pacemaker
install -m 644 tools/crm_mon.sysconfig ${RPM_BUILD_ROOT}%{_sysconfdir}/sysconfig/crm_mon

mkdir -p %{buildroot}%{_datadir}/pacemaker/nagios/plugins-metadata
for file in $(find %{nagios_name}-%{nagios_hash}/metadata -type f); do
    install -m 644 $file %{buildroot}%{_datadir}/pacemaker/nagios/plugins-metadata
done


mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/lib/rpm-state/%{name}

# These are not actually scripts
find %{buildroot} -name '*.xml' -type f -print0 | xargs -0 chmod a-x

# Don't package static libs
find %{buildroot} -name '*.a' -type f -print0 | xargs -0 rm -f
find %{buildroot} -name '*.la' -type f -print0 | xargs -0 rm -f

# Do not package these either
rm -f %{buildroot}/%{_sbindir}/fence_legacy
rm -f %{buildroot}/%{_mandir}/man8/fence_legacy.*

# For now, don't package the servicelog-related binaries built only for
# ppc64le when certain dependencies are installed. If they get more exercise by
# advanced users, we can reconsider.
rm -f %{buildroot}/%{_sbindir}/notifyServicelogEvent
rm -f %{buildroot}/%{_sbindir}/ipmiservicelogd

# Don't ship init scripts for systemd based platforms
rm -f %{buildroot}/%{_initrddir}/pacemaker
rm -f %{buildroot}/%{_initrddir}/pacemaker_remote

# Byte-compile Python sources where suitable and the distro procedures known
%if %{defined py_byte_compile} && %{defined python_path}
%{py_byte_compile %{python_path} %{buildroot}%{_datadir}/pacemaker/tests}
%if !%{defined _python_bytecompile_extra}
%{py_byte_compile %{python_path} %{buildroot}%{py_site}/cts}
%endif
%endif

%if %{with coverage}
GCOV_BASE=%{buildroot}/%{_var}/lib/pacemaker/gcov
mkdir -p $GCOV_BASE
find . -name '*.gcno' -type f | while read F ; do
        D=`dirname $F`
        mkdir -p ${GCOV_BASE}/$D
        cp $F ${GCOV_BASE}/$D
done
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
if [ "$1" = 2 ]; then
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

%pre libs
# XXX keep an eye on https://fedoraproject.org/wiki/Changes/SystemdSysusers
#     reopened recently:
# https://lists.fedoraproject.org/archives/list/devel@lists.fedoraproject.org/message/AETGESYR4IEQJMA6SKL7OERSDZFWFNEU/
getent group %{gname} >/dev/null || groupadd -r %{gname} -g 189
getent passwd %{uname} >/dev/null || useradd -r -g %{gname} -u 189 -s /sbin/nologin -c "cluster user" %{uname}
exit 0

%ldconfig_scriptlets libs
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
%if %{with legacy_links}
%exclude %{_sbindir}/pacemaker_remoted
%endif
%{_libexecdir}/pacemaker/*

%{_sbindir}/crm_attribute
%{_sbindir}/crm_master

%doc %{_mandir}/man7/pacemaker-controld.*
%doc %{_mandir}/man7/pacemaker-schedulerd.*
%doc %{_mandir}/man7/pacemaker-fenced.*
%doc %{_mandir}/man7/ocf_pacemaker_controld.*
%doc %{_mandir}/man7/ocf_pacemaker_remote.*
%doc %{_mandir}/man8/crm_attribute.*
%doc %{_mandir}/man8/crm_master.*
%doc %{_mandir}/man8/pacemakerd.*

%doc %{_datadir}/pacemaker/alerts

%license licenses/GPLv2
%doc COPYING
%doc ChangeLog

%dir %attr (750, %{uname}, %{gname}) %{_var}/lib/pacemaker/cib
%dir %attr (750, %{uname}, %{gname}) %{_var}/lib/pacemaker/pengine
/usr/lib/ocf/resource.d/pacemaker/controld
/usr/lib/ocf/resource.d/pacemaker/remote

%files cli
%dir %attr (750, root, %{gname}) %{_sysconfdir}/pacemaker
%config(noreplace) %{_sysconfdir}/logrotate.d/pacemaker
%config(noreplace) %{_sysconfdir}/sysconfig/crm_mon

%{_unitdir}/crm_mon.service

%{_sbindir}/attrd_updater
%{_sbindir}/cibadmin
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

%exclude /usr/lib/ocf/resource.d/pacemaker/controld
%exclude /usr/lib/ocf/resource.d/pacemaker/o2cb
%exclude /usr/lib/ocf/resource.d/pacemaker/remote

%dir /usr/lib/ocf
%dir /usr/lib/ocf/resource.d
/usr/lib/ocf/resource.d/pacemaker

%doc %{_mandir}/man7/*
%exclude %{_mandir}/man7/pacemaker-controld.*
%exclude %{_mandir}/man7/pacemaker-schedulerd.*
%exclude %{_mandir}/man7/pacemaker-fenced.*
%exclude %{_mandir}/man7/ocf_pacemaker_controld.*
%exclude %{_mandir}/man7/ocf_pacemaker_o2cb.*
%exclude %{_mandir}/man7/ocf_pacemaker_remote.*
%doc %{_mandir}/man8/*
%exclude %{_mandir}/man8/crm_attribute.*
%exclude %{_mandir}/man8/crm_master.*
%exclude %{_mandir}/man8/fence_legacy.*
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

%files libs
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
%if %{with legacy_links}
%{_sbindir}/pacemaker_remoted
%endif
%{_mandir}/man8/pacemaker-remoted.*
%license licenses/GPLv2
%doc COPYING
%doc ChangeLog

%files doc
%doc %{pcmk_docdir}
%license licenses/CC-BY-SA-4.0

%files cts
%{py_site}/cts
%{_datadir}/pacemaker/tests

%{_libexecdir}/pacemaker/cts-log-watcher
%{_libexecdir}/pacemaker/cts-support

%license licenses/GPLv2
%doc COPYING
%doc ChangeLog

%files libs-devel
%{_includedir}/pacemaker
%{_libdir}/*.so
%if %{with coverage}
%{_var}/lib/pacemaker/gcov
%endif
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
%{_datadir}/pkgconfig/pacemaker-schemas.pc

%files nagios-plugins-metadata
%dir %{_datadir}/pacemaker/nagios
%dir %{_datadir}/pacemaker/nagios/plugins-metadata
%attr(0644,root,root) %{_datadir}/pacemaker/nagios/plugins-metadata/*
%license %{nagios_name}-%{nagios_hash}/COPYING

%changelog
* Tue Mar 23 2021 jiangxinyu <jiangxinyu@kylinos.cn> - 2.0.3-2
- Add 'Resolve-the-failure-of-time-matching-in-test-cases.patch' file 2.0.3-2

* Thu Nov 05 2020 jiangxinyu <jiangxinyu@kylinos.cn> - 2.0.3-1
- Upgrade the pacemaker package version to 2.0.3-1

* Wed Apr 15 2020 houjian<houjian@kylinos.cn> - 2.0.2-3.2
- Init pacemaker project
