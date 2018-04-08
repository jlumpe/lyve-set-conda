"""Build script for Lyve-SET Conda package"""

import os
import subprocess as sp


# Make rules to run
BASE_MAKE_RULES = [
	'install-mkdir',
	'install-SGELK',
	'install-CGP',
	'install-perlModules',
	'install-config'
]
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
	'README.md',
	'LICENSE',
]


def log(message, *args, **kwargs):
	"""Write line to stdout with recognizable prefix.

	:param str message: Message to write
	:param \\**args: Positional arguments to format message with.
	:param \\**kwargs: Keyword arguments to format message with.
	"""
	print('\n@@', message.format(*args, **kwargs), '\n')


def cmd(*args, **export):
	"""Run a command in a subprocess.

	Prints command before executing.

	:param \\*args: Command and its arguments.
	:param \\**export: Environment variables to export.
	"""

	# Print the command
	msg = '$'

	if export is not None:
		for k, v in export.items():
			msg += ' {}="{}"'.format(k, v)

	for arg in args:
		msg += ' ' + arg

	log(msg)

	# Environment variables
	env = None
	if export is not None:
		env = dict(os.environ)
		env.update(export)

	# Run
	p = sp.Popen(args, env=env)
	rcode = p.wait()

	# Check exit code
	if rcode:
		raise RuntimeError(
			'Process returned non-zero exit code: {}'
			.format(rcode)
		)


def make_symlink_relative(path):
	"""Replace a symbolic link with a relative one.

	:param str path: Path to symbolic link.
	"""
	assert os.path.islink(path)
	target = os.readlink(path)

	# Skip if already relative
	if not os.path.isabs(target):
		return

	rel = os.path.relpath(target, os.path.dirname(path))
	os.unlink(path)
	os.symlink(rel, path)


def build(work_dir, prefix, dirty=False):
	"""Run the build process.

	:param str work_dir: Working directory containing the repo's source code.
	:param str prefix: Path to install to (should already exist).
	:param bool dirty: Whether the build process has already been run in this
		directory.
	"""

	log('Beginning build process')

	os.chdir(work_dir)

	# Makefile rules to run
	make_rules = BASE_MAKE_RULES[:]

	if dirty:
		log(
			'--dirty is set, skipping the following make rules: {}',
			' '.join(EXPENSIVE_MAKE_RULES),
		)
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
			make_symlink_relative(fpath)

	# Directory to install to
	install_dir = os.path.join(prefix, INSTALL_DIR)

	log('Installing to {}', install_dir)
	cmd('mkdir', '-p', install_dir)

	# Copy files
	log('Copying files...')

	for file in INSTALL_FILES:
		cmd(
			'cp',
			'-r',
			os.path.join(work_dir, file),
			os.path.join(install_dir, file),
		)

	# Install wrapper script
	script_src = os.path.join(work_dir, 'wrapper.sh')
	script_dst = os.path.join(prefix, 'bin', 'lyve-set')

	cmd('cp', script_src, script_dst)
	cmd('chmod', '+x', script_dst)

	# Done
	log('Install script completed successfully')


if __name__ == '__main__':
	if os.environ.get('CONDA_BUILD') != '1':
		raise RuntimeError('CONDA_BUILD environment variable not set')

	dirty = os.environ.get('DIRTY', '') == '1'
	build(os.getcwd(), os.environ['PREFIX'], dirty=dirty)
