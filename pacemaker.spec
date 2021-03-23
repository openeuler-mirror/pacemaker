# Globals and defines to control package behavior (configure these as desired)

## User and group to use for nonprivileged services
%global uname hacluster
%global gname haclient

## Where to install Pacemaker documentation
%global pcmk_docdir %{_docdir}/%{name}-doc

## GitHub entity that distributes source (for ease of using a fork)
%global github_owner ClusterLabs

## Upstream pacemaker version, and its package version (specversion
## can be incremented to build packages reliably considered "newer"
## than previously built packages with the same pcmkversion)
%global pcmkversion 2.0.3
%global specversion 2

## Upstream commit (or git tag, such as "Pacemaker-" plus the
## {pcmkversion} macro for an official release) to use for this package
%global commit 744a30d655c9fbd66ad6e103697db0283bb90779
## Since git v2.11, the extent of abbreviation is autoscaled by default
## (used to be constant of 7), so we need to convey it for non-tags, too.
%global commit_abbrev 7

## Python major version to use (2, 3, or 0 for auto-detect)
%global python_major 0

## Nagios source control identifiers
%global nagios_name nagios-agents-metadata
%global nagios_hash 105ab8a


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

## Whether this platform defaults to using systemd as an init system
## (needs to be evaluated prior to BuildRequires being enumerated and
## installed as it's intended to conditionally select some of these, and
## for that there are only few indicators with varying reliability:
## - presence of systemd-defined macros (when building in a full-fledged
##   environment, which is not the case with ordinary mock-based builds)
## - systemd-aware rpm as manifested with the presence of particular
##   macro (rpm itself will trivially always be present when building)
## - existence of /usr/lib/os-release file, which is something heavily
##   propagated by systemd project
## - when not good enough, there's always a possibility to check
##   particular distro-specific macros (incl. version comparison)
%define systemd_native (%{?_unitdir:1}%{!?_unitdir:0}%{nil \
  } || %{?__transaction_systemd_inhibit:1}%{!?__transaction_systemd_inhibit:0}%{nil \
  } || %(test -f /usr/lib/os-release; test $? -ne 0; echo $?))

# Even though we pass @SYSTEM here, Pacemaker is still an exception to the
# crypto policies because it adds "+ANON-DH" for CIB remote commands and
# "+DHE-PSK:+PSK" for Pacemaker Remote connections. This is currently
# required for the respective functionality.
## Base GnuTLS cipher priorities (presumably only the initial, required keyword)
## overridable with "rpmbuild --define 'pcmk_gnutls_priorities PRIORITY-SPEC'"
%define gnutls_priorities %{?pcmk_gnutls_priorities}%{!?pcmk_gnutls_priorities:@SYSTEM}

# Python-related definitions

## Use Python 3 on certain platforms if major version not specified
%if %{?python_major} == 0
%global python_major 3
%endif

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
%if 0%{?python_major} > 2
%global python_name python3
%global python_path %{?__python3}%{!?__python3:/usr/bin/python%{?python3_pkgversion}%{!?python3_pkgversion:3}}
%define python_site %{?python3_sitelib}%{!?python3_sitelib:%(
  %{python_path} -c 'from distutils.sysconfig import get_python_lib as gpl; print(gpl(1))' 2>/dev/null)}
%else
%if 0%{?python_major} > 1
%global python_name python2
%global python_path %{?__python2}%{!?__python2:/usr/bin/python%{?python2_pkgversion}%{!?python2_pkgversion:2}}
%define python_site %{?python2_sitelib}%{!?python2_sitelib:%(
  %{python_path} -c 'from distutils.sysconfig import get_python_lib as gpl; print(gpl(1))' 2>/dev/null)}
%else
%global python_name python
%global python_path %{?__python}%{!?__python:/usr/bin/python%{?python_pkgversion}}
%define python_site %{?python_sitelib}%{!?python_sitelib:%(
  python -c 'from distutils.sysconfig import get_python_lib as gpl; print(gpl(1))' 2>/dev/null)}
%endif
%endif


# Definitions for backward compatibility with older RPM versions

## Ensure the license macro behaves consistently (older RPM will otherwise
## overwrite it once it encounters "License:"). Courtesy Jason Tibbitts:
## https://pkgs.fedoraproject.org/cgit/rpms/epel-rpm-macros.git/tree/macros.zzz-epel?h=el6&id=e1adcb77
%if !%{defined _licensedir}
%define description %{lua:
    rpm.define("license %doc")
    print("%description")
}
%endif


