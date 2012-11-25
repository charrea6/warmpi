import os
from socket import gethostname

from brisa.upnp.device import Device
from brisa.upnp.device.service import Service, ErrorCode

from warmpi.schedule.program import Program, Period, OverlapError

heatingscheduler_scpd = os.path.join(os.path.dirname(__file__), 'heatingscheduler_scpd.xml')

class HeatingScheduler(Service):
    def __init__(self, programs):
        super(HeatingScheduler, self).__init__('relay',
            'urn:schemas-home-lan:device:HeatingScheduler:1',
            scpd_xml_filepath=heatingscheduler_scpd)
        self.programs = programs

    def __get_program(self, ProgramId):
        if ProgramId in self.programs.programs:
            return self.programs.programs[ProgramId]
        else:
            raise ErrorCode(600)

    def soap_GetPrograms(self, *args, **kwargs):
        return {'Results':self.programs.to_xml()}

    def soap_NewProgram(self, *args, **kwargs):
        p = Program(kwargs['Name'])
        self.programs.add_program(p)
        return {'ProgramId':p.id}

    def soap_DeleteProgram(self, *args, **kwargs):
        try:
            self.programs.remove_program(kwargs['ProgramId'])
        except ProgramActiveError:
            raise ErrorCode(800) # ProgramId is current active
        except KeyError:
            raise ErrorCode(600)
        return {}

    def soap_SetSelectedProgram(self, *args, **kwargs):
        try:
            ProgramId = kwargs['ProgramId']
            self.programs.set_active_program(ProgramId)
            self.set_state_variable('SelectedProgram', ProgramId)
        except KeyError:
            raise ErrorCode(600)
        return {}

    def soap_GetSelectedProgram(self, *args, **kwargs):
        if self.programs.active_program:
            id = self.programs.active_program.id
        else:
            id = ''
        return {'ProgramId':id}

    def soap_GetPeriods(self, *args, **kwargs):
        program = self.__get_program(kwargs['ProgramId'])
        return {'Result':program.to_xml()}

    def soap_AddPeriod(self, *args, **kwargs):
        period = Period.from_xml(kwargs['Period'])
        period.id = None # Ensure we allocate a new period
        ProgramId = kwargs['ProgramId']
        try:
            self.programs.add_period(ProgramId, period)
        except KeyError:
            raise ErrorCode(600)
        except OverlapError:
            raise ErrorCode(600)

        return {'PeriodId':period.id}

    def soap_RemovePeriod(self, *args, **kwargs):
        PeriodId = kwargs['PeriodId']
        try:
            self.programs.remove_period(PeriodId)
        except KeyError:
            raise ErrorCode(600)
        return {}



class HeatingController(Device):
    def __init__(self, programs):
        super(HeatingController,self).__init__('urn:schemas-home-lan:device:HeatingController:1', gethostname())
        self += HeatingScheduler(programs)
