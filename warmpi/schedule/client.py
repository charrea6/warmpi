import warmpi

class LocalClient(object):
    def __init__(self):
        self.conn = warmpi.get_client('schedule')

    def get_programs(self):
        return self.conn.call('get_programs')

    def get_program(self, program_id):
        return self.conn.call('get_program', program_id)

    def get_active_program(self):
        return self.conn.call('get_active_program')

    def set_active_program(self, program_id):
        self.conn.call('set_active_program', program_id)

    def remove_program(self, program_id):
        self.conn.call('remove_program', program_id)

    def add_program(self, program):
        return self.conn.call('add_program', program)

    def add_period(self, program_id, period):
        self.conn.call('add_period', program_id, period)

    def remove_period(self, period_id):
        self.conn.call('remove_period', period_id)

    def get_active_periods(self):
        return self.conn.call('get_active_periods')
