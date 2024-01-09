#
# Use MFRC522 lib from https://github.com/danjperron/micropython-mfrc522
#
#

from machine import Pin
from mfrc522 import MFRC522
from RfidAccess import RfidAccess
from sys import stdin
import utime

APP_VERSION  = '1.0.0'
FORGET_TIME  =  5000                                                 # time to forget one command (in ms)
BLOCK_SIZE   = 16
MAX_BLOCKS   = 16

iLed      = Pin(25, Pin.OUT)                                         # On-board LED

iSck      =  6                                                       # SPI SCK signal
iCopi     =  7                                                       # SPI Controller out, peripheral in
iCipo     =  4                                                       # SPI Controller in, peripheral out
iSda      =  5                                                       # SPI SDA signal aka CS here
iRst      = 22                                                       # RST signal

zReader   = MFRC522(spi_id = 0, sck = iSck, miso = iCipo, mosi = iCopi, cs = iSda, rst = iRst)
zAccess   = RfidAccess()

def readData(zUid):
  """
      Read the card tag and display it.
      The card shall stay close to the reader while dumping otherwise and error is raised
  """
  global zReader

  zDefaultKey     = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
  zReader.MFRC522_DumpClassic1K(zUid, Start = 0, End = 64, keyB = zDefaultKey)

def writeData(zUid, szData):
  """ 
      Write new data on the card
      zUid is the ID of the card
      szData is the data in text format
  """ 
  global zReader
  global zAccess
  
  szWords = szData.split('#')
  #szWords = [szData[iInd : iInd + BLOCK_SIZE] for iInd in range(0, len(szData), BLOCK_SIZE)]
  iSize   = len(szWords)
  print('Data = {}, size = {}\n'.format(szWords, iSize))
  for iInd in range(0, iSize):
    szWords[iInd] = szWords[iInd] + ' ' * (BLOCK_SIZE - len(szWords[iInd]))    # Add empty spaces to fill the BLOCK_SIZE
    print(' Word[{}] = {},\t'.format(iInd, szWords[iInd]))

  if iSize > MAX_BLOCKS:
    print('Too many data, abording!\n')
    return
  
  zDefaultKey     = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]             # Set the keys
  zFirstSectorKey = [0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5]
  zNextSectorKey  = [0xD3, 0xF7, 0xD3, 0xF7, 0xD3, 0xF7]
  zAccess.decodeAccess(0xFF, 0x07, 0x80)
  zBlock3 = zAccess.fillBlock3(keyA = zFirstSectorKey, keyB = zDefaultKey)
  if zReader.writeSectorBlock(zUid, 0, 3, zBlock3, keyB = zDefaultKey) == zReader.ERR: 
    print("Writing MAD sector failed!")
  else:
    zDataBlock = 16 * [0]                                            # Dummy data
    zReader.writeSectorBlock(zUid, 0, 1, zDataBlock, keyB = zDefaultKey)
    zReader.writeSectorBlock(zUid, 0, 2, zDataBlock, keyB = zDefaultKey)
    iIndex = 0
    for iSector in range(1, 16):                                     # Write all next sectors zAccess
      zReader.writeSectorBlock(zUid, iSector, 3, zBlock3, keyB = zDefaultKey) #! Not change data here
      for iBlock in range(3):
        if iIndex < iSize:
          zDataBlock = bytearray(szWords[iIndex].encode('UTF-8'))      # Set the data to be written
          iIndex += 1
        else:
          zDataBlock = 16 * [0]
        zReader.writeSectorBlock(zUid, iSector, iBlock, zDataBlock, keyB = zDefaultKey)
#      print(".", end = "")
  print('\n\tCard written.\n')
#  zReader.MFRC522_DumpClassic1K(zUid, Start = 0, End = 64, keyB = zDefaultKey)


def getTag():
  """
      Read the card tag and UID if there is one close.
      Display the metadata of the card (tag and UID)
  """
  global zReader
  iStatus = zReader.NOTAGERR
  zUid    = None

  try:
    zReader.init()
    (iStatus, iTag_type) = zReader.request(zReader.REQIDL)
    if iStatus == zReader.OK:
      (iStatus, zUid) = zReader.SelectTagSN()
      if zUid != []:
        print('Tag = ', iTag_type)
        print("Card {}  UID = {}".format(hex(int.from_bytes(bytes(zUid),
                                         "little", False)).upper(),
                                         zReader.tohexstring(zUid)))
    return(iStatus, zUid)
  except KeyboardInterrupt:
    print('\nApplication ended.')
    sys.exit(1)                                                      # Stops and exit the application


def run_app():
  """
      Main loop of the application, check the card and button status.
  """
  
  print("\nApplication started\n")
  iLed.off()
  while True:
    szAction   = stdin.readline().strip()                            # wait for the client command
    iStatus    = zReader.NOTAGERR                                    # set the Status to not OK value
    iLastEvent = utime.ticks_ms()                                    # stamp the command time
    print('\n\tCommand = {}\n'.format(szAction))
    if szAction == '*IDN?':                                          # Identification process
      print('RFID_PRI Pico, Version {}\n'.format(APP_VERSION))
    if szAction == "READ":                                           # Read process
      while (iStatus != zReader.OK) and ((utime.ticks_ms() - iLastEvent) <= FORGET_TIME):
        (iStatus, zUid) = getTag()                                   # wait for the card to be available
      if iStatus == zReader.OK:
        readData(zUid)
      else:
        print('Tag = -1\n')                                          # No card available
    if szAction == "WRITE":                                          # Write process
      iLed.on()
      szData = stdin.readline().strip()                              # Read the data associated to the Write command
      while (iStatus != zReader.OK) and ((utime.ticks_ms() - iLastEvent) <= FORGET_TIME):
        (iStatus, zUid) = getTag()                                   # wait for the card to be available
      if iStatus == zReader.OK:
        writeData(zUid, szData)
      else:
        print('Tag = -1\n')                                          # No card available
      iLed.off()
    print("Done")                                                    # End message used by the client application


if __name__ == "__main__":
  run_app()
