%global __provides_exclude ^(lib.*\\.so.*)$

Name:       spotify-curl
Version:    7.76.0
Release:    1%{?dist}
Summary:    Spotify compatibility package - Curl
License:    MIT
URL:        https://curl.haxx.se

Source:     https://curl.haxx.se/download/curl-%{version}.tar.xz

Patch0:     curl-7.71.1-gnutls.patch
Patch1:     curl-7.36.0-debug.patch

BuildRequires:  automake
BuildRequires:  groff
BuildRequires:  libidn2-devel
BuildRequires:  libmetalink-devel
BuildRequires:  libnghttp2-devel
BuildRequires:  libpsl-devel
BuildRequires:  libssh2-devel
BuildRequires:  libtool
BuildRequires:  pkgconfig(gnutls)
BuildRequires:  python3
BuildRequires:  zlib-devel

Requires:       spotify-client%{?_isa}

%description
This package is meant for compatibility purposes with Spotify which requires old
versions of specific libraries in a non-standard path.

%prep
%autosetup -p1 -n curl-%{version}

%build
autoreconf -vif
%configure \
    --disable-static \
    --enable-symbol-hiding \
    --enable-ipv6 \
    --enable-threaded-resolver \
    --enable-versioned-symbols \
    --with-ca-bundle="/etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt" \
    --with-gnutls \
    --with-libidn2 \
    --with-libmetalink \
    --with-libpsl \
    --with-libssh2 \
    --with-nghttp2 \
    --without-ssl \
    --without-nss

%make_build

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

%files
%license COPYING
%{_libdir}/spotify-client/libcurl-gnutls.so.*

%changelog
* Fri Apr 09 2021 Simone Caronni <negativo17@gmail.com> - 7.76.0-1
- Update to 7.76.0.

* Sat Jul 11 2020 Simone Caronni <negativo17@gmail.com> - 7.71.1-1
- Update to 7.71.1.
- Simplify SPEC file massively.
- Remove tests.

* Mon Apr 23 2018 Simone Caronni <negativo17@gmail.com> - 7.58.0-1
- Update to 7.58.0.
- Use Ubuntu patches, provide specific GNUTLS build.

* Sat Jan 06 2018 Simone Caronni <negativo17@gmail.com> - 7.53.1-2
- Do not provide libcurl.so.4.

* Tue Oct 10 2017 Simone Caronni <negativo17@gmail.com> - 7.53.1-1
- First build based off Fedora package.

