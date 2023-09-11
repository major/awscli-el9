%global pkgname aws-cli

%global bundled_flit_core_version 3.8.0
%global bundled_prompt_toolkit_version 3.0.38

%define vendor_path %{buildroot}%{python3_sitelib}/awscli/_vendor
%define vendor_pip %{__python3} -m pip install --quiet --no-deps -v --no-build-isolation --no-binary :all: -t %{vendor_path}

Name:               awscli2
Version:            2.13.17
Release:            1%{?dist}

Summary:            Universal Command Line Environment for AWS, version 2
# all files are licensed under Apache-2.0, except:
# - awscli/topictags.py is MIT
# - awscli/botocore/vendored/six.py is MIT
License:            Apache-2.0 AND MIT
URL:                https://github.com/aws/aws-cli/tree/v2
Source0:            https://github.com/aws/aws-cli/archive/%{version}/%{pkgname}-%{version}.tar.gz

Source10:            %{pypi_source flit_core %{bundled_flit_core_version}}
Source11:            %{pypi_source prompt_toolkit %{bundled_prompt_toolkit_version}}

BuildArch:          noarch

BuildRequires:      pyproject-rpm-macros
BuildRequires:      python3-devel
BuildRequires:      python3-pip
BuildRequires:      python3-wheel
BuildRequires:      python-unversioned-command
BuildRequires:      procps-ng

BuildRequires:      python3dist(cryptography)
BuildRequires:      python3dist(docutils)
BuildRequires:      python3dist(distro)
BuildRequires:      python3dist(jmespath)
BuildRequires:      python3dist(jsonschema)
BuildRequires:      python3dist(packaging)
BuildRequires:      python3dist(python-dateutil)
BuildRequires:      python3dist(ruamel-yaml)
BuildRequires:      python3dist(tomli)
BuildRequires:      python3dist(urllib3)
BuildRequires:      python3dist(wcwidth)

BuildRequires:      python3dist(pytest)

# Bundling potential
BuildRequires:      python3dist(awscrt)
BuildRequires:      python3dist(colorama)
BuildRequires:      python3dist(prompt-toolkit)

Recommends:         groff

Provides:           bundled(python3dist(flit_core)) = %{bundled_flit_core_version}
Provides:           bundled(python3dist(prompt_toolkit)) = %{bundled_prompt_toolkit_version}


# python-awscrt does not build on s390x
ExcludeArch:        s390x


%description
This package provides version 2 of the unified command line
interface to Amazon Web Services.


%prep
%setup -q -b10 -b11 -n %{pkgname}-%{version}

# fix permissions
find awscli/examples/ -type f -name '*.rst' -executable -exec chmod -x '{}' +


# use unittest.mock
find -type f -name '*.py' -exec sed \
    -e 's/^\( *\)import mock$/\1from unittest import mock/' \
    -e 's/^\( *\)from mock import mock/\1from unittest import mock/' \
    -e 's/^\( *\)from mock import/\1from unittest.mock import/' \
    -i '{}' +


%build
%python3 -m pip install --quiet --no-deps -v --no-build-isolation --no-binary :all: ../flit_core-*/
%pyproject_wheel


%install
%pyproject_install

## Vendoring example
# %%{vendor_pip} ../prompt_toolkit-*/
# find %{buildroot}%{python3_sitelib}/awscli -type f -name '*.py' -exec sed \
#   -e 's/from prompt_toolkit/from awscli._vendor.prompt_toolkit/' \
#   -e 's/import prompt_toolkit/import awscli._vendor.prompt_toolkit/' \
#   -i '{}' +

%pyproject_save_files awscli

# remove unnecessary scripts
rm -vf %{buildroot}%{_bindir}/{aws_bash_completer,aws_zsh_completer.sh,aws.cmd}

# install shell completion
install -Dpm0644 bin/aws_bash_completer \
  %{buildroot}%{_datadir}/bash-completion/completions/aws
install -Dpm0644 bin/aws_zsh_completer.sh \
  %{buildroot}%{_datadir}/zsh/site-functions/_awscli


%check
%pyproject_check_import
export OPENSSL_ENABLE_SHA1_SIGNATURES=yes

# Upstream also treats some warnings, such as DeprecationWarning, as a failure, but the
# code has deprecation warnings in it.  So, we disable warnings as errors for both
# sets of tests below.
%pytest tests/unit \
  --disable-pytest-warnings -Wd \
  -k "not test_non_aggregate_keys" \
  --ignore tests/unit/output/test_yaml_output.py

# awscli has some command runners built into tests and some of them eat the environment
# variables, especially PYTHONPATH, and cause awscli to fail to import.
%pytest tests/functional \
  --disable-pytest-warnings -Wd \
  --ignore tests/functional/autocomplete/test_completion_files.py \
  --ignore tests/functional/botocore/test_waiter_config.py \
  --ignore tests/functional/botocore/leak/test_resource_leaks.py \
  -k "not test_smoke_test_completer"


%files -f %{pyproject_files}
%license LICENSE.txt
%doc README.rst
%{_bindir}/aws
%{_bindir}/aws_completer
%{_datadir}/bash-completion/completions/aws
%{_datadir}/zsh/site-functions/_awscli


%changelog
* Fri Sep 08 2023 Major Hayden <major@redhat.com> - 2.13.17-1
- Initial RHEL 9 package.
