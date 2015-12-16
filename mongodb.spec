%{?scl:%scl_package mongodb}
%global pkg_name mongodb
# this macro is provided by the SCL meta package`s subpackage "SCL-scldevel"
# and injected into build-root automagically by relengs
%{?scl_v8_mongodb:%global scl_v8_mongodb_prefix %{scl_v8_mongodb}-}

Name:           %{?scl_prefix}mongodb
Version:        2.4.9
Release:        8%{?dist}
Summary:        High-performance, schema-free document-oriented database
Group:          Applications/Databases
License:        AGPLv3 and zlib and ASL 2.0
# util/md5 is under the zlib license
# manpages and bson are under ASL 2.0
# everything else is AGPLv3
URL:            http://www.mongodb.org

Source0:        http://fastdl.mongodb.org/src/%{pkg_name}-src-r%{version}.tar.gz
Source1:        %{pkg_name}-tmpfile
Source2:        %{pkg_name}.logrotate
Source3:        %{pkg_name}.conf
Source4:        %{pkg_name}.init
Source5:        %{pkg_name}.service
Source6:        %{pkg_name}.sysconf
Source7:        %{pkg_name}-shard.conf
Source8:        %{pkg_name}-shard.init
Source9:        %{pkg_name}-shard.service
Source10:       %{pkg_name}-shard.sysconf

Patch1:         mongodb-2.4.5-no-term.patch
##Patch 2 - make it possible to use system libraries
Patch2:         mongodb-2.4.5-use-system-version.patch
##Patch 5 - https://jira.mongodb.org/browse/SERVER-9210
Patch5:         mongodb-2.4.5-boost-fix.patch
##Patch 6 - https://github.com/mongodb/mongo/commit/1d42a534e0eb1e9ac868c0234495c0333d57d7c1
Patch6:         mongodb-2.4.5-boost-size-fix.patch
##Patch 7 - https://bugzilla.redhat.com/show_bug.cgi?id=958014
## Need to work on getting this properly patched upstream
Patch7:         mongodb-2.4.5-pass-flags.patch
##Patch 8 - Compile with GCC 4.8
Patch8:         mongodb-2.4.5-gcc48.patch
##Patch 10 - Support atomics on ARM
Patch10:        mongodb-2.4.5-atomics.patch
Patch12:        mongodb-2.4.6-use-ld-library-path.patch

Requires:       %{?scl_v8_mongodb_prefix}v8
BuildRequires:  python-devel
BuildRequires:  %{?scl_prefix}scons
BuildRequires:  openssl-devel
BuildRequires:  boost-devel
BuildRequires:  pcre-devel
BuildRequires:  %{?scl_v8_mongodb_prefix}v8-devel
BuildRequires:  readline-devel
BuildRequires:  libpcap-devel
# provides tcmalloc
BuildRequires:  %{?scl_prefix}gperftools-devel
# TODO this is no more in the Fedora spec file
#BuildRequires:  %{?scl_prefix}libunwind-devel
%if 0%{?rhel} >= 7
BuildRequires:  systemd
BuildRequires:  snappy-devel
%else
BuildRequires:  %{?scl_prefix}snappy-devel
%endif

# Mongodb must run on a little-endian CPU (see bug #630898)
ExcludeArch:    ppc ppc64 %{sparc} s390 s390x

%{?scl:Requires:%scl_runtime}

%description
Mongo (from "humongous") is a high-performance, open source, schema-free
document-oriented database. MongoDB is written in C++ and offers the following
features:
    * Collection oriented storage: easy storage of object/JSON-style data
    * Dynamic queries
    * Full index support, including on inner objects and embedded arrays
    * Query profiling
    * Replication and fail-over support
    * Efficient storage of binary data including large objects (e.g. photos
    and videos)
    * Auto-sharding for cloud-level scalability (currently in early alpha)
    * Commercial Support Available

A key goal of MongoDB is to bridge the gap between key/value stores (which are
fast and highly scalable) and traditional RDBMS systems (which are deep in
functionality).

%package -n %{scl}-lib%{pkg_name}
Summary:        MongoDB shared libraries
Group:          Development/Libraries
%{?scl:Requires:%scl_runtime}

%description -n %{scl}-lib%{pkg_name}
This package provides the shared library for the MongoDB client.

