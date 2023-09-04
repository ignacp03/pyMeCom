
import struct
from .mecom import MeCom

class LT_download_manager():
    def __init__(self, filepath, session):
        self.path = filepath
        self.LUT_MAX_FLOAT_COUNT = 16300
        self.LUT_MAX_INST = 4
        self.session = session

    def download_table(self):
        """
        Does the whole sequence
        """
        LutByteData, LutByteLength = self.LUT_OpenCSVFile()
        execution = self.LUT_DownloadManager(LutByteData,LutByteLength) 
        return execution   
    
    def LUT_OpenCSVFile(self):
        """
        Opens, checks and stores the CSV file inputs as float
        """
        nrOfColumns = 0
        columns = []
        sr = None

        # Check if OpenFileDialog result is OK
        fData = [[0.0] * self.LUT_MAX_FLOAT_COUNT for _ in range(self.LUT_MAX_INST)]
        fLength = [-1] * self.LUT_MAX_INST
        detectedTableInstances = [0] * self.LUT_MAX_INST

        try:
            sr = open(self.path, 'r')
            
            # Read First Line and do some pre-checks
            line = sr.readline().strip()
            columns = line.split(';')
            nrOfColumns = len(columns)

            # Check the Table header
            if nrOfColumns < 2:
                raise LookupError("The CSV file must have at least 2 columns. One 'Table Instance' column and 1-4 Data columns.")
                
            if nrOfColumns > self.LUT_MAX_INST + 1:
                raise LookupError(f"The CSV file is limited to a maximum of {self.LUT_MAX_INST} columns. One 'Table Instance' column and 1-4 Data columns.")
                return
            if columns[0] != "Table Instance":
                raise LookupError("The name of the A1 Cell must be 'Table Instance'.")
                return

            # Check if the header contains nothing else than 1-4, every number should only once be there
            for inst in range(1, self.LUT_MAX_INST + 1):
                detectedTableInstances[self.InstToAdr(inst)] = -1
            for i in range(1, nrOfColumns):
                try:
                    tableInstance = int(columns[i])
                except ValueError:
                    raise LookupError("The 'Table Instance' must be a number.")
                    return
                if tableInstance < 1 or tableInstance > self.LUT_MAX_INST:
                    raise LookupError(f"The 'Table Instance' must be between 1-{self.LUT_MAX_INST}.")
                    return
                for i2 in range(1, nrOfColumns):
                    if detectedTableInstances[i2 - 1] == tableInstance:
                        raise LookupError("The 'Table Instance' number must be different.")
                        return
                detectedTableInstances[i - 1] = tableInstance

            # Read the Float values
            for i in range(self.LUT_MAX_INST):
                fLength[i] = -1
            valueIndex = 0

            for line in sr:
                line = line.strip()
                columns = line.split(';')
                if len(columns) != nrOfColumns:
                    raise LookupError("Some rows do not contain the same number of columns as the header does.")
                    return

                for columnIndex in range(1, nrOfColumns):
                    if fLength[self.InstToAdr(detectedTableInstances[columnIndex - 1])] == -1:
                        # End of this column not yet reached
                        try:
                            fData[self.InstToAdr(detectedTableInstances[columnIndex - 1])][valueIndex] = float(columns[columnIndex])
                        except ValueError:
                            # Could not convert the column value to a float, assume the last value was the end of this column
                            fLength[self.InstToAdr(detectedTableInstances[columnIndex - 1])] = valueIndex
                    else:
                        # End of the Table already reached, check if no more data is here
                        if len(columns[columnIndex]) != 0:
                            raise LookupError(f"Row {valueIndex + 2}; Column {columnIndex + 1}: Contains a non-empty field under a field that could not be converted to a floating point value.")
                            return
                valueIndex += 1
                if valueIndex > self.LUT_MAX_FLOAT_COUNT:
                    raise LookupError(f"The maximum allowed values is {self.LUT_MAX_FLOAT_COUNT}.")
                    return

            # Set the lengths of the tables that have still data on this last row
            for columnIndex in range(1, nrOfColumns):
                if fLength[self.InstToAdr(detectedTableInstances[columnIndex - 1])] == -1:
                    fLength[self.InstToAdr(detectedTableInstances[columnIndex - 1])] = valueIndex
        except Exception as e:
            print("CSV File read Error!")
            raise LookupError(str(e))
            
            return
        finally:
            if sr is not None:
                sr.close()

        # Define the LutByteLength list to store table lengths
        LutByteLength = [0] * self.LUT_MAX_INST
        LUT_HEADER_SIZE = 12
        # Define LutByteData as a multi-dimensional list
        LutByteData = [[0.0] * (self.LUT_MAX_FLOAT_COUNT*4 + 12) for _ in range(self.LUT_MAX_INST)] 
        
        # Prepare the data for all 4 Tables if the table was defined
        for tableInst in range(1, self.LUT_MAX_INST + 1):
            LutByteLength[self.InstToAdr(tableInst)] = 0
            if fLength[self.InstToAdr(tableInst)] == -1:
                continue  # Table is not defined
            if fLength[self.InstToAdr(tableInst)] < 2:
                raise LookupError("The minimum allowed values / table is 2!")
                return

            # Add the static Fields
            LutByteLength[self.InstToAdr(tableInst)] = (fLength[self.InstToAdr(tableInst)] * 4) + 12
            tableType = 0
            LutByteData[self.InstToAdr(tableInst)][4:8] = LutByteLength[self.InstToAdr(tableInst)].to_bytes(4, 'little')
            LutByteData[self.InstToAdr(tableInst)][8:12] = tableType.to_bytes(4, 'little')

            # Add the data
            for i in range(fLength[self.InstToAdr(tableInst)]):
                float_bytes = struct.pack("<f", fData[self.InstToAdr(tableInst)][i])
                LutByteData[self.InstToAdr(tableInst)][12 + i * 4:16 + i * 4:] = float_bytes

            # Calculate and add the CRC (exclude the first 4 bytes, because this is the place for the CRC)
            crc = self.LUT_CalcCrcOfByteArray(LutByteData[self.InstToAdr(tableInst)][4:], LutByteLength[self.InstToAdr(tableInst)] - 4)
            LutByteData[self.InstToAdr(tableInst)][0:4] = crc.to_bytes(4, 'little')

        print("Lookup Table loaded successfully.")
        return LutByteData, LutByteLength 
    
    def LUT_DownloadManager(self,LutByteData,LutByteLength):
        """
        Downloads the table in chunks of 256 bits
        """
        global status, byteOffset, tableInst, totalBytesToDownload, totalBytesDownloaded, cmd
        status = 0
        download_completed = False
        while download_completed is False:
            if status == 0:

                #progressBar_LUT_Download.Value = 0
                print( "Start downloading...")
                tableInst = 0
                #Computation of the total bytes
                totalBytesToDownload = 0
                totalBytesDownloaded = 0
                for inst in range(1, self.LUT_MAX_INST + 1):
                    if LutByteLength[self.InstToAdr(inst)] == 0:
                        continue
                    totalBytesToDownload += (((LutByteLength[self.InstToAdr(inst)] - 1) // 256) + 1) * 256
                    print(totalBytesToDownload)
                status = 1
            if status == 1:
                #check wether the table has data
                tableInst += 1
                if tableInst > self.LUT_MAX_INST:
                    #all tables downloaded, proceed to verification
                    cmd = 2
                    status = 3
                elif LutByteLength[self.InstToAdr(tableInst)] > 0:
                    #start downloading instance
                    byteOffset = 0
                    status = 2
            if status == 2:
                #Download the table instance
                print(f"Downloading table instance {tableInst}")
                queryResult = self.LUT_DownloadPage(cmd = 1, tableInst= tableInst, byteOffset= byteOffset, data = LutByteData[self.InstToAdr(tableInst)][byteOffset:])
                if queryResult == 3:
                    #if command received
                    byteOffset += 256 #update offset
                    totalBytesDownloaded += 256 #update bytes downloaded
                    progress = 95 * totalBytesDownloaded / totalBytesToDownload
                    if progress > 95:
                        progress = 95
                    if progress < 0:
                        progress = 0
                    print(progress, '%')
                    
                    if byteOffset >= LutByteLength[self.InstToAdr(tableInst)]:
                        #if offset greater than the length of the table instance, move to the following 
                        status = 1

                elif queryResult == 2:
                    print("Device is busy. Waiting...")
                elif queryResult == 0xFF:
                    print("Communication Timeout. Please Try again.")
                    #progressBar_LUT_Download.Value = 0
                    status = 0
                else:
                    print( f"Error. Unexpected Status({queryResult}). Please Try again.")
                    #progressBar_LUT_Download.Value = 0
                    status = 0

            if status == 3:
                #Verification

                queryResult = self.LUT_DownloadPage(cmd, 0, 0, None)
                queryResult = 0
                if queryResult == 0:
                    #progressBar_LUT_Download.Value = 100
                    print("Download Successful")
                    download_completed = True
                    status = 0
                elif queryResult == 2:
                    print("Device is busy. Waiting...")
                elif queryResult == 3:
                    print( "Verification is running...")
                    cmd = 0
                elif queryResult == 0xFF:
                    print("Communication Timeout. Please Try again.")
                    #progressBar_LUT_Download.Value = 0
                    status = 0
                else:
                    print( "Error. Tables not ok. Please Try again.")
                    #progressBar_LUT_Download.Value = 0
                    status = 0
        return download_completed

    def LUT_DownloadPage(self, data,cmd = 1 , tableInst=1, byteOffset=0 ):
        """
        Queries the command
        """
        #txBuffer = bytearray(600)
        #txBuffer[0] = ord('?')
        #txBuffer[1] = ord('T')
        #txBuffer[2] = ord('D')
        #txBuffer[3:5] = "{:02X}".format(cmd)
        txBuffer = ''
        txBuffer += '?TD'
        txBuffer += "{:02X}".format(cmd)
    
        if cmd == 1:
            #txBuffer[5:7] = "{:02X}".format(tableInst)
            txBuffer += "{:02X}".format(tableInst)
            #txBuffer[7:15] = "{:08X}".format(byteOffset)
            txBuffer += "{:08X}".format(byteOffset)

        
            for i in range(256):
                #txBuffer[15 + i * 2:17 + i * 2] = "{:02X}".format(data[i])
                txBuffer += "{:02X}".format(data[i])
        
            response = self.session.execute_lookup_table(txBuffer)  ## function to send the command
                #CommError()

        else:
            response = self.session.execute_lookup_table(txBuffer) #function to send the command
                #CommError()

        return response
    

    #Help functions

    def CRC32Calc(self,OldCRC, data_byte):
        """
        Computes the CRC32
        """
        crc = OldCRC ^ data_byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc >>= 1
        return crc & 0xFFFFFFFF
    
    def InstToAdr(self,tableInst):
        """ 
        Allows conversion from table instance to array index
        """
        # You can define your mapping logic here
        # For example, if table instances start from 1, you can subtract 1 to get the index.
        return tableInst - 1
    
    def LUT_CalcCrcOfByteArray(self,data, length):
        """
        Computes the CRC of a Byte array
        """
        OldCRC = 0xFFFFFFFF
        for i in range(length):
            OldCRC = self.CRC32Calc(OldCRC, data[i])
        return OldCRC
    