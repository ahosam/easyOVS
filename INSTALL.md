EasyOVS Installation/Configuration Notes
===

# EasyOVS 0.5

The supported installation methods for EasyOVS are

1. Native installation on common Linux distributions, such as Ubuntu, Debian,
   CentOS and Fedora.

2. Other distributions may be supported in the future - if you would like to
   contribute an installation script, we would welcome it!

## Native installation from source on Ubuntu, Debian, CentOS and Fedora

If you're reading this, you've probably already done so, but the command to
download the EasyOVS source code is:

`$ git clone git://github.com/yeasy/easyovs.git`

If you are running Ubuntu, you may be able to use our handy `install.sh`
script, which is in `easyovs/util`.

*WARNING: USE AT YOUR OWN RISK!*

To install ALL of the software which is potentially useful software, you may
use:

`$ sudo bash easyovs/util/install.sh -a`

The time depends on the network quality and your machine performance. This
takes about 1 minutes on our test system.

You can change the directory where the dependencies are installed using the
`-s <directory>` flag.

`$ sudo bash easyovs/util/install.sh -s <directory> -a`

## Installation on other Linux distributions

Although we don't support other Linux distributions directly, it should be
possible to install and run EasyOVS with some degree of manual effort.

In general, you must have:

* Python, `bash`, `git`, `make`, etc.

* Root privileges (required for network device access)

We encourage contribution of patches to the `install.sh` script to support
other Linux distributions.