# Define conditionals so that "rpmbuild --with <feature>" and
# "rpmbuild --without <feature>" can enable and disable specific features

## Add option to enable support for stonith/external fencing agents
%bcond_with stonithd

## Add option to create binaries suitable for use with profiling tools
%bcond_with profiling

## Add option to create binaries with coverage analysis
%bcond_with coverage

## Add option to generate documentation (requires Publican, Asciidoc and Inkscape)
%bcond_with doc

## Add option to prefix package version with "0."
## (so later "official" packages will be considered updates)
%bcond_with pre_release

## Add option to ship Upstart job files
%bcond_with upstart_job

## Add option to turn off hardening of libraries and daemon executables
%bcond_without hardening

## Add option to disable links for legacy daemon names
%bcond_without legacy_links


# Keep sane profiling data if requested
%if %{with profiling}

## Disable -debuginfo package and stripping binaries/libraries
%define debug_package %{nil}

%endif


# Define the release version
# (do not look at externally enforced pre-release flag for tagged releases
# as only -rc tags, captured with the second condition, implies that then)
%if (!%{tag_release} && %{with pre_release}) || 0%{pre_release}
%if 0%{pre_release}
%define pcmk_release 0.%{specversion}.%(s=%{shortcommit}; echo ${s: -3})
%else
%define pcmk_release 0.%{specversion}.%{shortcommit}.git
%endif
%else
%if 0%{tag_release}
%define pcmk_release %{specversion}
%else
# Never use the short commit in a RHEL release number
%define pcmk_release %{specversion}
%endif
%endif

Name:          pacemaker
Summary:       Scalable High-Availability cluster resource manager
Version:       %{pcmkversion}
Release:       %{pcmk_release}%{?dist}.2
%if %{defined _unitdir}
License:       GPLv2+ and LGPLv2+
%else
# initscript is Revised BSD
License:       GPLv2+ and LGPLv2+ and BSD
%endif
Url:           http://www.clusterlabs.org
Group:         System Environment/Daemons

# Hint: use "spectool -s 0 pacemaker.spec" (rpmdevtools) to check the final URL:
# https://github.com/ClusterLabs/pacemaker/archive/e91769e5a39f5cb2f7b097d3c612368f0530535e/pacemaker-e91769e.tar.gz
Source0:       https://github.com/%{github_owner}/%{name}/archive/%{commit}/%{name}-%{shortcommit}.tar.gz
Source1:       https://github.com/%{github_owner}/%{nagios_name}/archive/%{nagios_hash}/%{nagios_name}-%{nagios_hash}.tar.gz
# ---
Patch0:        Build-fix-unability-to-build-with-Inkscape-1.0-beta-.patch
Patch1:        Resolve-the-failure-of-time-matching-in-test-cases.patch

Requires:      resource-agents
Requires:      %{name}-libs%{?_isa} = %{version}-%{release}
Requires:      %{name}-cluster-libs%{?_isa} = %{version}-%{release}
Requires:      %{name}-cli = %{version}-%{release}
%if !%{defined _unitdir}
Requires:      procps-ng
Requires:      psmisc
%endif
%{?systemd_requires}

ExclusiveArch: aarch64 i686 ppc64le s390x x86_64 %{arm}

Requires:      %{python_path}
BuildRequires: %{python_name}-devel

# Pacemaker requires a minimum libqb functionality
Requires:      libqb >= 0.17.0
BuildRequires: libqb-devel >= 0.17.0

# Basics required for the build (even if usually satisfied through other BRs)
BuildRequires: coreutils findutils grep sed

# Required for core functionality
BuildRequires: automake autoconf gcc libtool pkgconfig libtool-devel
BuildRequires: pkgconfig(glib-2.0) >= 2.16
#BuildRequires: libxml2-devel libxslt-devel libuuid-devel
BuildRequires: libxml2-devel libxslt-devel util-linux-devel
BuildRequires: bzip2-devel

# Enables optional functionality
BuildRequires: ncurses-devel docbook-style-xsl
BuildRequires: help2man gnutls-devel pam-devel pkgconfig(dbus-1)

%if %{systemd_native}
BuildRequires: pkgconfig(systemd)
%endif

