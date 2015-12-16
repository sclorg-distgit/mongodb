#%global _hardened_build 1
# for better compatibility with SCL spec file
%{?scl:%scl_package mongodb}
%{!?scl:%global pkg_name %{name}}
# mongod daemon
%global daemon mongod
# mongos daemon
%global daemonshard mongos

# Regression tests may take a long time (many cores recommended), skip them by
# passing --nocheck to rpmbuild or by setting runselftest to 0 if defining
# --nocheck is not possible (e.g. in koji build)
%{!?runselftest:%global runselftest 1}

# Python SCL (to run scons with python2.7; test subpackage)
%global scl_python python27
%global scl_python_prefix %{scl_python}-

# Convert SCL name into uppercase including - to _ conversion
%if 0%{?scl:1}
%global scl_upper %{lua:print(string.upper(string.gsub(rpm.expand("%{scl}"), "-", "_")))}
%global _initddir %{_root_initddir}
%if %runselftest
%global buildscls %{scl} %{scl_python}
%else
%global buildscls %{scl}
%endif
%endif

Name:           %{?scl_prefix}mongodb
Version:        2.6.9
Release:        1%{?dist}
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
Source3:        %{daemon}.conf
Source4:        %{daemon}.init
Source5:        %{daemon}.service
Source6:        %{daemon}.sysconf
Source7:        %{daemonshard}.conf
Source8:        %{daemonshard}.init
Source9:        %{daemonshard}.service
Source10:       %{daemonshard}.sysconf
Source11:       README
Source12:       daemon-scl-helper.sh

# https://bugzilla.redhat.com/show_bug.cgi?id=958014
# need to work on getting this properly patched upstream
# -> same work is made in prep section
#Patch7:         mongodb-2.4.5-pass-flags.patch

# compile with GCC 4.8
# -> upstream solved it, by default -Wno-unused-local-typedefs is used
#Patch8:         mongodb-2.4.5-gcc48.patch

Requires:       %{?scl_prefix_v8}v8 >= 3.14.5.10
%ifarch %{arm}
BuildRequires:  gcc >= 4.7
%endif
BuildRequires:  pcre-devel
%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
BuildRequires:  boost-devel >= 1.44
%else
BuildRequires:  %{?scl_prefix}boost-devel >= 1.44
%endif
# Provides tcmalloc
BuildRequires:  %{?scl_prefix}gperftools-devel
BuildRequires:  snappy-devel
BuildRequires:  %{?scl_prefix_v8}v8-devel
BuildRequires:  %{?scl_prefix}yaml-cpp-devel
BuildRequires:  %{?scl_prefix}scons
BuildRequires:  openssl-devel
BuildRequires:  libpcap-devel
BuildRequires:  %{?scl_prefix}libstemmer-devel
%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
BuildRequires:  systemd
%endif
%if %runselftest
%ifarch %{ix86} x86_64
BuildRequires:  %{?scl_python_prefix}python-pymongo
%endif
%endif

%{?scl:Requires:%scl_runtime}

# Mongodb must run on a little-endian CPU (see bug #630898)
ExcludeArch:    ppc ppc64 %{sparc} s390 s390x

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


%package server
Summary:        MongoDB server, sharding server and support scripts
Group:          Applications/Databases
Requires(pre):  shadow-utils
Requires:       %{?scl_prefix_v8}v8
%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units
%else
Requires(post): chkconfig
Requires(preun): chkconfig
Requires(postun): initscripts
%endif

%{?scl:Requires:%scl_runtime}

%description server
This package provides the mongo server software, mongo sharding server
software, default configuration files, and init scripts.


%ifarch %{ix86} x86_64
%package test
Summary:          MongoDB test suite
Group:            Applications/Databases
Requires:         %{name}%{?_isa} = %{version}-%{release}
Requires:         %{name}-server%{?_isa} = %{version}-%{release}
Requires:         %{?scl_python_prefix}python-pymongo

%{?scl:Requires:%scl_runtime}

%description test
This package contains the regression test suite distributed with
the MongoDB sources.
%endif

%prep
%setup -q -n mongodb-src-r%{version}

