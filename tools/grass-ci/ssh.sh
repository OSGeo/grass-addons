#!/bin/bash
# SSH client wrapper script used to specify private key

# Author: Ivan Mincik, ivan.mincik@gmail.com

exec /usr/bin/ssh -o StrictHostKeyChecking=no -i $GRASS_CI_DIR/grass-ci-ssh-key "$@"

# vim: set ts=4 sts=4 sw=4 noet:
