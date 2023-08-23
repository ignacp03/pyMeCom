
class Lookup_Table(object):
    """
    Allow senidng and downloading lookup tables
    """
    def __init__(self, fileloc):
        with open(fileloc) as f:
            self.file = [line.rstrip().split(';') for line in f]
        self.columns = len(self.file[0])
        assert self.columns <6 and self.columns >1, "Only up to 4 tables allowed. Table must have at least two columns"
        self.columns_length = []
        for column in range(self.columns-1):
            length = 0
            for row in self.file:
                if row[column+1] != '': length += 1
            self.columns_length.append([length-1])


    def file_police(self):
        """
        Check wether the file meets the requirements before being downloaded.
        """
        if self.columns >6 and self.columns <2:
            print("Only up to 4 tables allowed. Table must have at least two columns. Find", self.columns-1)
            return False
        
        #if self.rows > 16301:
         #   print("Only up to 16300 samples are allowed")
          #  return False
        
        if self.file[0][0] != 'Table Instance':
            print('First cell must be: Table Instance')
            return False
        
        headers = [str(header) for header in range(len(self.file[0]))]
        if headers[1:] != self.file[0][1:]:
            print('Headers must be the number of the table (1,2,3 or 4)')
            return False
        
        return True
        
    def extract_table_instances(self, table_instances:list):
        tables = []
        assert self.columns > len(table_instances), "There are not that many tables in the file"
        for t_instance in table_instances:
            table= []
            for m in self.file:
                if m[t_instance] != '': table.append(float(m[t_instance]))
            tables.append(table[1:])
            #now each row has the data from 1 table
        return tables


    def chunk_splitter(self,table):
        """
        Splits the table data in chunks of 256 bytes
        """
        table_splitted = []
        total_bytes = len(table)
        sub_lists = total_bytes// 256
        for list in range(sub_lists):
            table_splitted.append(table[list*256:(list+1)*256])
        table_splitted.append(table[sub_lists*256:])
        return table_splitted


