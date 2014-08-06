# Python Script
import pysimulavr, time

class SimulavrAdapter(object):
  
  DEFAULT_CLOCK_SETTING = 250 # 250ns or 4MHz

  def __init__(self, clock_period_ns = DEFAULT_CLOCK_SETTING):
    self.__clock_period_ns = clock_period_ns

  system_clock = property(lambda self: self.__sc)
  
  def loadDevice(self, t, e):
    self.__sc = pysimulavr.SystemClock.Instance()
    self.__sc.ResetClock()
    dev = pysimulavr.AvrFactory.instance().makeDevice(t)
    dev.Load(e)
    self.__elffile = e
    dev.SetClockFreq(self.__clock_period_ns)
    self.__sc.Add(dev)
    return dev
    
  def doRun(self, n):
    ct = self.__sc.GetCurrentTime
    while ct() < n:
      res = self.__sc.Step()
      if res is not 0: return res
    return 0
      
  def doStep(self, stepcount = 1):
    while stepcount > 0:
      res = self.__sc.Step()
      if res is not 0: return res
      stepcount -= 1
    return 0
    
  def getCurrentTime(self):
    return self.__sc.GetCurrentTime()
    
  def getAllRegisteredTraceValues(self):
    os = pysimulavr.ostringstream()
    pysimulavr.DumpManager.Instance().save(os)
    return filter(None, [i.strip() for i in os.str().split("\n")])

  def dmanSingleDeviceApplication(self):
    pysimulavr.DumpManager.Instance().SetSingleDeviceApp()
    
  def dmanStart(self):
    pysimulavr.DumpManager.Instance().start()
  
  def dmanStop(self):
    pysimulavr.DumpManager.Instance().stopApplication()
  
  def setVCDDump(self, vcdname, signals, rstrobe = False, wstrobe = False):
    dman = pysimulavr.DumpManager.Instance()
    sigs = ["+ " + i for i in signals]
    dman.addDumpVCD(vcdname, "\n".join(sigs), "ns", rstrobe, wstrobe)
    
  def getWordByName(self, dev, label):
    addr = dev.data.GetAddressAtSymbol(label)
    v = dev.getRWMem(addr)
    addr += 1
    v = (dev.getRWMem(addr) << 8) + v
    return v
  
  def enableGdb(self, dev, gdb_port = 1212):
    #TODO This is similar to the implementation in simulavr.tcl, but it
    #     doesn't work. I think we have to remove the device from the
    #     system clock, so GdbServer can decide whether it calls CpuCycle
    #     or not. As we cannot remove it, we have to avoid adding it
    #     in the first place.
    gdb = self.__gdb = pysimulavr.GdbServer(dev, gdb_port, False, True)
    self.__sc.Add(gdb)
    with open("avr-gdb-cmds", "w") as f:
      f.write("file %s\n" % self.__elffile)
      f.write("target remote localhost:%d\n" % gdb_port)
      f.write("break main")
    print "Run gdb: avr-gdb --command avr-gdb-cmds"
    time.sleep(1)

  def enableTrace(self, dev, trace_file, max_lines = 1000000):
    pysimulavr.cvar.sysConHandler.SetTraceFile(trace_file, max_lines)
    dev.trace_on = True

# EOF