# Fixed in upstream - version 2.7.3
sed -i -r "s|(conf.FindSysLibDep\(\"yaml\", \[\"yaml)(\"\]\))|\1-cpp\2|" SConstruct

# Use optflags and __global_ldflags, disable -fPIC
#(opt=$(echo "%{?optflags}" | sed -r -e 's| |","|g' )
#sed -i -r -e "s|(CCFLAGS=\[)\"-fPIC\"|\1\"$opt\"|" SConstruct)
#(opt=$(echo "%{?__global_ldflags}" | sed -r -e 's| |","|g' )
#sed -i -r -e "s|(LINKFLAGS=\[)\"-fPIC\"|\1\"$opt\"|" SConstruct)

# CRLF -> LF
sed -i 's/\r//' README

# disable propagation of $TERM env var into the Scons build system
sed -i -r "s|(for key in \('HOME'), 'TERM'(\):)|\1\2|" SConstruct

# disable run test and perftest programs
sed -i -r "s|^([[:space:]]*)(if suite == 'test':)|\1\2\n\1    continue|"      buildscripts/smoke.py
sed -i -r "s|^([[:space:]]*)(elif suite == 'perf':)|\1\2\n\1    continue|"    buildscripts/smoke.py

# by default use system mongod, mongos and mongo binaries
sed -i -r "s|(default=os.path.join\()mongo_repo(, 'mongod'\))|\1'%{_bindir}'\2|"   buildscripts/smoke.py
sed -i -r "s|(default=os.path.join\()mongo_repo(, 'mongo'\))|\1'%{_bindir}'\2|"    buildscripts/smoke.py
sed -i -r "s|(os.path.join\()mongo_repo(, program)|\1'%{_bindir}'\2|"              buildscripts/smoke.py

# set default data prefix
sed -i -r "s|(smoke_db_prefix = ')'|\1var'|"                           buildscripts/smoke.py
sed -i -r "s|^([[:space:]]*)(set_globals\(options, tests\))$|\1\2\n\1global failfile\n\1\
failfile = os.path.join\(os.path.join\(mongo_repo, smoke_db_prefix\), 'failfile.smoke'\)|"    buildscripts/smoke.py

# copy them (we will change their content)
cp %{SOURCE1} %{SOURCE2} %{SOURCE3} %{SOURCE4} %{SOURCE5} \
  %{SOURCE6} %{SOURCE7} %{SOURCE8} %{SOURCE9} %{SOURCE10} %{SOURCE11} ./

for f in %{SOURCE4} %{SOURCE8}; do
  sed -i -r -e "s|/usr/bin|%{_bindir}|g" \
    -e "s|/var(/run/mongodb)|%{_localstatedir}\1|g" \
    -e "s|/var(/log/mongodb)|%{_localstatedir}\1|g" \
    -e "s|/etc(/mongo[ds]\.conf)|%{_sysconfdir}\1|g" \
    -e "s|/etc(/sysconfig)|%{_sysconfdir}\1|g" \
    -e "s|/var(/lock)|%{_localstatedir}\1|g" \
    -e "s|__SCL_SCRIPTS__|%{?_scl_scripts}|g" \
    -e "s|__list of scls__|\$%{scl_upper}_SCLS_ENABLED|g" \
      "$(basename "$f")"
done

sed -i -r -e "s|/var(/log/mongodb)|%{_localstatedir}\1|g" \
  -e "s|/var(/run/mongodb)|%{_localstatedir}\1|g" \
  "$(basename %{SOURCE2})"

for f in %{SOURCE3} %{SOURCE7}; do
  sed -i -r -e "s|/var/lib(/mongodb)|%{_sharedstatedir}\1|g" \
    -e "s|/var(/run/mongodb)|%{_localstatedir}\1|g" \
    -e "s|/var(/log/mongodb)|%{_localstatedir}\1|g" \
    "$(basename "$f")"
done

for f in %{SOURCE6} %{SOURCE10}; do
  sed -i -r -e "s|/etc(/mongo[ds]\.conf)|%{_sysconfdir}\1|g" \
    "$(basename "$f")"
done

sed -i -r -e "s|(/run/mongodb)|%{_localstatedir}\1|g" \
  "$(basename %{SOURCE1})"