%package -n %{scl}-lib%{pkg_name}-devel
Summary:        MongoDB header files
Group:          Development/Libraries
Requires:       %{?scl_prefix}lib%{pkg_name} = %{version}-%{release}
Requires:       boost-devel
Provides:       %{?scl_prefix}%{pkg_name}-devel = %{version}-%{release}
Obsoletes:      %{?scl_prefix}%{pkg_name}-devel < 2.6
%{?scl:Requires:%scl_runtime}

%description -n %{scl}-lib%{pkg_name}-devel
This package provides the header files and C++ driver for MongoDB. MongoDB is
a high-performance, open source, schema-free document-oriented database.

%package server
Summary:        MongoDB server, sharding server and support scripts
Group:          Applications/Databases
Requires(pre):  shadow-utils
Requires:       %{?scl_v8_mongodb_prefix}v8
%if 0%{?rhel} >= 7
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
%else
Requires(post): chkconfig
Requires(preun): chkconfig
Requires(postun): initscripts
%endif
%{?scl:Requires:%scl_runtime}

%description server
This package provides the mongo server software, mongo sharding server
software, default configuration files, and init scripts.


%prep
%setup -q -n mongodb-src-r%{version}
%patch1 -p1
%patch2 -p1
%patch5 -p1
%patch6 -p1
%patch7 -p1
%patch8 -p1
%patch10 -p1 -b .atomics
%patch12 -p1 -b .paths

# copy them (we will change their content)
cp %{SOURCE1} %{SOURCE2} %{SOURCE3} %{SOURCE4} %{SOURCE5} \
  %{SOURCE6} %{SOURCE7} %{SOURCE8} %{SOURCE9} %{SOURCE10} ./

for f in %{SOURCE4} %{SOURCE8}; do
  sed -i -r -e 's|/usr/bin|%{_bindir}|g' \
    -e 's|(/var/run/mongodb)|%{?_scl_root}\1|g' \
    -e 's|(/var/log/)(mongodb)|\1%{?scl_prefix}\2|g' \
    -e 's|/etc(/mongodb(-shard)?\.conf)|%{?_sysconfdir}\1|g' \
    -e 's|/etc(/sysconfig)|%{?_sysconfdir}\1|g' \
    -e 's|(/var/lock)|%{?_scl_root}\1|g' \
    -e 's|__SCL_SCRIPTS__|%{?_scl_scripts}|g' \
    -e "s|__list of scls__|\$$(printf '%%s' '%{scl}' |
    tr '[:lower:][:space:]' '[:upper:]_')_SCLS_ENABLED|g" \
      "$(basename "$f")"
done

sed -i -r -e "s|(/var/log/)(mongodb)|\1%{?scl_prefix}\2|g" \
  -e "s|(/var/run/mongodb)|%{?_scl_root}\1|g" \
  "$(basename %{SOURCE2})"

for f in %{SOURCE3} %{SOURCE7}; do
  sed -i -r -e 's|(/var/lib/mongodb)|%{?_scl_root}\1|g' \
    -e 's|(/var/run/mongodb)|%{?_scl_root}\1|g' \
    -e 's|(/var/log/)(mongodb)|\1%{?scl_prefix}\2|g' \
    "$(basename "$f")"
done

for f in %{SOURCE6} %{SOURCE10}; do
  sed -i -r -e 's|/etc(/mongodb(-shard)?\.conf)|%{_sysconfdir}\1|g' \
    "$(basename "$f")"
done

sed -i -r -e 's|(/run/mongodb)|%{?_scl_root}/var/\1|g' \
  "$(basename %{SOURCE1})"

for f in %{SOURCE5} %{SOURCE9}; do
  #FIXME check if the _SCLS_ENABLED var isn't empty!
  sed -i -r -e 's|(/var/run/mongodb)|%{?_scl_root}\1|g' \
    -e 's|/etc(/sysconfig/mongodb)|%{_sysconfdir}\1|g' \
    -e 's|/usr/bin(/mongo[ds])|%{_bindir}\1|g' \
    -e 's|__SCL_SCRIPTS__|%{?_scl_scripts}|g' \
    -e "s|__list of scls__|\$$(printf '%%s' '%{scl}' |
    tr '[:lower:][:space:]' '[:upper:]_')_SCLS_ENABLED|g" \
      "$(basename "$f")"
done

# spurious permissions
chmod -x README

