# (c) 2010-2011 by Anton Korenyushkin

from subprocess import Popen, PIPE, STDOUT

import argparse
from django.utils.text import smart_split, unescape_string_literal

from error import Error
from paths import ROOT


class _PassAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=0, **kwargs):
        argparse.Action.__init__(
            self, option_strings, argparse.SUPPRESS, nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _Parser(argparse.ArgumentParser):
    def __init__(self, description):
        argparse.ArgumentParser.__init__(
            self, description=description, add_help=False)
        self.register('action', None, _PassAction)
        self('pos', nargs='*', action='store')

    def __call__(self, *args, **kwargs):
        self.add_argument(*args, **kwargs)
        return self

    def error(self, message):
        raise Error(message, self.description)


_parsers = {
    'add': _Parser('''\
usage: add [options] [--] <filepattern>...

    -n, --dry-run         dry run
    -v, --verbose         be verbose

    -f, --force           allow adding otherwise ignored files
    -u, --update          update tracked files
    -N, --intent-to-add   record only the fact that the path will be added later
    -A, --all             add all, noticing removal of tracked files
    --refresh             don't add, only refresh the index
    --ignore-errors       just skip files which cannot be added because of errors
''')('-n', '--dry-run',
     '-v', '--verbose'
     '-f', '--force',
     '-u', '--update',
     '-N', '--intent-to-add',
     '-A', '--all',
     '--refresh',
     '--ignore-errors'),

    'branch': _Parser('''\
usage: branch [options] [-r | -a] [--merged | --no-merged]
   or: branch [options] [-l] [-f] <branchname> [<start-point>]
   or: branch [options] [-r] (-d | -D) <branchname>
   or: branch [options] (-m | -M) [<oldbranch>] <newbranch>

    -v, --verbose         be verbose
    --track               set up tracking mode (see help pull)
    -r                    act on remote-tracking branches
    --contains <commit>   print only branches that contain the commit
    --abbrev[=<n>]        use <n> digits to display SHA-1s

    -a                    list both remote-tracking and local branches
    -d                    delete fully merged branch
    -D                    delete branch (even if not merged)
    -m                    move/rename a branch and its reflog
    -M                    move/rename a branch, even if target exists
    -l                    create the branch's reflog
    -f                    force creation (when already exists)
    --no-merged <commit>  print only not merged branches
    --merged <commit>     print only merged branches
''')('-v', '--verbose',
     '--track',
     '-r',
     '-a',
     '-d',
     '-D',
     '-m',
     '-M',
     '-l',
     '-f')
    ('--contains',
     '--no-merged',
     '--merged', nargs=1)
    ('--abbrev', nargs='?'),

    'checkout': _Parser('''\
usage: checkout [options] <branch>
   or: checkout [options] [<branch>] -- <file>...

    -q, --quiet           be quiet
    -b <new branch>       branch
    -l                    log for new branch
    -t, --track           track
    -2, --ours            stage
    -3, --theirs          stage
    -f                    force
    -m, --merge           merge
    --conflict <style>    conflict style (merge or diff3)
''')('-q', '--quiet',
     '-l',
     '-t', '--track',
     '-2', '--ours',
     '-3', '--theirs',
     '-f',
     '-m', '--merge')
    ('-b',
     '--conflict', nargs=1),

    'clean': _Parser('''\
usage: clean [-d] [-f] [-n] [-q] [-x | -X] [--] <paths>...

    -q, --quiet           be quiet
    -n, --dry-run         dry run
    -f                    force
    -d                    remove whole directories
    -x                    remove ignored files, too
    -X                    remove only ignored files
''')('-q', '--quiet',
     '-n', '--dry-run',
     '-f',
     '-d',
     '-x',
     '-X'),

    'commit': _Parser('''\
usage: commit [options] [--] <filepattern>...

    -q, --quiet           be quiet
    -v, --verbose         be verbose

Commit message options
    -m, --message <MESSAGE>
                          specify commit message
    -C, --reuse-message <COMMIT>
                          reuse message from specified commit

Commit contents options
    -a, --all             commit all changed files
    -i, --include         add specified files to index for commit
    -o, --only            commit only specified files
    --amend               amend previous commit
    --allow-empty         ok to record an empty change
''')('-q', '--quiet',
     '-v', '--verbose',
     '-a', '--all',
     '-i', '--include',
     '-o', '--only',
     '--amend',
     '--allow-empty')
    ('-m', '--message', nargs=1, required=True)
    ('-C', '--reuse-message', '--author', nargs=1),

    'describe': _Parser('''\
usage: describe [options] <committish>*

    --contains            find the tag that comes after the commit
    --debug               debug search strategy on stderr
    --all                 use any ref in .git/refs
    --tags                use any tag in .git/refs/tags
    --long                always use long format
    --abbrev[=<n>]        use <n> digits to display SHA-1s
    --exact-match         only output exact matches
    --candidates <n>      consider <n> most recent tags (default: 10)
    --match <pattern>     only consider tags matching <pattern>
    --always              show abbreviated commit object as fallback
''')('--contains',
     '--debug',
     '--all',
     '--tags',
     '--long',
     '--exact-match',
     '--always')
    ('--candidates',
     '--match', nargs=1)
    ('--abbrev', nargs='?'),

    'diff': _Parser('''\
usage: diff [--options] [--] [<path>...]
   or: diff [--options] --cached [<commit>] [--] [<path>...]
   or: diff [--options] <commit> [--] [<path>...]
   or: diff [--options] <commit> <commit> [--] [<path>...]
   or: diff [--options] <commit>..<commit> [--] [<path>...]
   or: diff [--options] <commit>...<commit> [--] [<path>...]
'''),

    'fetch': _Parser('''\
usage: fetch [options] [<repository> <refspec>...]

    -v, --verbose         be more verbose
    -q, --quiet           be more quiet
    -a, --append          append to FETCH_HEAD instead of overwriting
    -f, --force           force overwrite of local branch
    -t, --tags            fetch all tags and associated objects
    -n                    do not fetch all tags (--no-tags)
    -k, --keep            keep downloaded pack
    -u, --update-head-ok  allow updating of HEAD ref
    --depth <DEPTH>       deepen history of shallow clone
''')('-v', '--verbose',
     '-q', '--quiet',
     '-a', '--append',
     '-f', '--force',
     '-t', '--tags',
     '-n', '--no-tags',
     '-k', '--keep',
     '-u', '--update-head-ok')
    ('--depth', nargs=1),

    'grep': _Parser('''\
usage: grep <option>* [-e] <pattern> <rev>* [[--] <path>...]
''')('--cached',
     '-i', '--ignore-case',
     '-w', '--word-regexp',
     '-v', '--invert-match',
     '-h',
     '-H',
     '--full-name',
     '-E', '--extended-regexp,',
     '-G', '--basic-regexp',
     '-F', '--fixed-strings',
     '-n',
     '-l', '--files-with-matches, --name-only,',
     '-L', '--files-without-match',
     '-c', '--count',
     '--all-match')
    ('-A',
     '-B',
     '-C',
     '-e',
     '--and,',
     '--or,',
     '--not', nargs=1),

    'log': _Parser('''\
usage: log [<options>] [<since>..<until>] [[--] <path>...]
''')('-i', '--regexp-ignore-case',
     '-E', '--extended-regexp',
     '-F', '--fixed-strings',
     '--remove-empty',
     '--no-merges',
     '--first-parent',
     '--not',
     '--all',
     '--branches',
     '--tags',
     '--remotes',
     '--merge')
    ('-n', '--max-count',
     '--skip',
     '--since',
     '--after',
     '--until',
     '--before',
     '--author',
     '--commiter',
     '--grep', nargs=1),

    'merge': _Parser('''\
usage: merge [options] <remote>...
   or: merge [options] <msg> HEAD <remote>

    -n                    do not show a diffstat at the end of the merge
    --stat                show a diffstat at the end of the merge
    --summary             (synonym to --stat)
    --log                 add list of one-line log to merge commit message
    --squash              create a single commit instead of doing a merge
    --commit              perform a commit if the merge succeeds (default)
    --ff                  allow fast forward (default)
    -s, --strategy <strategy>
                          merge strategy to use
    -m, --message <message>
                          message to be used for the merge commit (if any)
    -v, --verbose         be more verbose
    -q, --quiet           be more quiet
''')('-n',
     '--stat',
     '--summary',
     '--log',
     '--squash',
     '--commit',
     '--ff',
     '-v', '--verbose',
     '-q', '--quiet')
    ('-s', '--strategy',
     '-m', '--message', nargs=1),

    'mv': _Parser('''\
usage: mv [options] <source>... <destination>

    -n, --dry-run         dry run
    -f                    force move/rename even if target exists
    -k                    skip move/rename errors
''')('-n', '--dry-run'
     '-f',
     '-k'),

    'push': _Parser('''\
usage: push [--all | --mirror] [--dry-run] [--tags] [-f | --force] [-v] [<repository> <refspec>...]

    -v, --verbose         be verbose
    --all                 push all refs
    --mirror              mirror all refs
    --tags                push tags
    --dry-run             dry run
    -f, --force           force updates
    --thin                use thin pack
''')('-v, --verbose'
     '--all',
     '--mirror',
     '--tags',
     '--dry-run',
     '-f, --force',
     '--thin'),

    'rebase': _Parser('''\
usage: rebase  [-v] [--force-rebase | -f] [--onto <newbase>] [<upstream>|--root] [<branch>]
''')('-m', '--merge',
     '-v', '--verbose',
     '--stat',
     '-n', '--no-stat',
     '-f', '--force-rebase',
     '--committer-date-is-author-date,',
     '--ignore-date',
     '-p', '--preserve-merges',
     '--root')
    ('-C',
     '--whitespace', nargs=1),

    'remote': _Parser('''\
usage: remote [-v | --verbose]
   or: remote add [-t <branch>] [-m <master>] [-f] [--mirror] <name> <url>
   or: remote rename <old> <new>
   or: remote rm <name>
   or: remote set-head <name> [-a | -d | <branch>]
   or: remote show [-n] <name>
   or: remote prune [-n | --dry-run] <name>
   or: remote [-v | --verbose] update [-p | --prune] [group]

    -v, --verbose         be verbose
''')('-v', '--verbose',
     '-n', '--dry-run',
     '-p', '--prune',
     '--mirror',
     '-a',
     '-d',
     '-f')
    ('-t',
     '-m', nargs=1),

    'reset': _Parser('''\
usage: reset [--mixed | --soft | --hard | --merge] [-q] [<commit>]
   or: reset [--mixed] <commit> [--] <paths>...

    --mixed               reset HEAD and index
    --soft                reset only HEAD
    --hard                reset HEAD, index and working tree
    --merge               reset HEAD, index and working tree
    -q                    disable showing new HEAD in hard reset and progress message
''')('--mixed',
     '--soft',
     '--hard',
     '--merge',
     '-q'),

    'revert': _Parser('''\
usage: revert [options] <commit-ish>

    -n, --no-commit       don't automatically commit
    -x                    append commit name when cherry-picking
    -m, --mainline <n>    parent number
''')('-n', '--no-commit',
     '-x')
    ('-m', '--mainline', nargs=1),

    'rm': _Parser('''\
usage: rm [options] [--] <file>...

    -n, --dry-run         dry run
    -q, --quiet           be quiet
    --cached              only remove from the index
    -f, --force           override the up-to-date check
    -r                    allow recursive removal
''')('-n', '--dry-run',
     '-q', '--quiet',
     '--cached',
     '-f', '--force',
     '-r'),

    'show': _Parser('''\
usage: show [options] <object>...
''')('--abbrev-commit'
     '--oneline')
    ('--pretty', '--format', nargs=1),

    'stash': _Parser('''\
usage: stash list [<options>]
   or: stash (show | drop | pop ) [<stash>]
   or: stash apply [--index] [<stash>]
   or: stash branch <branchname> [<stash>]
   or: stash [save [--keep-index] [<message>]]
   or: stash clear
''')('--index',
     '--keep-index'),

    'status': _Parser('''\
usage: status [options] [--] <filepattern>...

    -v, --verbose         be verbose
    -s, --short           show status concisely

    -a, --all             commit all changed files
    -i, --include         add specified files to index for commit
    -o, --only            commit only specified files
    --amend               amend previous commit
    --allow-empty         ok to record an empty change
''')('-v', '--verbose',
     '-s', '--short',
     '-a', '--all',
     '-i', '--include',
     '-o', '--only',
     '--amend',
     '--allow-empty'),

    'tag': _Parser('''\
usage: tag [-a] [-f] -m <msg> <tagname> [<head>]
   or: tag -d <tagname>...
   or: tag -l [-n[<num>]] [<pattern>]
   or: tag -v <tagname>...

    -l                    list tag names
    -n[<n>]               print n lines of each tag message
    -d                    delete tags

Tag creation options
    -a                    annotated tag, needs a message
    -m <msg>              message for the tag
    -f                    replace the tag if exists

Tag listing options
    --contains <commit>   print only tags that contain the commit
''')('-f', '-l', '-d')
    ('-a', action='store_true')
    ('-m', nargs=1, action='store')
    ('-n', nargs='?'),
}


def _add_diff_args(parser):
    parser(
        '-p', '-u',
        '--patience',
        '--numstat',
        '--shortstat',
        '--summary',
        '--name-only',
        '--name-status',
        '--no-renames',
        '--check',
        '--full-index',
        '-B',
        '-M',
        '-C',
        '--pickaxe-all',
        '--pickaxe-regex',
        '-R',
        '-b', '--ignore-space-change',
        '-w', '--ignore-all-space',
        '--no-prefix',
        '--cached',
        '--staged')
    parser(
        '-U', '--unified',
        '--diff-filter',
        '-S',
        '--relative',
        '--inter-hunk-context',
        '--src-prefix',
        '--dst-prefix', nargs=1)
    parser(
        '--stat',
        '--dirstat',
        '--dirstat-by-file',
        '--abbrev', nargs='?')


_add_diff_args(_parsers['diff'])
_add_diff_args(_parsers['log'])
_parsers['pull'] = _parsers['fetch']


def _check_url(url):
    protocol, sep, _ = url.partition('://')
    if sep:
        if protocol not in (
            'git', 'http', 'ssh', 'https', 'git+ssh', 'ssh+git'):
            raise Error('The protocol "%s" isn\'t supported.' % protocol)
    else:
        if '/' in url and ':' not in url:
            raise Error('Local URLs aren\'t supported.')


def parse_git_command(string):
    command, _, tail = string.lstrip().partition(' ')
    if command == 'help':
        return command, tail.split()
    try:
        parser = _parsers[command]
    except KeyError:
        raise Error('Command "%s" is not supported.' % command)
    args = []
    for arg in smart_split(tail):
        try:
            arg = unescape_string_literal(arg)
        except ValueError:
            pass
        args.append(arg)
    namespace = parser.parse_args(args)
    if command in ('push', 'pull', 'fetch'):
        for url in namespace.pos:
            _check_url(url)
    elif command == 'remote':
        if namespace.pos and namespace.pos[0] == 'add':
            _check_url(namespace.pos[-1])
    elif command == 'tag':
        if namespace.a and namespace.m is None:
            raise Error('The -m option is required if -a is used.')
    return command, args


class GitRunner(object):
    def __init__(self, dev_name, app_name, author_name, author_email):
        dev_path = ROOT.devs[dev_name]
        app_path = dev_path.apps[app_name]
        self._env = {
            'GIT_WORK_TREE': app_path.code,
            'GIT_DIR': app_path.git,
            'GIT_SSH': dev_path.ssh,
            'GIT_AUTHOR_NAME': author_name,
            'GIT_AUTHOR_EMAIL': author_email,
            'GIT_COMMITTER_NAME': author_name,
            'GIT_COMMITTER_EMAIL': author_email,
        }

    def run(self, command, *args):
        if command == 'help':
            if args:
                try:
                    return _parsers[args[0]].description
                except KeyError:
                    raise Error('Command "%s" is not supported.' % args[0])
            else:
                return '''\
The most commonly used git commands are:
   add        Add file contents to the index
   branch     List, create, or delete branches
   checkout   Checkout a branch or paths to the working tree
   commit     Record changes to the repository
   diff       Show changes between commits, commit and working tree, etc
   fetch      Download objects and refs from another repository
   grep       Print lines matching a pattern
   log        Show commit logs
   merge      Join two or more development histories together
   mv         Move or rename a file, a directory, or a symlink
   pull       Fetch from and merge with another repository or a local branch
   push       Update remote refs along with associated objects
   rebase     Forward-port local commits to the updated upstream head
   reset      Reset current HEAD to the specified state
   rm         Remove files from the working tree and from the index
   show       Show various types of objects
   status     Show the working tree status
   tag        Create, list, or delete a tag object

See 'help COMMAND' for more information on a specific command.
'''
        process = Popen(
            ['/usr/bin/git', command] + list(args),
            env=self._env,
            cwd=self._env['GIT_WORK_TREE'],
            stdout=PIPE,
            stderr=STDOUT)
        process.wait()
        return process.stdout.read()
