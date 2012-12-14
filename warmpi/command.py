import optparse

class UsageError(Exception):
    pass

def define_command(commands, name, usage,  options=[]):
    def deco(func):
        commands.append(Command(name, options, usage, func))
        return func
    return deco

class Command(object):
    def __init__(self, name, options, usage, func):
        self.name = name
        self.options = options
        self.usage = usage
        self.execute = func


def dispatch(commands, args):
    found = False
    if len(args) >= 1:
        for command in commands:
            if command.name == args[0]:
                parser = optparse.OptionParser(usage=command.usage, option_list=command.options)
                options,args = parser.parse_args(args[1:])
                try:
                    command.execute(options, args)
                except UsageError:
                    parser.print_usage()

                found = True
                break

        if not found:
            print 'Command %s not found' % args[0]
    if not found:
        print 'Available commands:'
        for command in commands:
            print '    ' + command.name
