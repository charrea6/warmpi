try:
    import xml.etree.cElementTree as ElementTree
except:
    import xml.etree.ElementTree as ElementTree

import datetime
import re
import logging

RE_TIME = re.compile('(\d?\d):(\d\d)')
log = logging.getLogger('schedule.program')


class OverlapError(Exception):
    pass

class ProgramActiveError(Exception):
    pass

class InvalidFormatError(Exception):
    pass

class Programs(object):
    def __init__(self, path, update_cb):
        self.path = path
        self.programs = {}
        self.active_program = None
        self.next_id = 0
        self.updated = update_cb
        try:
            self.__load()
        except:
            print 'Failed to load programs!'
            import traceback
            traceback.print_exc()
            log.warn('Failed to load programs', exc_info=True)

    def add_program(self, program):
        if program.id is None:
            program.id = str(self.next_id)
            while program.id in self.programs:
                self.next_id += 1
                program.id = str(self.next_id)
            self.next_id += 1

        self.programs[program.id] = program
        self.__save('add-program', program)
        return program

    def remove_program(self, program_id):
        if self.active_program and self.active_program == program_id:
            raise ProgramActiveError()
        del self.programs[program_id]
        self.__save('remove-program', program_id)

    def add_period(self, program_id, period):
        self.programs[program_id].add_period(period)
        self.__save('add-period', period)
        return period

    def remove_period(self, period_id):
        program_id,_ = period_id.split(':')
        self.programs[program_id].remove_period(period_id)
        self.__save('remove-period', period_id)

    def set_active_program(self, program_id):
        if self.active_program is not None and self.active_program.id == program_id:
            return
        new_program = self.programs[program_id]
        if self.active_program is not None:
            self.active_program.active = False
        new_program.active = True
        self.active_program = new_program
        self.__save('active-program', self.active_program)

    def __save(self, reason, arg):
        programs = ElementTree.Element('programs')
        for program in self.programs.values():
            programs.append(ElementTree.XML(program.to_xml()))
        tree = ElementTree.ElementTree(programs)
        tree.write(self.path)
        self.updated(self, reason, arg)

    def __load(self):
        tree = ElementTree.ElementTree()
        tree.parse(self.path)
        self.active_program = None
        for element in tree.findall('program'):
            program = Program.from_xml(element)
            self.programs[program.id] = program
            if self.active_program is None:
                if program.active:
                    self.active_program = program
            else:
                program.active = False
        self.updated(self, 'load', None)

    def to_xml(self):
        element = ElementTree.Element('programs')
        for program in self.programs.values():
            element.append(ElementTree.Element('program',
                  {'id':program.id, 'name':program.name, 'active':'%d' % program.active}))
        return ElementTree.tostring(element, 'utf-8')


class Program(object):
    def __init__(self, name, id=None):
        self.id = None if id is None else str(id)
        self.next_id = 0
        self.name = name
        self.active = False
        self.periods = {}

    def add_period(self, period):
        for p in self.periods.values():
            if p.system == period.system:
                if p.start >= period.start and p.start < period.end or \
                    period.start >= p.start and period.start < p.end:
                    # We have an overlap but are these on different days?
                    if p.days & period.days:
                        raise OverlapError('Overlap detected')

        if period.id is None:
            period.id = '%s:%d' % (self.id, self.next_id)
            while period.id in self.periods:
                self.next_id += 1
                period.id = '%s:%d' % (self.id, self.next_id)
            self.next_id += 1

        self.periods[period.id] = period

    def remove_period(self, period_id):
        del self.periods[period_id]

    def get_periods_for_day(self, day):
        periods = []
        for period in self.periods.values():
            if period.is_valid_for_day(day):
                periods.append(period)
        return periods


    def to_xml(self):
        element = ElementTree.Element('program', {'name':self.name})
        if self.id is not None:
            element.attrib['id'] = self.id
            element.attrib['active'] = '%d' % self.active

        for period in self.periods.values():
            element.append(ElementTree.XML(period.to_xml()))
        return ElementTree.tostring(element, 'utf-8')

    @classmethod
    def from_xml(cls, element):
        if isinstance(element, (str, unicode)):
            element = ElementTree.XML(element)
        id = element.attrib.get('id', None)
        name = element.attrib['name']
        program = Program(name, id)
        program.active = bool(int(element.attrib.get('active', 0)))
        for element in element.findall('period'):
            program.add_period(Period.from_xml(element))
        return program


class Period(object):
    DAYS = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
    SYSTEMS = ('HW', 'CH')

    def __init__(self, system, days, start, end, temperatures, id=None):
        self.id = None if id is None else str(id)
        self.system = system
        self.days = set(days)
        self.start = start
        self.end = end
        self.temperatures = temperatures

    def is_valid_for_day(self, day):
        return day in self.days

    def to_xml(self):
        id = '' if self.id is None else ('id="%s"' % self.id)
        temperatures = ''
        if self.temperatures:
            for temperature,zone in self.temperatures:
                temperatures += '<temperature zone="%s">%d</temperature>' % (zone, temperature)
        days = ''
        if self.days:
            for day in self.days:
                days += '<day>%s</day>' % self.DAYS[day]
        return '<period %s system="%s"><start>%s</start><end>%s</end>%s%s</period>' %\
               (id, self.system, self.start.strftime('%H:%M'), self.end.strftime('%H:%M'), days, temperatures)

    @classmethod
    def from_xml(cls, element):
        if isinstance(element, (str, unicode)):
            element = ElementTree.fromstring(element)
        id = element.attrib.get('id', None)
        system = element.attrib['system']
        if system not in Period.SYSTEMS:
            raise InvalidFormatError('Unknown system "%s"' % system)

        def to_time(text):
            m = RE_TIME.match(text)
            if m is None:
                raise InvalidFormatError('"%s" is not a valid time format' % text)
            return datetime.time(int(m.group(1)), int(m.group(2)))

        start = to_time(element.find('start').text)
        end = to_time(element.find('end').text)
        days = set()
        for day_element in element.findall('day'):
            try:
                day = Period.DAYS.index(day_element.text)
                days.add(day)
            except ValueError:
                raise InvalidFormatError('Unknown day "%s"' % day_element.text)
        temperatures = []
        for temp_element in element.findall('temperature'):
            temperature = int(temp_element.text)
            zone = temp_element.attrib['zone']
            temperatures.append((temperature, zone))
        return Period(system, days, start, end, temperatures, id)
