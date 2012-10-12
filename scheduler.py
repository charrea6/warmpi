from brisa.core.reactors._select import SelectReactor
import datetime
reactor = SelectReactor()

from schedule.program import Programs, Period
from schedule.upnp import HeatingController
from relayctrl.client import LocalClient

def total_seconds(td):
    return (td.microseconds / 10.0**6) + (td.seconds + td.days * 24 * 3600)

class Scheduler(object):
    def __init__(self, path):
        self.current_periods = {}
        self.active_periods = {}
        self.relay = LocalClient()
        self.timer = None
        self.programs = Programs(path, self.programs_updated)


    def programs_updated(self, programs, reason, arg):
        print 'Programs Updated:', reason
        self.programs = programs
        if self.programs.active_program is not None:
            self.load_periods()


    def load_periods(self):
        today = datetime.datetime.today().weekday()
        periods = self.programs.active_program.get_periods_for_day(today)
        self.current_periods = {}
        for period in periods:
            sys_periods = self.current_periods.get(period.system, None)
            if sys_periods is None:
                self.current_periods[period.system] = [period]
            else:
                sys_periods.append(period)

        for system, periods in self.current_periods.items():
            periods.sort(lambda x,y: cmp(x.start, y.start))

        self.evaluate_periods()

    def evaluate_periods(self):
        print 'Evaluate periods'

        systems = {'HW': self.evaluate_hw, 'CH':self.evaluate_ch}
        new_periods = {}
        now = datetime.datetime.now()
        now_time = now.time()
        next_start_stop = datetime.time.max
        for periods in self.current_periods.values():
            for period in periods:
                if now_time >= period.start and now_time < period.end:
                    new_periods[period.system] = period
                    if period.end < next_start_stop:
                        next_start_stop = period.end
                else:
                    if now_time < period.start and period.start < next_start_stop:
                        next_start_stop = period.start
        try:
            for system,evaluate in systems.items():
                active = self.active_periods.get(system, None)
                next = new_periods.get(system, None)
                if active != next:
                    evaluate(active, next)
        except:
            import traceback
            traceback.print_exc()

        self.active_periods = new_periods

        if next_start_stop == datetime.time.max:
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow =  midnight + datetime.timedelta(days=1)
            diff = total_seconds(tomorrow - now)
            print 'Sleeping %f seconds until midnight, now %r' % (diff, now)
            self.sleep_util(tomorrow, self.load_periods)
        else:
            next_dt = now.replace(hour=next_start_stop.hour, minute=next_start_stop.minute, second=0, microsecond=0)
            diff = total_seconds(next_dt - now)
            print 'Sleeping %f seconds until next event, now %r next %r %r' % (diff, now, next_dt, datetime.datetime.now())
            self.sleep_util(next_dt, self.evaluate_periods)

    def sleep_util(self, dt_util, cb):
        self.__sleep_info = (dt_util, cb)
        self.__sleep_again()

    def __sleep_again(self):
        if self.timer is not None:
            reactor.rem_timer(self.timer)

        dt_util, cb = self.__sleep_info
        diff = total_seconds(dt_util - datetime.datetime.now())
        if diff > 60.0:
            self.timer = reactor.add_timer(diff / 2.0, self.__sleep_again)
        else:
            self.timer = reactor.add_timer(diff, cb)
        
    def evaluate_hw(self, previous_period, next_period):
        if previous_period is None:
            msg = 'ON  +'
            self.relay.set_state('HW', True)
        else:
            msg = 'OFF -'
            self.relay.set_state('HW', False)
        print '%s : Turning Hot Water %s' % (datetime.datetime.now().ctime(), msg)

    def evaluate_ch(self, previous_period, next_period):
        if previous_period is None:
            msg = 'ON  +'
            self.relay.set_state('CH', True)
        else:
            msg = 'OFF -'
            self.relay.set_state('CH', False)

        print '%s : Turning Central Heating %s' % (datetime.datetime.now().ctime(), msg)


if __name__ == '__main__':
    scheduler = Scheduler('programs.xml')
    device = HeatingController(scheduler.programs)
    device.start()
    reactor.add_after_stop_func(device.stop)
    reactor.main()

