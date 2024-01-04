#
# Use MFRC522 lib from https://github.com/danjperron/micropython-mfrc522
#
#

from machine import Pin
from mfrc522 import MFRC522
from RfidAccess import RfidAccess
import utime
import sys

MIN_BUT_SET_TIME    =  500                                           # time between but events in ms

iButton   = Pin(16, Pin.IN, Pin.PULL_UP)                             # Press button
iLed      = Pin(25, Pin.OUT)                                         # On-board LED

iSck      =  6                                                       # SPI SCK signal
iCopi     =  7                                                       # SPI Controller out, peripheral in
iCipo     =  4                                                       # SPI Controller in, peripheral out
iSda      =  5                                                       # SPI SDA signal aka CS here
iRst      = 22                                                       # RST signal

zReader   = MFRC522(spi_id = 0, sck = iSck, miso = iCipo, mosi = iCopi, cs = iSda, rst = iRst)
zAccess   = RfidAccess()
zLastCard = [0]                                                      # Last seen card

def checksum(data):
    crc = 0xc7
    for byte in data:
        crc ^= byte
        for _ in range(8):
            msb = crc & 0x80
            crc = (crc << 1) & 0xff
            if msb:
                crc ^= 0x1d
    return crc

def eraseTag(zUid):
  pass

def createTag(zUid):
  pass

def writeTag(zUid):
  """ 
      Use EraseNdefTag.py in case of problem
      !!! CreateNdefTag.py doesn't work
  """ 
  global zReader
  global zAccess
  
# create tag and then erase (make a blank) tag

  zDefaultKey     = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
  zFirstSectorKey = [0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5]
  zNextSectorKey  = [0xD3, 0xF7, 0xD3, 0xF7, 0xD3, 0xF7]
  #set MAD sector
  zAccess.decodeAccess(0xFF, 0x07, 0x80)
  zBlock3 = zAccess.fillBlock3(keyA = zFirstSectorKey, keyB = zDefaultKey)
  #Write the sector zAccess
  if zReader.writeSectorBlock(zUid, 0, 3, zBlock3, keyB = zDefaultKey) == zReader.ERR:
    print("Writing MAD sector failed!")
  else:
    zDataBlock = 16 * [0]                                            # Dummy data
    zReader.writeSectorBlock(zUid, 0, 1, zDataBlock, keyB = zDefaultKey)
    zReader.writeSectorBlock(zUid, 0, 2, zDataBlock, keyB = zDefaultKey)
    for iSector in range(1, 16):                                     # Write all next sectors zAccess
      zReader.writeSectorBlock(zUid, iSector, 3, zBlock3, keyB = zDefaultKey) #? Can the payload be changed?
      for iBlock in range(3):
        zDataBlock[1] = iSector * iBlock + 1                         # Test to change data
        zReader.writeSectorBlock(zUid, iSector, iBlock, zDataBlock, keyB = zDefaultKey)
      print(".", end = "")
  print('\n\tCard written.\n')
  zReader.MFRC522_DumpClassic1K(zUid, Start = 0, End = 64, keyB = zDefaultKey)


def readTag(zUid):
  """
      Read the card tag and display it.
      The card shall stay close to the reader while dumping otherwise and error is raised
  """
  global zReader

  zDefaultKey     = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
  zReader.MFRC522_DumpClassic1K(zUid, Start = 0, End = 64, keyB = zDefaultKey)
  print("Done")

def getTag():
  """
      Read the card tag and UID if there is one close.
      Display the metadata of the card (tag and UID)
  """
  global zLastCard
  global zReader
  iStatus = zReader.NOTAGERR
  zUid    = None

  try:
    zReader.init()
    (iStatus, iTag_type) = zReader.request(zReader.REQIDL)
    if iStatus == zReader.OK:
      (iStatus, zUid) = zReader.SelectTagSN()
      if zLastCard != zUid and zUid != []:
        print('Tag type: ', iTag_type)
        print("Card detected {}  UID = {}".format(hex(int.from_bytes(bytes(zUid),
                                                  "little", False)).upper(),
                                                  zReader.tohexstring(zUid)))
    else:
      zLastCard = [0]                                                # If not continous signal, reset the UID
    return(iStatus, zUid)
  except KeyboardInterrupt:
    print('\nBye.')
    sys.exit(1)                                                      # Stops and exit the application

def run_app():
  """
      Main loop of the application, check the card and button status.
  """
  global zLastCard
  iLastButSet = 0                                                    # Time of the last action on the button

  print("\nPlease place card on Reader\n")
  iLed.off()
  while True:
    (iStatus, zUid) = getTag()
    if(iButton.value() == 0):                                        # Write but pressed
      iLed.on()                                                      # Turn the LED on
      if ((utime.ticks_us() - iLastButSet) > MIN_BUT_SET_TIME):
        iLastButSet = utime.ticks_us()
        if iStatus == zReader.OK:
          if zLastCard != zUid:
            writeTag(zUid)
            zLastCard = zUid                                         # Update last Card UID
    else:
      iLed.off()                                                     # Button not pressed, turn the LED off
      if iStatus == zReader.OK:
        if zLastCard != zUid:
          readTag(zUid)
          zLastCard = zUid                                           # Update last Card UID
    utime.sleep_ms(50)                                               # Slow down the loop in ms

if __name__ == "__main__":
  run_app()