# wrong end-of-file encoding
sed -i 's/\r//' README

# Put lib dir in correct place
# https://jira.mongodb.org/browse/SERVER-10049
sed -i -e "s@\$INSTALL_DIR/lib@\$INSTALL_DIR/%{_lib}@g" src/SConscript.client

# prefix client library with %{scl_prefix}%{version}
(pre='EnsureSConsVersion(2, 3, 0)'
post='sharedLibEnv.AppendUnique(SHLIBVERSION="%{?scl_prefix}%{version}")'
sed -i -r \
  -e "s|([[:space:]]*)(sharedLibEnv *= *env.Clone.*)|\1$pre\n\1\2\n\1$post|" \
  -e "s|(sharedLibEnv.)Install *\(|\1InstallVersionedLib(|" \
  src/SConscript.client)

#FIXME hack the mongodb build system to provide
#  /usr/lib64/mysql/libmysqlclient.so.mysql55-18
#  /usr/lib64/mysql/libmysqlclient.so.mysql55-18.0.0
#  => here change SConscript.client
#     in install

%build
# NOTE: Build flags must be EXACTLY the same in the install step!
# If you fail to do this, mongodb will be built twice...
%{?scl:scl enable %{scl} - << "EOF"}
# see add_option() calls in SConstruct for options
scons \
        %{?_smp_mflags} \
        --sharedclient \
        --use-system-all \
        --prefix=%{buildroot}%{_prefix} \
        --extrapath=%{_prefix} \
        --usev8 \
        --nostrip \
        --ssl \
        --full \
        --debug=findlibs \
        --d
%{?scl:EOF}

%install
# NOTE: Install flags must be EXACTLY the same in the build step!
# If you fail to do this, mongodb will be built twice...
%{?scl:scl enable %{scl} - << "EOF"}
scons install \
        %{?_smp_mflags} \
        --sharedclient \
        --use-system-all \
        --prefix=%{buildroot}%{_prefix} \
        --extrapath=%{_prefix} \
        --usev8 \
        --nostrip \
        --ssl \
        --full \
        --debug=findlibs \
        --d
#        --libpath=%{_libdir} \
%{?scl:EOF}
rm -f %{buildroot}%{_libdir}/libmongoclient.a
rm -f %{buildroot}%{_libdir}/../lib/libmongoclient.a

# TODO EPEL 4 & 5 expands to %{_prefix}/com, otherwise to /var/lib
#mkdir -p %{buildroot}%{_sharedstatedir}/%{pkg_name}
mkdir -p %{buildroot}%{_localstatedir}/lib/%{pkg_name}
mkdir -p %{buildroot}%{_root_localstatedir}/log/%{?scl_prefix}%{pkg_name}
mkdir -p %{buildroot}%{_localstatedir}/run/%{pkg_name}
mkdir -p %{buildroot}%{_sysconfdir}/sysconfig

%if 0%{?rhel} >= 7
install -p -D -m 644 "$(basename %{SOURCE1})"  %{buildroot}%{_libdir}/../lib/tmpfiles.d/%{?scl_prefix}%{pkg_name}.conf
install -p -D -m 644 "$(basename %{SOURCE5})"  %{buildroot}%{_unitdir}/%{?scl_prefix}%{pkg_name}.service
install -p -D -m 644 "$(basename %{SOURCE9})"  %{buildroot}%{_unitdir}/%{?scl_prefix}%{pkg_name}-shard.service
%else
install -p -D -m 755 "$(basename %{SOURCE4})"  %{buildroot}%{_root_initddir}/%{?scl_prefix}%{pkg_name}
install -p -D -m 755 "$(basename %{SOURCE8})"  %{buildroot}%{_root_initddir}/%{?scl_prefix}%{pkg_name}-shard
%endif
install -p -D -m 644 "$(basename %{SOURCE2})"  %{buildroot}%{?scl:%_root_sysconfdir}%{!?scl:%_sysconfdir}/logrotate.d/%{?scl_prefix}%{pkg_name}
install -p -D -m 644 "$(basename %{SOURCE3})"  %{buildroot}%{_sysconfdir}/%{pkg_name}.conf
install -p -D -m 644 "$(basename %{SOURCE7})"  %{buildroot}%{_sysconfdir}/%{pkg_name}-shard.conf
install -p -D -m 644 "$(basename %{SOURCE6})"  %{buildroot}%{_sysconfdir}/sysconfig/%{pkg_name}
install -p -D -m 644 "$(basename %{SOURCE10})" %{buildroot}%{_sysconfdir}/sysconfig/%{pkg_name}-shard