# RH patches are created by git, so we need git to apply them
BuildRequires: git

Requires:      corosync >= 2.0.0
BuildRequires: corosynclib-devel >= 2.0.0

%if %{with stonithd}
BuildRequires: cluster-glue-libs-devel
%endif

## (note no avoiding effect when building through non-customized mock)
%if !%{bleeding}
%if %{with doc}
BuildRequires: inkscape asciidoc publican
%endif
%endif

Provides:      pcmk-cluster-manager = %{version}-%{release}
Provides:      pcmk-cluster-manager%{?_isa} = %{version}-%{release}

# Bundled bits
## Pacemaker uses the crypto/md5-buffer module from gnulib
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
  --with(out) : coverage doc stonithd hardening pre_release profiling

%package cli
License:       GPLv2+ and LGPLv2+
Summary:       Command line tools for controlling Pacemaker clusters
Group:         System Environment/Daemons
Requires:      %{name}-libs%{?_isa} = %{version}-%{release}
#Recommends:    pcmk-cluster-manager = %{version}-%{release}
Requires:      tar
Requires:      bzip2
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
Group:         System Environment/Daemons
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
Group:         System Environment/Daemons
Requires:      %{name}-libs%{?_isa} = %{version}-%{release}

%description cluster-libs
Pacemaker is an advanced, scalable High-Availability cluster resource
manager.

The %{name}-cluster-libs package contains cluster-aware shared
libraries needed for nodes that will form part of the cluster nodes.

%package remote
%if %{defined _unitdir}
License:       GPLv2+ and LGPLv2+
%else
# initscript is Revised BSD
License:       GPLv2+ and LGPLv2+ and BSD
%endif
Summary:       Pacemaker remote daemon for non-cluster nodes
Group:         System Environment/Daemons
Requires:      %{name}-libs%{?_isa} = %{version}-%{release}
Requires:      %{name}-cli = %{version}-%{release}
Requires:      resource-agents
%if !%{defined _unitdir}
Requires:      procps-ng
%endif
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
Group:         Development/Libraries
Requires:      %{name}-libs%{?_isa} = %{version}-%{release}
Requires:      %{name}-cluster-libs%{?_isa} = %{version}-%{release}
Requires:      util-linux-devel%{?_isa} libtool-devel%{?_isa}
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
Group:         System Environment/Daemons
Requires:      %{python_path}
Requires:      %{name}-libs = %{version}-%{release}
Requires:      procps-ng
Requires:      psmisc
BuildArch:     noarch

# systemd python bindings are separate package in some distros
%if %{defined systemd_requires}

Requires:      %{python_name}-systemd

%endif

%description   cts
Test framework for cluster-related technologies like Pacemaker

%package       doc
License:       CC-BY-SA-4.0
Summary:       Documentation for Pacemaker
Group:         Documentation
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
Group:         System Environment/Daemons
# NOTE below are the plugins this metadata uses.
# These packages are not requirements because RHEL does not ship these plugins.
# This metadata provides third-party support for nagios. Users may install the
# plugins via third-party rpm packages, or source. If RHEL ships the plugins in
# the future, we should consider enabling the following required fields.
#Requires:      nagios-plugins-http
#Requires:      nagios-plugins-ldap
#Requires:      nagios-plugins-mysql
#Requires:      nagios-plugins-pgsql
#Requires:      nagios-plugins-tcp
Requires:      pcmk-cluster-manager
BuildArch:     noarch

%description   nagios-plugins-metadata
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

export systemdunitdir=%{?_unitdir}%{!?_unitdir:no}

# RHEL changes pacemaker's concurrent-fencing default to true
export CPPFLAGS="-DDEFAULT_CONCURRENT_FENCING_TRUE"

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
        %{!?with_legacy_links: --disable-legacy-links}                          \
        %{?with_profiling:     --with-profiling}                                \
        %{?with_coverage:      --with-coverage}                                 \
        %{!?with_doc:          --with-brand=}                                   \
        %{?gnutls_priorities:  --with-gnutls-priorities="%{gnutls_priorities}"} \
        --with-initdir=%{_initrddir}                                            \
        --localstatedir=%{_var}                                                 \
        --with-bug-url=https://bugzilla.redhat.com/                             \
        --with-nagios                                                             \
        --with-nagios-metadata-dir=%{_datadir}/pacemaker/nagios/plugins-metadata/ \
        --with-nagios-plugin-dir=%{_libdir}/nagios/plugins/                       \
        --with-version=%{version}-%{release}

