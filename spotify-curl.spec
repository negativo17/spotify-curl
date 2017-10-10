# Running tests requires ~20 minutes
%global with_tests 0

Name:       spotify-curl
Version:    7.53.1
Release:    1%{?dist}
Summary:    A utility for getting files from remote servers (FTP, HTTP, and others)
License:    MIT

Source:     https://curl.haxx.se/download/curl-%{version}.tar.lzma

# fix out of bounds read in curl --write-out (CVE-2017-7407)
Patch1:     0001-curl-7.53.1-CVE-2017-7407.patch
# fix switching off SSL session id when client cert is used (CVE-2017-7468)
Patch2:     0002-curl-7.53.1-CVE-2017-7468.patch
# nss: do not leak PKCS #11 slot while loading a key (#1444860)
Patch3:     0003-curl-7.53.1-nss-pem-slot-leak.patch
# nss: use libnssckbi.so as the default source of trust
Patch4:     0004-curl-7.53.1-libnssckbi.patch
# fix out of bounds read in FTP PWD response parser (CVE-2017-1000254)
Patch5:     0005-curl-7.53.1-CVE-2017-1000254.patch
# nss: fix a possible use-after-free in SelectClientCert() (#1436158)
Patch7:     0007-curl-7.54.1-nss-cc-use-after-free.patch
# ignore Content-Length/Transfer-Encoding headers in CONNECT response (#1476427)
Patch8:     0008-curl-7.53.1-connect-response-headers.patch
# do not continue parsing of glob after range overflow (CVE-2017-1000101)
Patch9:     0009-curl-7.54.1-CVE-2017-1000101.patch
# tftp: reject file name lengths that do not fit buffer (CVE-2017-1000100)
Patch10:    0010-curl-7.54.1-CVE-2017-1000100.patch
# patch making libcurl multilib ready
Patch101:   0101-curl-7.32.0-multilib.patch
# prevent configure script from discarding -g in CFLAGS (#496778)
Patch102:   0102-curl-7.36.0-debug.patch
# use localhost6 instead of ip6-localhost in the curl test-suite
Patch104:   0104-curl-7.19.7-localhost6.patch

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
BuildRequires:  nss-devel
BuildRequires:  openldap-devel
BuildRequires:  openssh-clients
BuildRequires:  openssh-server
BuildRequires:  pkgconfig
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
    --with-gssapi${KRB5_PREFIX} \
    --with-libidn2 \
    --with-libmetalink \
    --with-libpsl \
    --with-libssh2 \
    --with-nghttp2 \
    --without-ssl \
    --with-nss \
    --without-ca-bundle

# Remove bogus rpath
#sed -i \
#    -e 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' \
#    -e 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool

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
* Tue Oct 10 2017 Simone Caronni <negativo17@gmail.com> - 7.53.1-1
- First build based off Fedora package.

