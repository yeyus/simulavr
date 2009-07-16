# -*- coding: UTF-8 -*-
# Python test script as demonstration of using pysimulavr in unit tests

from unittest import TestSuite, TextTestRunner, TestCase, defaultTestLoader
import pysimulavr

class SimulavrAdapter(object):
  
  DEFAULT_CLOCK_SETTING = 250 # 250ns or 4MHz
  
  def loadDevice(self, t, e):
    self.__sc = pysimulavr.SystemClock.Instance()
    self.__sc.ResetClock()
    dev = pysimulavr.AvrFactory.instance().makeDevice(t)
    dev.Load(e)
    dev.SetClockFreq(self.DEFAULT_CLOCK_SETTING)
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
    
class TestBaseClass(TestCase, SimulavrAdapter):
  
  def setUp(self):
    self.device = self.loadDevice("atmega128", "example.elf")
    
  def tearDown(self):
    del self.device
    
  def test_01(self):
    "just run 3000 ns + 250 ns"
    n = 3000
    self.doRun(n)
    self.assertEqual(self.getCurrentTime(), n)
    self.doStep()
    self.assertEqual(self.getCurrentTime(), n + self.device.GetClockFreq())
    
  def test_02(self):
    "just run 2 steps"
    self.doStep()
    self.assertEqual(self.getCurrentTime(), 0)
    self.doStep()
    self.assertEqual(self.getCurrentTime(), self.device.GetClockFreq())
    
  def test_03(self):
    "check PC and PC size"
    self.assertEqual(self.device.PC_size, 2)
    self.doStep()
    self.doStep()
    self.assertEqual(self.device.PC, 0x8c / 2)
    
  def test_04(self):
    "check flash and data symbols"
    self.assertEqual(self.device.Flash.GetAddressAtSymbol("main"), 0xfc / 2)
    self.assertEqual(self.device.data.GetAddressAtSymbol("timer2_ticks"), 0x100)
    
  def addr2word(self, addr):
    d1 = self.device.getRWMem(addr + 1)
    d2 = self.device.getRWMem(addr)
    return d2 + (d1 << 8)
    
  def test_05(self):
    "access to data by symbol"
    addr = self.device.data.GetAddressAtSymbol("timer2_ticks")
    o = 10000
    self.doRun(o)
    self.assertEqual(self.addr2word(addr), 0)
    self.doRun(2000000 + o)
    self.assertEqual(self.addr2word(addr), 1)
    self.doRun((2000000 * 3) + o)
    self.assertEqual(self.addr2word(addr), 3)
    
  def test_06(self):
    "write access to data by symbol"
    addr = self.device.data.GetAddressAtSymbol("timer2_ticks")
    o = 10000
    self.doRun(o)
    self.assertEqual(self.addr2word(addr), 0)
    self.device.setRWMem(addr, 2)
    self.doRun(1000000 + o)
    self.assertEqual(self.addr2word(addr), 2)
    self.doRun(2000000 + o)
    self.assertEqual(self.addr2word(addr), 3)
    
  def test_07(self):
    "test toggle output pin"
    o = 17000
    self.assertEqual(self.device.GetPin("A0").toChar(), "t")
    self.doRun(o)
    # now output should be set to LOW
    self.assertEqual(self.device.GetPin("A0").toChar(), "L")
    self.doRun(10100000 + o)
    self.assertEqual(self.device.GetPin("A0").toChar(), "H")
    self.doRun(20100000 + o)
    self.assertEqual(self.device.GetPin("A0").toChar(), "L")
    
  def test_08(self):
    "work with breakpoints"
    bpaddr = self.device.Flash.GetAddressAtSymbol("main")
    self.device.BP.AddBreakpoint(bpaddr)
    self.doRun(10000)
    self.assertEqual(self.device.PC, 0xc2 / 2)
    self.doStep(4) # call to main
    self.assertEqual(self.device.PC, bpaddr)
    self.doStep(4) # 4 steps more, do nothing because of breakpoint
    self.assertEqual(self.device.PC, bpaddr)
    self.device.BP.RemoveBreakpoint(bpaddr)
    self.doStep(2) # push needs 2 steps
    self.assertEqual(self.device.PC, bpaddr + 1)
        
if __name__ == "__main__":
  
  allTestsFrom = defaultTestLoader.loadTestsFromTestCase
  suite = TestSuite()
  suite.addTests(allTestsFrom(TestBaseClass))
  TextTestRunner(verbosity = 2).run(suite)
  
# EOF