install -d -m 755            %{buildroot}%{_mandir}/man1
install -p -m 644 debian/*.1 %{buildroot}%{_mandir}/man1/


%post -p /sbin/ldconfig


%postun -p /sbin/ldconfig


%pre server
getent group %{pkg_name} >/dev/null || groupadd -r %{pkg_name}
getent passwd %{pkg_name} >/dev/null || \
# TODO _sharedstatedir
useradd -r -g %{pkg_name} -u 184 -d %{_localstatedir}/lib/%{pkg_name} -s /sbin/nologin \
-c "MongoDB Database Server" %{pkg_name}
exit 0


%post server
%if 0%{?rhel} >= 7
  # https://fedoraproject.org/wiki/Packaging:ScriptletSnippets#Systemd
  %tmpfiles_create %{?scl_prefix}%{pkg_name}.conf
  # daemon-reload
  %systemd_postun
%else
  /sbin/chkconfig --add %{?scl_prefix}%{pkg_name}
  /sbin/chkconfig --add %{?scl_prefix}%{pkg_name}-shard
%endif

# work-around for RHBZ#924044
%if 0%{?rhel} < 7
restorecon -R %{_scl_root} >/dev/null 2>&1 || :
restorecon -R %{_root_localstatedir}/log/%{?scl_prefix}%{pkg_name} >/dev/null 2>&1 || :
restorecon %{_root_initddir}/%{?scl_prefix}%{pkg_name}       >/dev/null 2>&1 || :
restorecon %{_root_initddir}/%{?scl_prefix}%{pkg_name}-shard >/dev/null 2>&1 || :
%endif

# FIXME set the SELinux context up and make it permanent
#chcon --reference /tmp /var/lib/%{pkg_name}/tmp
#chcon --reference /var/lib/%{pkg_name} tmp
##/usr/sbin/semanage fcontext -a -t mongod_db_t "/var/lib/%{pkg_name}/tmp(/.*)?"
# FIXME wtf?
#restorecon -R -v /var/lib/mysql

%preun server
if [ "$1" = 0 ]; then
%if 0%{?rhel} >= 7
  # --no-reload disable; stop
  %systemd_preun %{?scl_prefix}%{pkg_name}.service
  %systemd_preun %{?scl_prefix}%{pkg_name}-shard.service
%else
  /sbin/service %{?scl_prefix}%{pkg_name}       stop >/dev/null 2>&1
  /sbin/service %{?scl_prefix}%{pkg_name}-shard stop >/dev/null 2>&1
  /sbin/chkconfig --del %{?scl_prefix}%{pkg_name}
  /sbin/chkconfig --del %{?scl_prefix}%{pkg_name}-shard
%endif
fi


%postun server
%if 0%{?rhel} >= 7
  # daemon-reload
  %systemd_postun
%endif
if [ "$1" -ge 1 ]; then
%if 0%{?rhel} >= 7
  # try-restart
  %systemd_postun_with_restart %{?scl_prefix}%{pkg_name}.service
  %systemd_postun_with_restart %{?scl_prefix}%{pkg_name}-shard.service
%else
  /sbin/service %{?scl_prefix}%{pkg_name}       condrestart >/dev/null 2>&1 || :
  /sbin/service %{?scl_prefix}%{pkg_name}-shard condrestart >/dev/null 2>&1 || :
%endif
fi


%files
%{_bindir}/bsondump
%{_bindir}/mongo
%{_bindir}/mongodump
%{_bindir}/mongoexport
%{_bindir}/mongofiles
%{_bindir}/mongoimport
%{_bindir}/mongooplog
%{_bindir}/mongoperf
%{_bindir}/mongorestore
%{_bindir}/mongosniff
%{_bindir}/mongostat
%{_bindir}/mongotop

%{_mandir}/man1/bsondump.1*
%{_mandir}/man1/mongo.1*
%{_mandir}/man1/mongodump.1*
%{_mandir}/man1/mongoexport.1*
%{_mandir}/man1/mongofiles.1*
%{_mandir}/man1/mongoimport.1*
%{_mandir}/man1/mongooplog.1*
%{_mandir}/man1/mongoperf.1*
%{_mandir}/man1/mongorestore.1*
%{_mandir}/man1/mongosniff.1*
%{_mandir}/man1/mongostat.1*
%{_mandir}/man1/mongotop.1*

%files -n %{scl}-lib%{pkg_name}
%doc README GNU-AGPL-3.0.txt APACHE-2.0.txt
%{_libdir}/libmongoclient.so.%{?scl_prefix}%{version}

# usually contains ln -s /usr/lib/<???> lib<???>.so
%files -n %{scl}-lib%{pkg_name}-devel
%{_includedir}

%files server
%{_bindir}/mongod
%{_bindir}/mongos
%{_mandir}/man1/mongod.1*
%{_mandir}/man1/mongos.1*
# TODO
#%dir %attr(0750, %{pkg_name}, root) %{_sharedstatedir}/%{pkg_name}
%dir %attr(0750, %{pkg_name}, root) %{_localstatedir}/lib/%{pkg_name}
%dir %attr(0750, %{pkg_name}, root) %{_root_localstatedir}/log/%{?scl_prefix}%{pkg_name}
%dir %attr(0750, %{pkg_name}, root) %{_localstatedir}/run/%{pkg_name}
%config(noreplace) %{?scl:%_root_sysconfdir}%{!?scl:%_sysconfdir}/logrotate.d/%{?scl_prefix}%{pkg_name}
%config(noreplace) %{_sysconfdir}/%{pkg_name}.conf
%config(noreplace) %{_sysconfdir}/%{pkg_name}-shard.conf
%config(noreplace) %{_sysconfdir}/sysconfig/%{pkg_name}
%config(noreplace) %{_sysconfdir}/sysconfig/%{pkg_name}-shard
%if 0%{?rhel} >= 7
%{_unitdir}/*.service
%{_libdir}/../lib/tmpfiles.d/%{?scl_prefix}%{pkg_name}.conf
%else
%{_root_initddir}/%{?scl_prefix}%{pkg_name}
%{_root_initddir}/%{?scl_prefix}%{pkg_name}-shard
%endif

%changelog
* Mon Mar 31 2014 Honza Horak <hhorak@redhat.com> - 2.4.9-8
- Fix unix socket path in config file
  Related: #1057097

* Mon Mar 31 2014 Honza Horak <hhorak@redhat.com> - 2.4.9-7
- Fix configuration of shard server so it is at least run-able
  Related: #1057097

* Mon Mar 31 2014 Honza Horak <hhorak@redhat.com> - 2.4.9-6
- Require existing package
  Related: #1075688

* Tue Mar 25 2014 Jan Pacner <jpacner@redhat.com> - 2.4.9-5
- Resolves: #1075736 (initscript doesnt respect LSB)
- Resolves: #1057097 (Use the same name for daemon and log file)
- Resolves: #1075688 (metapackage shouldnt depend on another metapackage)
- Resolves: #1075025 (Leftovers files after mongodb packages removal)

* Mon Feb 17 2014 Honza Horak <hhorak@redhat.com> - 2.4.9-4
- Rebase due libunwind soname prefix
  Related: #1042874

* Mon Jan 20 2014 Jan Pacner <jpacner@redhat.com> - 2.4.9-3
- Related: #1055555 (add -scldevel subpackage for shipped build-requires garbage)
- fix installed dirs permissions

* Fri Jan 17 2014 Honza Horak <hhorak@redhat.com> - 2.4.9-2
- Rebuild for gperftools
  Related: #1039927

* Wed Jan 15 2014 Jan Pacner <jpacner@redhat.com> - 2.4.9
- Resolves: RHBZ#1051746 (update to mongodb-2.4.9)

* Mon Jan 13 2014 Honza Horák <hhorak@redhat.com> - 2.4.8-6
- Rebild for prefixed libsnappy
  Related: RHBZ#1049403

* Thu Dec 19 2013 Jan Pacner <jpacner@redhat.com> - 2.4.8-5
- Related: #1042874 (non-namespaced RPM provides and libraries)

* Tue Dec 17 2013 Jan Pacner <jpacner@redhat.com> - 2.4.8-4
- Resolves: #1039038 (additional forking of mongod)
- change log placement to be consistent with other SCLs

* Thu Nov 28 2013 Jan Pacner <jpacner@redhat.com> - 2.4.8-3
- removed scl-source; fixed pid file path

* Wed Nov 27 2013 Honza Horak <hhorak@redhat.com> - 2.4.8-2
- Run restore context as work-around for #924044
- remove scl-source (no more needed)

* Thu Nov 21 2013 Jan Pacner <jpacner@redhat.com> - 2.4.8-1
- new upstream release
- fix sed arguments
- patch cleanup (BSON patch not needed any more)
- rename lib subpackages to match the scl_prefix-libpkg_name pattern
- change v8 dependency to a shared one from external SCL
- use system pkg for snappy if present (i.e. on RHEL7)
- auto-generate list of scls in systemd unit file

* Mon Nov 18 2013 Jan Pacner <jpacner@redhat.com> - 2.4.6-3
- fix double --quiet option in init script; fix bad sed pattern
- fix libmongodb bad prefix
- fix scl-service installation
- log path mismatches fixed

* Fri Oct 25 2013 Jan Pacner <jpacner@redhat.com> - 2.4.6-2
- make sysconf options being respected
- fix sourceX files installation in % install

* Mon Oct 14 2013 Jan Pacner <jpacner@redhat.com> - 2.4.6-1
- Modified for SCL (software collection) mongodb24

* Wed Aug 21 2013 Troy Dawson <tdawson@redhat.com> - 2.4.6-1
- Updated to 2.4.6
- Added Requires: v8  (#971595)

* Sun Jul 28 2013 Petr Machata <pmachata@redhat.com> - 2.4.5-6
- Rebuild for boost 1.54.0

* Sat Jul 27 2013 pmachata@redhat.com - 2.4.5-5
- Rebuild for boost 1.54.0

* Fri Jul 12 2013 Troy Dawson <tdawson@redhat.com> - 2.4.5-4
- Added Provides: mongodb-devel to libmongodb-devel

* Fri Jul 12 2013 Troy Dawson <tdawson@redhat.com> - 2.4.5-3
- Removed hardening section.  Currently doesn't work with 2.4.x
  Wasn't really being applied when we thought it was.
- Cleaned up RHEL5 spec leftovers

* Thu Jul 11 2013 David Marlin <dmarlin@redhat.com> - 2.4.5-2
- Updated arm patches to work with 2.4.x

* Mon Jul 08 2013 Troy Dawson <tdawson@redhat.com> - 2.4.5-1
- Update to version 2.4.5 to fix CVE-2013-4650
- Patch3 fixed upstream - https://jira.mongodb.org/browse/SERVER-5575
- Patch4 fixed upstream - https://jira.mongodb.org/browse/SERVER-6514
- Put lib dir in correct place
- no longer have to remove duplicate headers

* Sun Jul 07 2013 Johan Hedin <johan.o.hedin@gmail.com> - 2.4.4-4
- Added patch to make mongodb compile with gcc 4.8

* Wed Jul 03 2013 Johan Hedin <johan.o.hedin@gmail.com> - 2.4.4-3
- Added missing daemon name to the preun script for the server
- Fixed init script so that it does not kill the server on shutdown
- Renamed mongodb-devel to libmongdb-devel
- Dependency cleanup between the sub packages
- Moved Requires for the server to the server sub package
- Using %%{_unitdir} macro for where to put systemd unit files
- Fixed rpmlint warnings regarding %% in comments and mixed tabs/spaces
- Run systemd-tmpfiles --create mongodb.conf in post server

* Mon Jul 01 2013 Troy Dawson <tdawson@redhat.com> - 2.4.4-2
- Turn on hardened build (#958014)
- Apply patch to accept env flags

* Sun Jun 30 2013 Johan Hedin <johan.o.hedin@gmail.com> - 2.4.4-1
- Bumped version up to 2.4.4
- Rebased the old 2.2 patches that are still needed to 2.4.4
- Added some new patches to build 2.4.4 properly

* Sat May 04 2013 David Marlin <dmarlin@redhat.com> - 2.2.4-2
- Updated patch to work on both ARMv5 and ARMv7 (#921226)

* Thu May 02 2013 Troy Dawson <tdawson@redhat.com> - 2.2.4-1
- Bumped version up to 2.2.4
- Refreshed all patches to 2.2.4

* Fri Apr 26 2013 David Marlin <dmarlin@redhat.com> - 2.2.3-5
- Patch to build on ARM (#921226)

* Wed Mar 27 2013 Troy Dawson <tdawson@redhat.com> - 2.2.3-4
- Fix for CVE-2013-1892

* Sun Feb 10 2013 Denis Arnaud <denis.arnaud_fedora@m4x.org> - 2.2.3-3
- Rebuild for Boost-1.53.0

* Sat Feb 09 2013 Denis Arnaud <denis.arnaud_fedora@m4x.org> - 2.2.3-2
- Rebuild for Boost-1.53.0

* Tue Feb 05 2013 Troy Dawson <tdawson@redhat.com> - 2.2.3-1
- Update to version 2.2.3

* Mon Jan 07 2013 Troy Dawson <tdawson@redhat.com> - 2.2.2-2
- remove duplicate headers (#886064)

* Wed Dec 05 2012 Troy Dawson <tdawson@redhat.com> - 2.2.2-1
- Updated to version 2.2.2

* Tue Nov 27 2012 Troy Dawson <tdawson@redhat.com> - 2.2.1-3
- Add ssl build option
- Using the reserved mongod UID for the useradd
- mongod man page in server package (#880351)
- added optional MONGODB_OPTIONS to init script

* Wed Oct 31 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.2.1-2
- Make sure build and install flags are the same
- Actually remove the js patch file

* Wed Oct 31 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.2.1-1
- Remove fork fix patch (fixed upstream)
- Remove pcre patch (fixed upstream)
- Remove mozjs patch (now using v8 upstream)
- Update to 2.2.1

* Tue Oct 02 2012 Troy Dawson <tdawson@redhat.com> - 2.2.0-6
- full flag patch to get 32 bit builds to work 

* Tue Oct 02 2012 Troy Dawson <tdawson@redhat.com> - 2.2.0-5
- shared libraries patch
- Fix up minor %%files issues

* Fri Sep 28 2012 Troy Dawson <tdawson@redhat.com> - 2.2.0-4
- Fix spec files problems

* Fri Sep 28 2012 Troy Dawson <tdawson@redhat.com> - 2.2.0-3
- Updated patch to use system libraries
- Update init script to use a pidfile

* Thu Sep 27 2012 Troy Dawson <tdawson@redhat.com> - 2.2.0-2
- Added patch to use system libraries

* Wed Sep 19 2012 Troy Dawson <tdawson@redhat.com> - 2.2.0-1
- Updated to 2.2.0
- Updated patches that were still needed
- use v8 instead of spider_monkey due to bundled library issues

* Tue Aug 21 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.7-1
- Update to 2.0.7
- Don't patch for boost-filesystem version 3 on EL6

* Mon Aug 13 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.6-3
- Remove EL5 support
- Add patch to use boost-filesystem version 3

* Wed Aug 01 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.6-2
- Don't apply fix-xtime patch on EL5

* Wed Aug 01 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.6-1
- Update to 2.0.6
- Update no-term patch
- Add fix-xtime patch for new boost

* Fri Jul 20 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Apr 17 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.4-1
- Update to 2.0.4
- Remove oldpython patch (fixed upstream)
- Remove snappy patch (fixed upstream)

* Tue Feb 28 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.2-10
- Rebuilt for c++ ABI breakage

* Fri Feb 10 2012 Petr Pisar <ppisar@redhat.com> - 2.0.2-9
- Rebuild against PCRE 8.30

* Fri Feb 03 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-8
- Disable HTTP interface by default (#752331)

* Fri Feb 03 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-7
- Enable journaling by default (#656112)
- Remove BuildRequires on unittest (#755081)

* Fri Feb 03 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-6
- Clean up mongodb-src-r2.0.2-js.patch and fix #787246

* Tue Jan 17 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-5
- Enable build using external snappy

* Tue Jan 17 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-4
- Patch buildsystem for building on older pythons (RHEL5)

* Mon Jan 16 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-3
- Merge the 2.0.2 spec file with EPEL
- Merge mongodb-sm-pkgconfig.patch into mongodb-src-r2.0.2-js.patch

* Mon Jan 16 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-2
- Add pkg-config enablement patch

* Sat Jan 14 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-1
- Update to 2.0.2
- Add new files (mongotop and bsondump manpage)
- Update mongodb-src-r1.8.2-js.patch => mongodb-src-r2.0.2-js.patch
- Update mongodb-fix-fork.patch
- Fix pcre linking

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.8.2-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Sun Nov 20 2011 Chris Lalancette <clalancette@gmail.com> - 1.8.2-10
- Rebuild for rawhide boost update

* Thu Sep 22 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-9
- Copy the right source file into place for tmpfiles.d

* Tue Sep 20 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-8
- Add a tmpfiles.d file to create the /var/run/mongodb subdirectory

* Mon Sep 12 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-7
- Add a patch to fix the forking to play nice with systemd
- Make the /var/run/mongodb directory owned by mongodb

* Thu Jul 28 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-6
- BZ 725601 - fix the javascript engine to not hang (thanks to Eduardo Habkost)

* Mon Jul 25 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-5
- Fixes to post server, preun server, and postun server to use systemd

* Thu Jul 21 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-4
- Update to use systemd init

* Thu Jul 21 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-3
- Rebuild for boost ABI break

* Wed Jul 13 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-2
- Make mongodb-devel require boost-devel (BZ 703184)

* Fri Jul 01 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-1
- Update to upstream 1.8.2
- Add patch to ignore TERM

* Fri Jul 01 2011 Chris Lalancette <clalance@redhat.com> - 1.8.0-3
- Bump release to build against new boost package

* Sat Mar 19 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.8.0-2
- Make mongod bind only to 127.0.0.1 by default

* Sat Mar 19 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.8.0-1
- Update to 1.8.0
- Remove upstreamed nonce patch

* Wed Feb 16 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.7.5-5
- Add nonce patch

* Sun Feb 13 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.7.5-4
- Manually define to use boost-fs v2

* Sat Feb 12 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.7.5-3
- Disable extra warnings

* Fri Feb 11 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.7.5-2
- Disable compilation errors on warnings

* Fri Feb 11 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.7.5-1
- Update to 1.7.5
- Remove CPPFLAGS override
- Added libmongodb package

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.6.4-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Mon Dec 06 2010 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.6.4-3
- Add post/postun ldconfig... oops!

* Mon Dec 06 2010 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.6.4-2
- Enable --sharedclient option, remove static lib

* Sat Dec 04 2010 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.6.4-1
- New upstream release

* Fri Oct 08 2010 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.6.3-4
- Put -fPIC onto both the build and install scons calls

* Fri Oct 08 2010 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.6.3-3
- Define _initddir when it doesn't exist for el5 and others

* Fri Oct 08 2010 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.6.3-2
- Added -fPIC build option which was dropped by accident

* Thu Oct  7 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.6.3-1
- removed js Requires
- new upstream release
- added more excludearches: sparc s390, s390x and bugzilla pointer

* Tue Sep  7 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.6.2-2
- added ExcludeArch for ppc

* Fri Sep  3 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.6.2-1
- new upstream release 1.6.2
- send mongod the USR1 signal when doing logrotate
- use config options when starting the daemon from the initfile
- removed dbpath patch: rely on config
- added pid directory to config file and created the dir in the spec
- made the init script use options from the config file
- changed logpath in mongodb.conf

* Wed Sep  1 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.6.1-1
- new upstream release 1.6.1
- patched SConstruct to allow setting cppflags
- stopped using sed and chmod macros

* Fri Aug  6 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.6.0-1
- new upstream release: 1.6.0
- added -server package
- added new license file to %%docs
- fix spurious permissions and EOF encodings on some files

* Tue Jun 15 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.4.3-2
- added explicit js requirement
- changed some names

* Wed May 26 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.4.3-1
- updated to 1.4.3
- added zlib license for util/md5
- deleted upstream deb/rpm recipes
- made scons not strip binaries
- made naming more consistent in logfile, lockfiles, init scripts etc.
- included manpages and added corresponding license
- added mongodb.conf to sources

* Fri Oct  2 2009 Ionuț Arțăriși <mapleoin@fedoraproject.org> - 1.0.0-3
- fixed libpath issue for 64bit systems

* Thu Oct  1 2009 Ionuț Arțăriși <mapleoin@fedoraproject.org> - 1.0.0-2
- added virtual -static package

* Mon Aug 31 2009 Ionuț Arțăriși <mapleoin@fedoraproject.org> - 1.0.0-1
- Initial release.
