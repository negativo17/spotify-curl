# Running tests requires ~20 minutes
%global with_tests 0

#global __provides_exclude ^(lib.*\\.so.*)$

Name:       spotify-curl
Version:    7.58.0
Release:    1%{?dist}
Summary:    A utility for getting files from remote servers (FTP, HTTP, and others)
License:    MIT
URL:        https://curl.haxx.se

Source:     https://curl.haxx.se/download/curl-%{version}.tar.xz

Patch1:     04_workaround_as_needed_bug.patch
Patch2:     06_always-disable-valgrind.patch
Patch3:     07_do-not-disable-debug-symbols.patch
Patch4:     08_enable-zsh.patch
Patch5:     11_omit-directories-from-config.patch
Patch6:     CVE-2018-1000120.patch
Patch7:     CVE-2018-1000121.patch
Patch8:     CVE-2018-1000122.patch
Patch9:     90_gnutls.patch

BuildRequires:  automake
BuildRequires:  groff
BuildRequires:  krb5-devel
BuildRequires:  libidn2-devel
BuildRequires:  libmetalink-devel
BuildRequires:  libnghttp2-devel
BuildRequires:  libpsl-devel
BuildRequires:  libssh2-devel
BuildRequires:  libtool
BuildRequires:  multilib-rpm-config
BuildRequires:  openldap-devel
BuildRequires:  openssh-clients
BuildRequires:  openssh-server
BuildRequires:  pkgconfig(gnutls)
BuildRequires:  python
BuildRequires:  stunnel
BuildRequires:  zlib-devel

# nghttpx (an HTTP/2 proxy) is used by the upstream test-suite
BuildRequires:  nghttp2

# perl modules used in the test suite
BuildRequires:  perl(Cwd)
BuildRequires:  perl(Digest::MD5)
BuildRequires:  perl(Exporter)
BuildRequires:  perl(File::Basename)
BuildRequires:  perl(File::Copy)
BuildRequires:  perl(File::Spec)
BuildRequires:  perl(IPC::Open2)
BuildRequires:  perl(MIME::Base64)
BuildRequires:  perl(strict)
BuildRequires:  perl(Time::Local)
BuildRequires:  perl(Time::HiRes)
BuildRequires:  perl(warnings)
BuildRequires:  perl(vars)

# The test-suite runs automatically trough valgrind if valgrind is available
# on the system. By not installing valgrind into mock's chroot, we disable
# this feature for production builds on architectures where valgrind is known
# to be less reliable, in order to avoid unnecessary build failures (see RHBZ
# #810992, #816175, and #886891).  Nevertheless developers are free to install
# valgrind manually to improve test coverage on any architecture.
%ifarch x86_64
BuildRequires: valgrind
%endif

# require at least the version of libssh2 that we were built against,
# to ensure that we have the necessary symbols available (#525002, #642796)
%global libssh2_version %(pkg-config --modversion libssh2 2>/dev/null || echo 0)

%description
This package is meant for compatibility purposes with Spotify which requires old
versions of specific libraries in a non-standard path.

%prep
%autosetup -p1 -n curl-%{version}

# disable test 1112 (#565305) and test 1801
# <https://github.com/bagder/curl/commit/21e82bd6#commitcomment-12226582>
# and test 2033, which is a flaky test for HTTP/1 pipelining
printf "1112\n1801\n2033\n" >> tests/data/DISABLED

# disable test 1319 on ppc64 (server times out)
%ifarch ppc64
echo "1319" >> tests/data/DISABLED
%endif

# temporarily disable failing libidn2 test-cases
printf "1034\n1035\n2046\n2047\n" >> tests/data/DISABLED

%build
[ -x /usr/kerberos/bin/krb5-config ] && KRB5_PREFIX="=/usr/kerberos"
autoreconf -vif
%configure \
    --disable-static \
    --enable-symbol-hiding \
    --enable-ipv6 \
    --enable-ldaps \
    --enable-manual \
    --enable-threaded-resolver \
    --enable-versioned-symbols \
    --with-gnutls \
    --with-gssapi${KRB5_PREFIX} \
    --with-libidn2 \
    --with-libmetalink \
    --with-libpsl \
    --with-libssh2 \
    --with-nghttp2 \
    --without-ssl \
    --without-nss \
    --without-ca-bundle

make %{?_smp_mflags} V=1

%if %with_tests

%check
# we have to override LD_LIBRARY_PATH because we eliminated rpath
LD_LIBRARY_PATH="$RPM_BUILD_ROOT%{_libdir}:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH

# compile upstream test-cases
cd tests
make %{?_smp_mflags} V=1

# run the upstream test-suite
./runtests.pl -a -p -v '!flaky'

%endif

%install
%make_install
rm -fr \
    %{buildroot}%{_includedir} \
    %{buildroot}%{_bindir} \
    %{buildroot}%{_datadir} \
    %{buildroot}%{_libdir}/pkgconfig \
    %{buildroot}%{_libdir}/*.la \
    %{buildroot}%{_libdir}/*.so

mkdir %{buildroot}%{_libdir}/spotify-client/
mv %{buildroot}%{_libdir}/*.so.* %{buildroot}%{_libdir}/spotify-client/

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%license COPYING
%{_libdir}/spotify-client/*.so.*

%changelog
* Mon Apr 23 2018 Simone Caronni <negativo17@gmail.com> - 7.58.0-1
- Update to 7.58.0.
- Use Ubuntu patches, provide specific GNUTLS build.

* Sat Jan 06 2018 Simone Caronni <negativo17@gmail.com> - 7.53.1-2
- Do not provide libcurl.so.4.

* Tue Oct 10 2017 Simone Caronni <negativo17@gmail.com> - 7.53.1-1
- First build based off Fedora package.