for f in %{SOURCE5} %{SOURCE9}; do
  #FIXME check if the _SCLS_ENABLED var isn't empty!
  sed -i -r -e "s|/var(/run/mongodb)|%{_localstatedir}\1|g" \
    -e "s|/etc(/sysconfig)|%{_sysconfdir}\1|g" \
    -e "s|/usr/bin(/mongo[ds])|%{_bindir}\1|g" \
    -e "s|__SCL_SCRIPTS__|%{?_scl_scripts}|g" \
    -e "s|__list of scls__|\$%{scl_upper}_SCLS_ENABLED|g" \
    -e "s|@libexecdir@|%{_libexecdir}|" \
      "$(basename "$f")"
done

sed -i -r -e "s|(/usr/share)|%{_datarootdir}|g" \
  "$(basename %{SOURCE11})"


%build
# see add_option() calls in SConstruct for options
%{?scl:scl enable %{buildscls} - << "EOF"}
scons all \
        %{?_smp_mflags} \
        --use-system-all  \
        --usev8 \
        --nostrip \
        --ssl \
        --propagate-shell-environment

%{?scl:EOF}


%install
# NOTE: If install flags are not EXACTLY the same as in %%build,
#   mongodb will be built twice!
%{?scl:scl enable %{buildscls} - << "EOF"}
scons install \
        %{?_smp_mflags} \
        --use-system-all \
        --usev8 \
        --nostrip \
        --ssl \
        --propagate-shell-environment \
        --prefix=%{buildroot}%{_prefix}

%{?scl:EOF}

mkdir -p %{buildroot}%{_sharedstatedir}/%{pkg_name}
mkdir -p %{buildroot}%{_localstatedir}/log/%{pkg_name}
mkdir -p %{buildroot}%{_localstatedir}/run/%{pkg_name}
mkdir -p %{buildroot}%{_sysconfdir}/sysconfig

%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
install -p -D -m 644 "$(basename %{SOURCE1})"  %{buildroot}%{_tmpfilesdir}/%{?scl_prefix}%{pkg_name}.conf
install -p -D -m 644 "$(basename %{SOURCE5})"  %{buildroot}%{_unitdir}/%{?scl_prefix}%{daemon}.service
install -p -D -m 644 "$(basename %{SOURCE9})"  %{buildroot}%{_unitdir}/%{?scl_prefix}%{daemonshard}.service

mkdir -p %{buildroot}%{_libexecdir}
install -p -m 755     %{SOURCE12}              %{buildroot}%{_libexecdir}/mongodb-scl-helper
%else
install -p -D -m 755 "$(basename %{SOURCE4})"  %{buildroot}%{_initddir}/%{?scl_prefix}%{daemon}
install -p -D -m 755 "$(basename %{SOURCE8})"  %{buildroot}%{_initddir}/%{?scl_prefix}%{daemonshard}
%endif
install -p -D -m 644 "$(basename %{SOURCE2})"  %{buildroot}%{?scl:%_root_sysconfdir}%{!?scl:%_sysconfdir}/logrotate.d/%{?scl_prefix}%{pkg_name}
install -p -D -m 644 "$(basename %{SOURCE3})"  %{buildroot}%{_sysconfdir}/%{daemon}.conf
install -p -D -m 644 "$(basename %{SOURCE7})"  %{buildroot}%{_sysconfdir}/%{daemonshard}.conf
install -p -D -m 644 "$(basename %{SOURCE6})"  %{buildroot}%{_sysconfdir}/sysconfig/%{daemon}
install -p -D -m 644 "$(basename %{SOURCE10})" %{buildroot}%{_sysconfdir}/sysconfig/%{daemonshard}

install -d -m 755            %{buildroot}%{_mandir}/man1
install -p -m 644 debian/*.1 %{buildroot}%{_mandir}/man1/

%ifarch %{ix86} x86_64
mkdir -p %{buildroot}%{_datadir}/%{pkg_name}-test
mkdir -p %{buildroot}%{_datadir}/%{pkg_name}-test/var
install -p -D -m 555    buildscripts/smoke.py   %{buildroot}%{_datadir}/%{pkg_name}-test/
install -p -D -m 444    buildscripts/cleanbb.py %{buildroot}%{_datadir}/%{pkg_name}-test/
install -p -D -m 444    buildscripts/utils.py   %{buildroot}%{_datadir}/%{pkg_name}-test/

cp -R                   jstests                 %{buildroot}%{_datadir}/%{pkg_name}-test/

install -p -D -m 444    "$(basename %{SOURCE11})"           %{buildroot}%{_datadir}/%{pkg_name}-test/


%check
# More info about testing:
# http://www.mongodb.org/about/contributors/tutorial/test-the-mongodb-server/
# Run new-style unit tests (*_test files)
%if %runselftest
%{?scl:scl enable %{buildscls} - << "EOF"}
cd %{_builddir}/%{pkg_name}-src-r%{version}
while read unittest
do
    ./$unittest
    if [ $? -ne 0 ]
    then
        exit 1
    fi
done < ./build/unittests.txt

# Run JavaScript integration tests
mkdir ./var
buildscripts/smoke.py --smoke-db-prefix ./var --continue-on-failure --mongo=%{buildroot}%{_bindir}/mongo --mongod=%{buildroot}%{_bindir}/%{daemon} --nopreallocj jsCore
rm -Rf ./var
%{?scl:EOF}
%endif
%endif

%post -p /sbin/ldconfig


%postun -p /sbin/ldconfig


%pre server
getent group  %{pkg_name} >/dev/null || groupadd -r %{pkg_name}
# TODO _sharedstatedir
getent passwd %{pkg_name} >/dev/null || useradd -r -g %{pkg_name} -u 184 \
  -d /var/lib/%{pkg_name} -s /sbin/nologin \
  -c "MongoDB Database Server" %{pkg_name}
exit 0


%post server
%if 0%{?scl:1}
# handle SELinux context for files outside of normal location
%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
semanage fcontext -a -e %{_unitdir}/%{daemon}.service %{_unitdir}/%{?scl_prefix}%{daemon}.service >/dev/null 2>&1 || :
semanage fcontext -a -e %{_unitdir}/%{daemonshard}.service %{_unitdir}/%{?scl_prefix}%{daemonshard}.service >/dev/null 2>&1 || :
selinuxenabled && load_policy || :
restorecon %{_unitdir}/%{?scl_prefix}* >/dev/null 2>&1 || :
%else
semanage fcontext -a -e %{_initddir}/%{daemon} %{_initddir}/%{?scl_prefix}%{daemon} >/dev/null 2>&1 || :
semanage fcontext -a -e %{_initddir}/%{daemon} %{_initddir}/%{?scl_prefix}%{daemonshard} >/dev/null 2>&1 || :
selinuxenabled && load_policy || :
restorecon %{_initddir}/%{?scl_prefix}* >/dev/null 2>&1 || :
%endif
restorecon -r %{?_scl_root}/ >/dev/null 2>&1 || :
restorecon -R %{_sharedstatedir}/%{pkg_name}
restorecon -R %{_localstatedir}/log/%{pkg_name}
restorecon -R %{_localstatedir}/run/%{pkg_name}
%endif

%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
  # https://fedoraproject.org/wiki/Packaging:ScriptletSnippets#Systemd
  # daemon-reload
  %systemd_postun
%else
  /sbin/chkconfig --add %{?scl_prefix}%{daemon}
  /sbin/chkconfig --add %{?scl_prefix}%{daemonshard}
%endif


%preun server
if [ "$1" = 0 ]; then
%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
  # --no-reload disable; stop
  %systemd_preun %{?scl_prefix}%{daemon}.service
  %systemd_preun %{?scl_prefix}%{daemonshard}.service
%else
  /sbin/service %{?scl_prefix}%{daemon}       stop >/dev/null 2>&1
  /sbin/service %{?scl_prefix}%{daemonshard}  stop >/dev/null 2>&1
  /sbin/chkconfig --del %{?scl_prefix}%{daemon}
  /sbin/chkconfig --del %{?scl_prefix}%{daemonshard}
%endif
fi


%postun server
%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
  # daemon-reload
  %systemd_postun
%endif
if [ "$1" -ge 1 ] ; then
%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
  # try-restart
  %systemd_postun_with_restart %{?scl_prefix}%{daemon}.service
  %systemd_postun_with_restart %{?scl_prefix}%{daemonshard}.service
%else
  /sbin/service %{?scl_prefix}%{daemon}       condrestart >/dev/null 2>&1 || :
  /sbin/service %{?scl_prefix}%{daemonshard}  condrestart >/dev/null 2>&1 || :
%endif
fi


%files
%{!?_licensedir:%global license %%doc}
%license GNU-AGPL-3.0.txt APACHE-2.0.txt
%doc README
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


%files server
%{_bindir}/mongod
%{_bindir}/mongos
%{_mandir}/man1/mongod.1*
%{_mandir}/man1/mongos.1*

%dir %attr(0750, %{pkg_name}, root) %{_sharedstatedir}/%{pkg_name}
%dir %attr(0750, %{pkg_name}, root) %{_localstatedir}/log/%{pkg_name}
%dir %attr(0750, %{pkg_name}, root) %{_localstatedir}/run/%{pkg_name}
%config(noreplace) %{?scl:%_root_sysconfdir}%{!?scl:%_sysconfdir}/logrotate.d/%{?scl_prefix}%{pkg_name}
%config(noreplace) %{_sysconfdir}/%{daemon}.conf
%config(noreplace) %{_sysconfdir}/%{daemonshard}.conf
%config(noreplace) %{_sysconfdir}/sysconfig/%{daemon}
%config(noreplace) %{_sysconfdir}/sysconfig/%{daemonshard}
%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
%{_tmpfilesdir}/%{?scl_prefix}%{pkg_name}.conf
%{_unitdir}/*.service
%{_libexecdir}/mongodb-scl-helper
%else
%{_initddir}/%{?scl_prefix}%{daemon}
%{_initddir}/%{?scl_prefix}%{daemonshard}
%endif


%ifarch %{ix86} x86_64
%files test
%doc %{_datadir}/%{pkg_name}-test/README
%dir %attr(0755, %{pkg_name}, root) %{_datadir}/%{pkg_name}-test
%dir %attr(0755, %{pkg_name}, root) %{_datadir}/%{pkg_name}-test/var
%dir %attr(0755, %{pkg_name}, root) %{_datadir}/%{pkg_name}-test/jstests
%{_datadir}/%{pkg_name}-test/smoke.*
%{_datadir}/%{pkg_name}-test/cleanbb.*
%{_datadir}/%{pkg_name}-test/utils.*
%{_datadir}/%{pkg_name}-test/jstests/*
%endif

%changelog
* Wed May 13 2015 Marek Skalicky <mskalick@redhat.com> 2.6.9-1
- Correct SELinux type for slc-helper script 
  Resolves: #1202013
- Fix mongodb user HOME (Resolves: #1206157)
- Upgrade to latest minor release 2.6.9 (Resolves: #1207118)

* Thu Mar 19 2015 Marek Skalicky <mskalick@redhat.com> 2.6.8-4
- Use mongod_initrc_exex_t SELinux type for slc-helper script

* Thu Mar 19 2015 Marek Skalicky <mskalick@redhat.com> 2.6.8-3
- Fixed SELinux context
- Renamed scl-helper script

* Thu Mar 19 2015 Marek Skalicky <mskalick@redhat.com> 2.6.8-2
- Resolves: #1202013 (Daemon run with proper SELinux context)

* Mon Mar 2 2015 Marek Skalicky <mskalick@redhat.com> 2.6.8-1
- Upgrade to version 2.6.8
- Resolves: #1194412 (MongoDB Security & Defaults)

* Fri Feb 27 2015 Honza Horak <hhorak@redhat.com> - 2.6.7-9
- Remove NFS register feature for questionable usage for DBs
- Allow to skip tests during build
- Simplify few SCL macros

* Thu Feb 26 2015 Marek Skalicky <mskalick@redhat.com> 2.6.7-8
- Resolves: #1075736 (initscript doesn't respect LSB)

* Tue Jan 27 2015 Honza Horak <hhorak@redhat.com> - 2.6.7-7
- Use 0755 on var directory for tests, mark README as doc

* Tue Jan 27 2015 Honza Horak <hhorak@redhat.com> - 2.6.7-6
- Run selinux magic in post, not preun
- Create lock file directory

* Tue Jan 27 2015 Honza Horak <hhorak@redhat.com> - 2.6.7-5
- Add removed $ by mistake
- Create dir for config files and data in scl register

* Tue Jan 27 2015 Honza Horak <hhorak@redhat.com> - 2.6.7-4
- Implement scl register support

* Mon Jan 26 2015 Honza Horak <hhorak@redhat.com> - 2.6.7-3
- Convert - to _ when translating to uppercase scl name
- Do not use & in the init script if daemon call is used

* Fri Jan 23 2015 Marek Skalicky <mskalick@redhat.com> 2.6.7-2
- Changed name of conf and log files
- Added service-environment into mongodb package
- Changed location of log files

* Mon Jan 19 2015 Marek Skalicky <mskalick@redhat.com> 2.6.7-1
- Merged changes from Fedora Rawhide

* Tue Nov 18 2014 Marek Skalicky <mskalick@redhat.com> 2.6.5-5
- Changed and cleaned up requirements

* Fri Nov 14 2014 Marek Skalicky <mskalick@redhat.com> 2.6.5-4
- Changed v8 dependency to SCL v8314
- Added MONGODB_OPTIONS options variable into *.init files

* Fri Nov 7 2014 Marek Skalicky <mskalick@redhat.com> 2.6.5-3
- Ported to SCL

* Thu Oct 9 2014 Marek Skalicky <mskalick@redhat.com> 2.6.5-2
- Corrected/Finished renaming services and pid files
- Changed default mongos ports

* Thu Oct 9 2014 Marek Skalicky <mskalick@redhat.com> 2.6.5-1
- Updated to version 2.6.5
- Renamed sysmted service files (to reflect mainstream names)

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.6.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Wed Jul  9 2014 Jan Pacner <jpacner@redhat.com> - 2.6.3-1
- Resolves: #1103163 new major release with major differences
- add sharding server daemon init/unit files (and rename existing)
- use ld library path from env
- spec cleanup/clarification
- Resolves: #1047858 (RFE: Turn on PrivateTmp and relocate unix socket file)
- Related: #963824 (bloated binaries; splitting according to latest upstream)

* Sat Jun  7 2014 Peter Robinson <pbrobinson@fedoraproject.org> 2.4.9-7
- aarch64 now has gperftools

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.4.9-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Fri May 23 2014 Petr Machata <pmachata@redhat.com> - 2.4.9-5
- Rebuild for boost 1.55.0

* Fri May 23 2014 David Tardon <dtardon@redhat.com> - 2.4.9-4
- rebuild for boost 1.55.0


* Fri Feb 14 2014 T.C. Hollingsworth <tchollingsworth@gmail.com> - 2.4.9-3
- rebuild for icu-53 (via v8)

* Tue Feb 04 2014 Matthias Saou <matthias@saou.eu> 2.4.9-2
- Merge el6 branch changes (we shouldn't start diverging now).
- Re-introduce conditionals, but to still support EL6.
- Include run directory only for EL6.
- Don't own the /usr/include directory.
- Make libmongodb requirement arch specific (#1010535).
- Fix multiple_occurrences error from duplicate --quiet options (#1022476).
- Fix broken v8 version specific requirement (#1027157).

* Sun Jan 19 2014 Peter Robinson <pbrobinson@fedoraproject.org> 2.4.9-1
- Update to 2.4.9
- Drop old < F-15 conditionals
- Cleanup Spec
- Run ldconfig for the lib package, not binary package
- Don't make some directories world readable (RHBZ 857926)

* Mon Jan 06 2014 Jan Pacner <jpacner@redhat.com> - 2.4.6-3
- Resolves: #1027157 (mongo shell sefgaults when using arbitrary v8 version)

* Thu Nov 28 2013 Jan Pacner <jpacner@redhat.com> - 2.4.8-1
- new release
- Resolves: #1010712 (LimitNOFILE)
- make sysconf options being respected

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
