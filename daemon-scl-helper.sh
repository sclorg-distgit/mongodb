#!/bin/sh

# This helper script is necessary for having proper SELinux context of daemon
# process run in SCL environment via systemd unit file.
# Without this script the process looses SELinux type because /usr/bin/scl
# has context bin_t and unit_t -> bin_t results in unconfined process running.
# If this helper script has the same SELinux context as the original binary,
# the process will have proper SELinux context.
#
# This script was designed to be usable the same as the scl command is used,
# including the collections given as more arguments, separated from binary
# itself by -- separator.
# So it is possible to use the list of collections to be enabled via
# environment file.
# Thus, instead of:
#   /usr/bin/scl enable scl1 scl2 -- /path/to/bin arg1 arg2
# you can use:
#   /usr/bin/this-script enable scl1 scl2 -- /path/to/bin arg1 arg2
#
# Notice: do not forget to set proper SELinux context for this file.
# The context should be the same as the binary running has.

action="$1"
shift

while [ -n "$1" ] && [ "$1" != "--" ] ; do
  source scl_source "$action" "$1"
  shift
done

if [ $# -le 2 ] ; then
  echo "Usage `basename $0` enable sclname [sclname ...] -- /path/to/bin [arg ...]" >&2
  exit 1
fi

shift

exec "$@"