%if 0%{?suse_version} >= 1200
# Fedora handles rpath removal automagically
sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool
%endif

make %{_smp_mflags} V=1 all

#%check
#{ cts/cts-scheduler --run load-stopped-loop \
#  && cts/cts-cli \
#  && touch .CHECKED
#} 2>&1 | sed 's/[fF]ail/faiil/g'  # prevent false positives in rpmlint
#[ -f .CHECKED ] && rm -f -- .CHECKED
#exit $?  # TODO remove when rpm<4.14 compatibility irrelevant


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

%if %{with upstart_job}
mkdir -p ${RPM_BUILD_ROOT}%{_sysconfdir}/init
install -m 644 pacemakerd/pacemaker.upstart ${RPM_BUILD_ROOT}%{_sysconfdir}/init/pacemaker.conf
install -m 644 pacemakerd/pacemaker.combined.upstart ${RPM_BUILD_ROOT}%{_sysconfdir}/init/pacemaker.combined.conf
install -m 644 tools/crm_mon.upstart ${RPM_BUILD_ROOT}%{_sysconfdir}/init/crm_mon.conf
%endif

mkdir -p %{buildroot}%{_datadir}/pacemaker/nagios/plugins-metadata
for file in $(find %{nagios_name}-%{nagios_hash}/metadata -type f); do
    install -m 644 $file %{buildroot}%{_datadir}/pacemaker/nagios/plugins-metadata
done

%if %{defined _unitdir}
mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/lib/rpm-state/%{name}
%endif

# Don't package static libs
find %{buildroot} -name '*.a' -type f -print0 | xargs -0 rm -f
find %{buildroot} -name '*.la' -type f -print0 | xargs -0 rm -f

# Do not package these either
rm -f %{buildroot}/%{_sbindir}/fence_legacy
rm -f %{buildroot}/%{_mandir}/man8/fence_legacy.*
find %{buildroot} -name '*o2cb*' -type f -print0 | xargs -0 rm -f

# For now, don't package the servicelog-related binaries built only for
# ppc64le when certain dependencies are installed. If they get more exercise by
# advanced users, we can reconsider.
rm -f %{buildroot}/%{_sbindir}/notifyServicelogEvent
rm -f %{buildroot}/%{_sbindir}/ipmiservicelogd

# Don't ship init scripts for systemd based platforms
%if %{defined _unitdir}
rm -f %{buildroot}/%{_initrddir}/pacemaker
rm -f %{buildroot}/%{_initrddir}/pacemaker_remote
%endif

# Byte-compile Python sources where suitable and the distro procedures known
%if %{defined py_byte_compile}
%{py_byte_compile %{python_path} %{buildroot}%{_datadir}/pacemaker/tests}
%if !%{defined _python_bytecompile_extra}
%{py_byte_compile %{python_path} %{buildroot}%{python_site}/cts}
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
%if %{defined _unitdir}
%systemd_post pacemaker.service
%else
/sbin/chkconfig --add pacemaker || :
%endif

%preun
%if %{defined _unitdir}
%systemd_preun pacemaker.service
%else
/sbin/service pacemaker stop >/dev/null 2>&1 || :
if [ "$1" -eq 0 ]; then
    # Package removal, not upgrade
    /sbin/chkconfig --del pacemaker || :
fi
%endif

%postun
%if %{defined _unitdir}
%systemd_postun_with_restart pacemaker.service
%endif

%pre remote
%if %{defined _unitdir}
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
%endif

%post remote
%if %{defined _unitdir}
%systemd_post pacemaker_remote.service
%else
/sbin/chkconfig --add pacemaker_remote || :
%endif

%preun remote
%if %{defined _unitdir}
%systemd_preun pacemaker_remote.service
%else
/sbin/service pacemaker_remote stop >/dev/null 2>&1 || :
if [ "$1" -eq 0 ]; then
    # Package removal, not upgrade
    /sbin/chkconfig --del pacemaker_remote || :
fi
%endif

%postun remote
%if %{defined _unitdir}
# This next line is a no-op, because we stopped the service earlier, but
# we leave it here because it allows us to revert to the standard behavior
# in the future if desired
%systemd_postun_with_restart pacemaker_remote.service
# Explicitly take care of removing the flag-file(s) upon final removal
if [ "$1" -eq 0 ] ; then
    rm -f %{_localstatedir}/lib/rpm-state/%{name}/restart_pacemaker_remote
