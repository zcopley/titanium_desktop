import app
import osx_app
import linux_app
import win32_app
import os
import platform
import subprocess
import sys
import os.path as p
import __init__

class PackagingEnvironment(object):
	def __init__(self, target_os, packaging_server=False):
		self.components_dir = None
		self.version = __init__.get_titanium_version()
		self.excludes = ['.pdb', '.exp', '.ilk', '.lib', '.svn',
			'.git', '.gitignore', '.cvsignore']

		self.target_os = target_os

		script_dir = p.abspath(p.dirname(sys._getframe(0).f_code.co_filename))
		if packaging_server:
			self.init_packaging_server_dirs(script_dir)
		else:
			self.init_normal_dirs(script_dir)

	def init_packaging_server_dirs(self, script_dir):
		self.install_dirs = [p.join(script_dir, '..', '..', '..')]

	def init_normal_dirs(self, script_dir):
		if (self.target_os == 'linux'):
			self.install_dirs = [
				p.expanduser('~/.titanium'),
				"/opt/titanium",
				"/usr/local/lib/titanium",
				"/usr/lib/titanium"
			]
		elif (self.target_os == 'osx'):
			self.install_dirs = [
				p.expanduser('~/Library/Application Support/Titanium'),
				'/Library/Application Support/Titanium'
			]
		elif (self.target_os == 'win32'):
			self.install_dirs = [
				p.join(os.environ['APPDATA'], 'Titanium'),
				# TODO: Is there a better way to determine this directory?
				'C:\\ProgramData\\Titanium',
				'C:\\Documents and Settings\All Users\Application Data\Titanium'
			]
		else:
			raise Exception("Unknown environment!")

		# If we are in the build hierarchy, try to find runtimes and modules
		# relative to this file's location.
		build_subpath = p.join('build', self.target_os)
		self.components_dir = None
		if (p.exists(p.join(script_dir, '..', 'kroll')) and
			p.exists(p.join(script_dir, '..', 'build', self.target_os, 'runtime')) and
			p.exists(p.join(script_dir, '..', 'build', self.target_os, 'sdk'))):
			self.components_dir = p.join(script_dir, '..', 'build', self.target_os)
		elif p.exists(p.join(script_dir, '..', 'runtime')) and p.exists(p.join(script_dir, '..', 'sdk')):
			self.components_dir = p.join(script_dir, '..')

	def create_app(self, path):
		if self.target_os == 'linux':
			return linux_app.LinuxApp(self, path)
		if self.target_os == 'osx':
			return osx_app.OSXApp(self, path)
		if self.target_os == 'win32':
			return win32_app.Win32App(self, path)

	def log(self, text):
		print u'    -> %s' % text
		sys.stdout.flush()

	def get_excludes(self):
		return self.excludes

	def get_component(self, type, name, version):
		# First try the build directory.
		if self.components_dir:
			target = p.join(self.components_dir, type)
			if name: # Modules have names
				 target = p.join(target, name)
			if p.exists(target):
				return target

		# Next try searching list of installed directories
		for dir in self.install_dirs:
			target = p.join(dir, type, self.target_os)
			if name: target = p.join(target, name)
			target = p.join(target, version)
			if p.exists(target):
				return target

		return None

	def get_sdk_dir(self, version):
		c = self.get_component('sdk', None, version)
		if not c:
			raise Exception(u'Could not find SDK version %s' % version)
		return c

	def get_runtime_dir(self, version):
		c = self.get_component('runtime', None, version)
		if not c:
			raise Exception(u'Could not find runtime version %s' % version)
		return c

	def get_module_dir(self, module):
		c = self.get_component('modules', module[0], module[1])
		if not c:
			raise Exception(u'Could not find module %s-%s' % module)
		return c

	def run(self, args):
		self.log(u'Launching: %s' % args)
		subprocess.call(args)

	def ignore_errors(self, function):
		try:
			function()
		except Exception, e:
			self.log("Ignoring error: %s" % e)
