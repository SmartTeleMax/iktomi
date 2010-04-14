import os
import re
import sys
import datetime

from jinja2 import Environment, FileSystemLoader


CURDIR = os.path.dirname(os.path.abspath(__file__))

def get_template():
    jinja_env = Environment(loader=FileSystemLoader([CURDIR]),
                            autoescape=True)
    return jinja_env.get_template('debug.html')

def smart_unicode(s, *args, **kwargs):
    return unicode(s)

def technical_500_response(rctx, exc_type, exc_value, tb):
    """
    Create a technical server error response. The last three arguments are
    the values returned from sys.exc_info() and friends.
    """
    reporter = ExceptionReporter(rctx, exc_type, exc_value, tb)
    return reporter.get_traceback_html()


class ExceptionReporter:
    """
    A class to organize and coordinate reporting on exceptions.
    """
    def __init__(self, rctx, exc_type, exc_value, tb):
        self.rctx = rctx
        self.exc_type = exc_type
        self.exc_value = exc_value
        self.tb = tb

    def get_traceback_html(self):
        "Return HTML code for traceback."

        frames = self.get_traceback_frames()

        unicode_hint = ''
        if issubclass(self.exc_type, UnicodeError):
            start = getattr(self.exc_value, 'start', None)
            end = getattr(self.exc_value, 'end', None)
            if start is not None and end is not None:
                unicode_str = self.exc_value.args[1]
                unicode_hint = smart_unicode(unicode_str[max(start-4, 0):min(end+5, len(unicode_str))], 'ascii', errors='replace')
        
        environment = self.rctx.request.environ.items()
        environment.sort(key=lambda x: x[0])

        c = {
            'exception_type': self.exc_type.__name__,
            'exception_value': smart_unicode(self.exc_value, errors='replace'),
            'unicode_hint': unicode_hint,
            'frames': frames,
            'lastframe': frames[-1],
            'environment': environment,
            'rctx': self.rctx,
            'sys_executable': sys.executable,
            'sys_version_info': '%d.%d.%d' % sys.version_info[0:3],
            'server_time': datetime.datetime.now(),
            'sys_path' : sys.path,
        }

        return get_template().render(c)

    def _get_lines_from_file(self, filename, lineno, context_lines, loader=None, module_name=None):
        """
        Returns context_lines before and after lineno from file.
        Returns (pre_context_lineno, pre_context, context_line, post_context).
        """
        source = None
        if loader is not None and hasattr(loader, "get_source"):
            source = loader.get_source(module_name)
            if source is not None:
                source = source.splitlines()
        if source is None:
            try:
                f = open(filename)
                try:
                    source = f.readlines()
                finally:
                    f.close()
            except (OSError, IOError):
                pass
        if source is None:
            return None, [], None, []

        encoding = 'ascii'
        for line in source[:2]:
            # File coding may be specified. Match pattern from PEP-263
            # (http://www.python.org/dev/peps/pep-0263/)
            match = re.search(r'coding[:=]\s*([-\w.]+)', line)
            if match:
                encoding = match.group(1)
                break
        source = [unicode(sline, encoding, 'replace') for sline in source]

        lower_bound = max(0, lineno - context_lines)
        upper_bound = lineno + context_lines

        pre_context = [line.strip('\n') for line in source[lower_bound:lineno]]
        context_line = source[lineno].strip('\n')
        post_context = [line.strip('\n') for line in source[lineno+1:upper_bound]]

        return lower_bound, pre_context, context_line, post_context

    def get_traceback_frames(self):
        frames = []
        tb = self.tb
        while tb is not None:
            # support for __traceback_hide__ which is used by a few libraries
            # to hide internal frames.
            if tb.tb_frame.f_locals.get('__traceback_hide__'):
                tb = tb.tb_next
                continue
            filename = tb.tb_frame.f_code.co_filename
            function = tb.tb_frame.f_code.co_name
            lineno = tb.tb_lineno - 1
            loader = tb.tb_frame.f_globals.get('__loader__')
            module_name = tb.tb_frame.f_globals.get('__name__')
            pre_context_lineno, pre_context, context_line, post_context = self._get_lines_from_file(filename, lineno, 7, loader, module_name)
            if pre_context_lineno is not None:
                frames.append({
                    'tb': tb,
                    'filename': filename,
                    'function': function,
                    'lineno': lineno + 1,
                    'vars': tb.tb_frame.f_locals.items(),
                    'id': id(tb),
                    'pre_context': pre_context,
                    'context_line': context_line,
                    'post_context': post_context,
                    'pre_context_lineno': pre_context_lineno + 1,
                })
            tb = tb.tb_next

        if not frames:
            frames = [{
                'filename': '&lt;unknown&gt;',
                'function': '?',
                'lineno': '?',
                'context_line': '???',
            }]

        return frames

    def format_exception(self):
        """
        Return the same data as from traceback.format_exception.
        """
        import traceback
        frames = self.get_traceback_frames()
        tb = [ (f['filename'], f['lineno'], f['function'], f['context_line']) for f in frames ]
        list = ['Traceback (most recent call last):\n']
        list += traceback.format_list(tb)
        list += traceback.format_exception_only(self.exc_type, self.exc_value)
        return list

