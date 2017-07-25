"""Build script for Lyve-SET Conda package"""

import os
import subprocess as sp


BASE_MAKE_RULES = ['install-SGELK', 'install-CGP', 'install-mkdir', 'install-perlModules', 'install-config']
EXPENSIVE_MAKE_RULES = ['install-phast']


# Relative directory in conda env to install to
# Just put everything in a subdirectory of opt
INSTALL_DIR = 'opt/lyve-set'

# Files to install in conda ENV from working directory
INSTALL_FILES = [
	'scripts',
	'lib',
	'plugins',
	'docs',
	'LICENSE',
]


# Contents of wrapper script
WRAPPER_SCRIPT = '''\
#!/bin/bash

# Wrapper script around Lyve-SET commands

# Parent directory of script directory
ENV_DIR=$(dirname(dirname(readlink -f $0)))

export LYVESET_DIR="$ENV_DIR/{INSTALL_DIR}"
export PATH="$LYVESET_DIR/scripts:$PATH"

if [# -eq 0 ]; then
	# No arguments, print usage and available commands

	cat <<- EOF
	Wrapper around Lyve-SET scripts

	usage:(basename0) COMMAND [COMMAND_ARGS...]


	Available Lyve-SET commands:

	EOF
	ls "$LYVESET_DIR/scripts" | sort

else
	# Run command

	CMD=$1
	shift
	"$LYVESET_DIR/scripts/$CMD" "$@"

fi
'''.format(INSTALL_DIR=INSTALL_DIR)


def log(string, *args, **kwargs):
	print('\n@@', string.format(*args, **kwargs), '\n')


def cmd(*args, export=None):

	msg = '$'

	if export is not None:
		for k, v in export.items():
			msg += ' {}="{}"'.format(k, v)

	for arg in args:
		msg += ' ' + arg

	log(msg)

	env = None
	if export is not None:
		env = dict(os.environ)
		env.update(export)

	p = sp.Popen(args, env=env)
	code = p.wait()

	if code != 0:
		raise RuntimeError('Command exited with non-zero code.')


def build(work_dir, prefix, dirty=False):

	log('Beginning build process')

	os.chdir(work_dir)

	# Makefile rules to run
	make_rules = BASE_MAKE_RULES[:]

	if dirty:
		log('--dirty is set, skipping the following make rules: ' + ' '.join(EXPENSIVE_MAKE_RULES))
	else:
		make_rules += EXPENSIVE_MAKE_RULES

	# Run Makefile
	log('Running Makefile...')
	cmd('make', *make_rules)

	# Convert absolute symlink paths to relative paths
	log('Fixing symlinks...')
	for fname in os.listdir('scripts'):
		fpath = os.path.join('scripts', fname)

		if os.path.islink(fpath):

			abspath = os.readlink(fpath)
			if not os.path.isabs(abspath):
				continue
			relpath = os.path.relpath(abspath, 'scripts')

			os.unlink(fpath)
			os.symlink(relpath, fpath)

	# Directory to install to
	install_dir = os.path.join(prefix, INSTALL_DIR)

	log('Installing to {}', install_dir)
	cmd('mkdir', '-p', install_dir)

	# Copy files
	log('Copying files...')

	for file in INSTALL_FILES:
		cmd('cp', '-r', os.path.join(work_dir, file), os.path.join(install_dir, file))

	# Create and install wrapper script
	script_path = os.path.join(prefix, 'bin', 'lyve-set')

	log('Writing wrapper script to ' + script_path + '...')
	with open(script_path, 'w') as fobj:
		fobj.write(WRAPPER_SCRIPT)

	cmd('chmod', '+x', script_path)


if __name__ == '__main__':
	if os.environ.get('CONDA_BUILD') != '1':
		raise RuntimeError('CONDA_BUILD environment variable not set')

	build(os.getcwd(), os.environ['PREFIX'], dirty=os.environ.get('DIRTY', '') == '1')
