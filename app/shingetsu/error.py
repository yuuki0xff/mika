
class ShingetsuException(Exception): pass

class BadFileNameException(ShingetsuException): pass
class BadRecordException(ShingetsuException): pass
class BadTimeRange(ShingetsuException): pass