fi
%endif

%posttrans remote
%if %{defined _unitdir}
if [ -e %{_localstatedir}/lib/rpm-state/%{name}/restart_pacemaker_remote ] ; then
    systemctl start pacemaker_remote >/dev/null 2>&1
    rm -f %{_localstatedir}/lib/rpm-state/%{name}/restart_pacemaker_remote
fi
%endif

%post cli
%if %{defined _unitdir}
%systemd_post crm_mon.service
%endif
if [ "$1" -eq 2 ]; then
    # Package upgrade, not initial install:
    # Move any pre-2.0 logs to new location to ensure they get rotated
    { mv -fbS.rpmsave %{_var}/log/pacemaker.log* %{_var}/log/pacemaker \
      || mv -f %{_var}/log/pacemaker.log* %{_var}/log/pacemaker
    } >/dev/null 2>/dev/null || :
fi

%preun cli
%if %{defined _unitdir}
%systemd_preun crm_mon.service
%endif

%postun cli
%if %{defined _unitdir}
%systemd_postun_with_restart crm_mon.service
%endif

%pre libs
getent group %{gname} >/dev/null || groupadd -r %{gname} -g 189
getent passwd %{uname} >/dev/null || useradd -r -g %{gname} -u 189 -s /sbin/nologin -c "cluster user" %{uname}
exit 0

%if %{defined ldconfig_scriptlets}
%ldconfig_scriptlets libs
%ldconfig_scriptlets cluster-libs
%else
%post libs -p /sbin/ldconfig
%postun libs -p /sbin/ldconfig

%post cluster-libs -p /sbin/ldconfig
%postun cluster-libs -p /sbin/ldconfig
%endif

%files
###########################################################
%config(noreplace) %{_sysconfdir}/sysconfig/pacemaker
%{_sbindir}/pacemakerd

%if %{defined _unitdir}
%{_unitdir}/pacemaker.service
%else
%{_initrddir}/pacemaker
%endif

%exclude %{_libexecdir}/pacemaker/cts-log-watcher
%exclude %{_libexecdir}/pacemaker/cts-support
%exclude %{_sbindir}/pacemaker-remoted
%if %{with legacy_links}
%exclude %{_sbindir}/pacemaker_remoted
%endif
%exclude %{_datadir}/pacemaker/nagios
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

%if %{with upstart_job}
%config(noreplace) %{_sysconfdir}/init/pacemaker.conf
%config(noreplace) %{_sysconfdir}/init/pacemaker.combined.conf
%endif

%files cli
%dir %attr (750, root, %{gname}) %{_sysconfdir}/pacemaker
%config(noreplace) %{_sysconfdir}/logrotate.d/pacemaker
%config(noreplace) %{_sysconfdir}/sysconfig/crm_mon

%if %{defined _unitdir}
%{_unitdir}/crm_mon.service
%endif

%if %{with upstart_job}
%config(noreplace) %{_sysconfdir}/init/crm_mon.conf
%endif

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
%exclude /usr/lib/ocf/resource.d/pacemaker/remote

%dir /usr/lib/ocf
%dir /usr/lib/ocf/resource.d
/usr/lib/ocf/resource.d/pacemaker

%doc %{_mandir}/man7/*
%exclude %{_mandir}/man7/pacemaker-controld.*
%exclude %{_mandir}/man7/pacemaker-schedulerd.*
%exclude %{_mandir}/man7/pacemaker-fenced.*
%exclude %{_mandir}/man7/ocf_pacemaker_controld.*
%exclude %{_mandir}/man7/ocf_pacemaker_remote.*
%doc %{_mandir}/man8/*
%exclude %{_mandir}/man8/crm_attribute.*
%exclude %{_mandir}/man8/crm_master.*
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
%if %{defined _unitdir}
# state directory is shared between the subpackets
# let rpm take care of removing it once it isn't
# referenced anymore and empty
%ghost %dir %{_localstatedir}/lib/rpm-state/%{name}
%{_unitdir}/pacemaker_remote.service
%else
%{_initrddir}/pacemaker_remote
%endif

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
%{python_site}/cts
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

%files nagios-plugins-metadata
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
