import sys
from os import path

# To Install: 
#  * Place this file in C:\Python26\Lib\site-packages\IPython\UserConfig\
#  * Edit C:\Python26\Lib\site-packages\IPython\UserConfig\ipythonrc
#     - at the end of the file, add "execfile magic_srun.py"
#
# Extending the PYTHONPATH:
#  * Open the "System" Control Panel
#  * Select the Advanced tab
#  * Select "Environment Variables"
#  * Add a new PYTHONPATH variable, with the name of your directory with .py files

def magic_srun(self, parameter_s ='',runner=None,
			  file_finder=get_py_filename):
	"""Search the path for the named file, then run it inside IPython as a program.

	Usage:\\
	  %run [-n -i -t [-N<N>] -d [-b<N>] -p [profile options]] file [args]
	
	Parameters after the filename are passed as command-line arguments to
	the program (put in sys.argv). Then, control returns to IPython's
	prompt.

	This is similar to running at a system prompt:\\
	  $ python file args\\
	but with the advantage of giving you IPython's tracebacks, and of
	loading all variables into your interactive namespace for further use
	(unless -p is used, see below).

	The file is executed in a namespace initially consisting only of
	__name__=='__main__' and sys.argv constructed as indicated. It thus
	sees its environment as if it were being run as a stand-alone program
	(except for sharing global objects such as previously imported
	modules). But after execution, the IPython interactive namespace gets
	updated with all variables defined in the program (except for __name__
	and sys.argv). This allows for very convenient loading of code for
	interactive work, while giving each program a 'clean sheet' to run in.

	Options:
	
	-n: __name__ is NOT set to '__main__', but to the running file's name
	without extension (as python does under import).  This allows running
	scripts and reloading the definitions in them without calling code
	protected by an ' if __name__ == "__main__" ' clause.

	-i: run the file in IPython's namespace instead of an empty one. This
	is useful if you are experimenting with code written in a text editor
	which depends on variables defined interactively.

	-e: ignore sys.exit() calls or SystemExit exceptions in the script
	being run.  This is particularly useful if IPython is being used to
	run unittests, which always exit with a sys.exit() call.  In such
	cases you are interested in the output of the test results, not in
	seeing a traceback of the unittest module.

	-t: print timing information at the end of the run.  IPython will give
	you an estimated CPU time consumption for your script, which under
	Unix uses the resource module to avoid the wraparound problems of
	time.clock().  Under Unix, an estimate of time spent on system tasks
	is also given (for Windows platforms this is reported as 0.0).

	If -t is given, an additional -N<N> option can be given, where <N>
	must be an integer indicating how many times you want the script to
	run.  The final timing report will include total and per run results.

	For example (testing the script uniq_stable.py):

		In [1]: run -t uniq_stable

		IPython CPU timings (estimated):\\
		  User  :    0.19597 s.\\
		  System:        0.0 s.\\

		In [2]: run -t -N5 uniq_stable

		IPython CPU timings (estimated):\\
		Total runs performed: 5\\
		  Times :      Total       Per run\\
		  User  :   0.910862 s,  0.1821724 s.\\
		  System:        0.0 s,        0.0 s.

	-d: run your program under the control of pdb, the Python debugger.
	This allows you to execute your program step by step, watch variables,
	etc.  Internally, what IPython does is similar to calling:
	
	  pdb.run('execfile("YOURFILENAME")')

	with a breakpoint set on line 1 of your file.  You can change the line
	number for this automatic breakpoint to be <N> by using the -bN option
	(where N must be an integer).  For example:

	  %run -d -b40 myscript

	will set the first breakpoint at line 40 in myscript.py.  Note that
	the first breakpoint must be set on a line which actually does
	something (not a comment or docstring) for it to stop execution.

	When the pdb debugger starts, you will see a (Pdb) prompt.  You must
	first enter 'c' (without qoutes) to start execution up to the first
	breakpoint.

	Entering 'help' gives information about the use of the debugger.  You
	can easily see pdb's full documentation with "import pdb;pdb.help()"
	at a prompt.

	-p: run program under the control of the Python profiler module (which
	prints a detailed report of execution times, function calls, etc).

	You can pass other options after -p which affect the behavior of the
	profiler itself. See the docs for %prun for details.

	In this mode, the program's variables do NOT propagate back to the
	IPython interactive namespace (because they remain in the namespace
	where the profiler executes them).

	Internally this triggers a call to %prun, see its documentation for
	details on the options available specifically for profiling.

	There is one special usage for which the text above doesn't apply:
	if the filename ends with .ipy, the file is run as ipython script,
	just as if the commands were written on IPython prompt.
	"""

	# get arguments and set sys.argv for program to be run.
	opts,arg_lst = self.parse_options(parameter_s,'nidtN:b:pD:l:rs:T:e',
									  mode='list',list_all=1)

	try:
		filename = file_finder(arg_lst[0])
		if not path.isfile(filename):
			for pathdir in sys.path:
				if path.isfile(path.join(pathdir, filename)):
					filename = path.join(pathdir, filename)
					warn('Running as: ' + filename)
	except IndexError:
		warn('you must provide at least a filename.')
		print '\n%run:\n',OInspect.getdoc(self.magic_run)
		return
	except IOError,msg:
		error(msg)
		return

	if filename.lower().endswith('.ipy'):
		self.api.runlines(open(filename).read())
		return
	
	# Control the response to exit() calls made by the script being run
	exit_ignore = opts.has_key('e')
	
	# Make sure that the running script gets a proper sys.argv as if it
	# were run from a system shell.
	save_argv = sys.argv # save it for later restoring
	sys.argv = [filename]+ arg_lst[1:]  # put in the proper filename

	if opts.has_key('i'):
		# Run in user's interactive namespace
		prog_ns = self.shell.user_ns
		__name__save = self.shell.user_ns['__name__']
		prog_ns['__name__'] = '__main__'
		main_mod = self.shell.new_main_mod(prog_ns)
	else:
		# Run in a fresh, empty namespace
		if opts.has_key('n'):
			name = os.path.splitext(os.path.basename(filename))[0]
		else:
			name = '__main__'

		main_mod = self.shell.new_main_mod()
		prog_ns = main_mod.__dict__
		prog_ns['__name__'] = name

	# Since '%run foo' emulates 'python foo.py' at the cmd line, we must
	# set the __file__ global in the script's namespace
	prog_ns['__file__'] = filename

	# pickle fix.  See iplib for an explanation.  But we need to make sure
	# that, if we overwrite __main__, we replace it at the end
	main_mod_name = prog_ns['__name__']

	if main_mod_name == '__main__':
		restore_main = sys.modules['__main__']
	else:
		restore_main = False

	# This needs to be undone at the end to prevent holding references to
	# every single object ever created.
	sys.modules[main_mod_name] = main_mod
	
	stats = None
	try:
		self.shell.savehist()

		if opts.has_key('p'):
			stats = self.magic_prun('',0,opts,arg_lst,prog_ns)
		else:
			if opts.has_key('d'):
				deb = Debugger.Pdb(self.shell.rc.colors)
				# reset Breakpoint state, which is moronically kept
				# in a class
				bdb.Breakpoint.next = 1
				bdb.Breakpoint.bplist = {}
				bdb.Breakpoint.bpbynumber = [None]
				# Set an initial breakpoint to stop execution
				maxtries = 10
				bp = int(opts.get('b',[1])[0])
				checkline = deb.checkline(filename,bp)
				if not checkline:
					for bp in range(bp+1,bp+maxtries+1):
						if deb.checkline(filename,bp):
							break
					else:
						msg = ("\nI failed to find a valid line to set "
							   "a breakpoint\n"
							   "after trying up to line: %s.\n"
							   "Please set a valid breakpoint manually "
							   "with the -b option." % bp)
						error(msg)
						return
				# if we find a good linenumber, set the breakpoint
				deb.do_break('%s:%s' % (filename,bp))
				# Start file run
				print "NOTE: Enter 'c' at the",
				print "%s prompt to start your script." % deb.prompt
				try:
					deb.run('execfile("%s")' % filename,prog_ns)
					
				except:
					etype, value, tb = sys.exc_info()
					# Skip three frames in the traceback: the %run one,
					# one inside bdb.py, and the command-line typed by the
					# user (run by exec in pdb itself).
					self.shell.InteractiveTB(etype,value,tb,tb_offset=3)
			else:
				if runner is None:
					runner = self.shell.safe_execfile
				if opts.has_key('t'):
					# timed execution
					try:
						nruns = int(opts['N'][0])
						if nruns < 1:
							error('Number of runs must be >=1')
							return
					except (KeyError):
						nruns = 1
					if nruns == 1:
						t0 = clock2()
						runner(filename,prog_ns,prog_ns,
							   exit_ignore=exit_ignore)
						t1 = clock2()
						t_usr = t1[0]-t0[0]
						t_sys = t1[1]-t0[1]
						print "\nIPython CPU timings (estimated):"
						print "  User  : %10s s." % t_usr
						print "  System: %10s s." % t_sys
					else:
						runs = range(nruns)
						t0 = clock2()
						for nr in runs:
							runner(filename,prog_ns,prog_ns,
								   exit_ignore=exit_ignore)
						t1 = clock2()
						t_usr = t1[0]-t0[0]
						t_sys = t1[1]-t0[1]
						print "\nIPython CPU timings (estimated):"
						print "Total runs performed:",nruns
						print "  Times : %10s    %10s" % ('Total','Per run')
						print "  User  : %10s s, %10s s." % (t_usr,t_usr/nruns)
						print "  System: %10s s, %10s s." % (t_sys,t_sys/nruns)
						
				else:
					# regular execution
					runner(filename,prog_ns,prog_ns,exit_ignore=exit_ignore)

			if opts.has_key('i'):
				self.shell.user_ns['__name__'] = __name__save
			else:
				# The shell MUST hold a reference to prog_ns so after %run
				# exits, the python deletion mechanism doesn't zero it out
				# (leaving dangling references).
				self.shell.cache_main_mod(prog_ns,filename)
				# update IPython interactive namespace

				# Some forms of read errors on the file may mean the
				# __name__ key was never set; using pop we don't have to
				# worry about a possible KeyError.
				prog_ns.pop('__name__', None)

				self.shell.user_ns.update(prog_ns)
	finally:
		# It's a bit of a mystery why, but __builtins__ can change from
		# being a module to becoming a dict missing some key data after
		# %run.  As best I can see, this is NOT something IPython is doing
		# at all, and similar problems have been reported before:
		# http://coding.derkeiler.com/Archive/Python/comp.lang.python/2004-10/0188.html
		# Since this seems to be done by the interpreter itself, the best
		# we can do is to at least restore __builtins__ for the user on
		# exit.
		self.shell.user_ns['__builtins__'] = __builtin__
		
		# Ensure key global structures are restored
		sys.argv = save_argv
		if restore_main:
			sys.modules['__main__'] = restore_main
		else:
			# Remove from sys.modules the reference to main_mod we'd
			# added.  Otherwise it will trap references to objects
			# contained therein.
			del sys.modules[main_mod_name]

		self.shell.reloadhist()
			
	return stats


from IPython.iplib import InteractiveShell
InteractiveShell.magic_srun = magic_srun

del magic_srun
