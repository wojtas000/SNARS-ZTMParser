import re
import pandas as pd

class ZTMParser:

    def __init__(self, file_path):
        '''
        Initializes the object by reading the .TXT file and extracting the relevant information about ZTM communication architecture.
        '''

        with open(file_path, 'r') as file:
            self.content = file.read()
            self.station_groups = self.extract_station_groups()
            self.stations = self.extract_stations()
            self.bus_lines = self.extract_bus_lines()
            self.transport_lines_variants = self.extract_transport_line_numbers_and_types()

    def extract_station_groups(self):
        '''
        Extracts station groups from the file.
        Returns: pandas dataframe with columns: ID, Name, City Code, City Name
        '''

        match = re.search(r'\*ZA (\d+)(.*?)#ZA', self.content, re.DOTALL)
        num_records = int(match.group(1))
        section_content = match.group(2).strip().split('\n')

        # Initialize lists to store data
        ids, names, city_codes, city_names = [], [], [], []

        # Extract information from each line in the section
        for line in section_content:
            # delete spaces at the beginning and end of the line
            line = line.strip()
            parts = re.split(r'\s{3,}|,\s*|\s{2,}', line, maxsplit=3)
            if len(parts) >= 4:
                ids.append(parts[0])
                names.append(parts[1])
                city_codes.append(parts[2])
                city_names.append(parts[3])

        # Create a pandas dataframe
        data = {'ID': ids, 'Name': names, 'City Code': city_codes, 'City Name': city_names}
        df = pd.DataFrame(data)

        return df
    
    def extract_stations(self):
        '''
        Extracts stations from the file 
        Returns: pandas dataframe with columns: Group_ID, ID, Street, Destination, Y and X coordinates.
        '''

        data = []
        zp_match = re.search(r'\*ZP (\d+)(.*?)#ZP', self.content, re.DOTALL)
        zp_section_content = zp_match.group(2).strip().split('\n')

        for line in zp_section_content:
            # if stripped line starts with 6 digit ID
            if re.match(r'\d{6}', line.strip()):
                # split line when there are 3 or more spaces
                parts = re.split(r'\s{3,}', line.strip(), maxsplit=6)
                group_id = parts[0][:-2]
                id = parts[0]
                street = parts[2].replace('Ul./Pl.: ', '').strip()
                destination = parts[3].replace('Kier.: ', '').strip()
                y_coord = re.search(r'(\d+(\.\d*)?)', parts[4]).group(1) if re.search(r'(\d+(\.\d*)?)', parts[4]) else None
                x_coord = re.search(r'(\d+(\.\d*)?)', parts[5]).group(1) if re.search(r'(\d+(\.\d*)?)', parts[5]) else None
                data.append({'Group_ID': group_id, 'ID': id, 'Street': street, 'Destination': destination, 'Y': y_coord, 'X': x_coord})
            else:
                continue

        df = pd.DataFrame(data)
        return df
    
    def extract_bus_lines(self):
        '''
        Extracts bus lines from the file and returns a dictionary of pandas dataframes.
        Each dataframe represents a single bus line and is indexed by station number in correct order.

        Returns: dictionary of pandas dataframes with columns: ID, Name
        '''
        ll_match = re.search(r'\*LL (\d+)(.*?)#LL', self.content, re.DOTALL)
        ll_section_content = ll_match.group(2).strip().split('\n')

        bus_lines_dict = {}

        lw_matches = re.findall(r'\*LW(.*?)#LW', ll_match.group(2), re.DOTALL)
        for i, lw_section in enumerate(lw_matches):
            station_ids = []
            station_name = []
            for line in lw_section.split('\n'):
                match = re.search(r'r (\d{6})\s+(.+?),\s*--', line)
                if match:
                    station_ids.append(match.group(1))
                    station_name.append(match.group(2).strip())
            
            bus_lines_dict[i] = pd.DataFrame({'ID': station_ids, 'Name': station_name}, index=range(1, len(station_ids)+1))
          
        return bus_lines_dict

    def extract_transport_line_numbers_and_types(self):
        '''
        Extracts info about transport lines from the file and returns a pandas dataframe.
        Each row represents a single transport line (or its variant) and contains information about line number, variant number and type (BUS, TRAM, TRAIN).
        '''

        ll_match = re.search(r'\*LL (\d+)(.*?)#LL', self.content, re.DOTALL)
        ll_section_content = ll_match.group(2).strip().split('\n')
        line_names = []
        variants = []

        for line, next_line in zip(ll_section_content, ll_section_content[1:]):
            # get lines with beginning Linia: string
            if re.match(r'Linia:', line.strip()):
                
                line_name = line.strip()
                next_line = next_line.strip()
                number_of_variants = re.search(r'(\d+)', next_line).group(1)
                line_names += [line_name] * int(number_of_variants)
                variants += list(range(1, int(number_of_variants)+1))

        df = pd.DataFrame({ 'Line Name': line_names, 'Variant': variants})

        df['Line Number'] = df['Line Name'].apply(lambda x: '-'.join(x.split('-')[:-1]).strip())
        df['Line Name'] = df['Line Name'].apply(lambda x: x.split('-')[-1].strip())
        bus = ['LINIA ZWYKŁA', 'LINIA ZWYKŁA OKRESOWA', 'LINIA EKSPRESOWA', 'LINIA PRZYSPIESZONA', 'LINIA PRZYSPIESZONA OKRESOWA', 'LINIA STREFOWA', 'LINIA STREFOWA UZUPEŁNIAJĄCA', 'LINIA STREFOWA UZUPEŁNIAJĄCA', 'LINIA NOCNA', 'LINIA ZASTĘPCZA', 'LINIA SPECJALNA']
        tram = ['LINIA TRAMWAJOWA', 'LINIA TRAMWAJOWA UZUPEŁNIAJĄCA']
        train = ['LINIA KOLEI MIEJSKIEJ']
        df['Line Type'] = df['Line Name'].apply(lambda x: 'BUS' if x in bus else 'TRAM' if x in tram else 'TRAIN' if x in train else None)
        # drop Line Name column
        df.drop('Line Name', axis=1, inplace=True)

        return df

    def get_edges(self):
        '''
        Returns a list of tuples representing edges of the graph.
        Each tuple contains two station IDs.
        '''

        edges = []
        for line in self.bus_lines.values():
            for i in range(len(line)-1):
                edges.append((line.iloc[i]['ID'], line.iloc[i+1]['ID']))
        return edges
    
    def get_nodes(self):
        '''
        Returns a list of station IDs.
        '''

        return list(self.stations['ID'])
    
    def get_coordinates(self):
        '''
        Returns a dictionary of tuples representing coordinates of each station.
        '''

        # Convert 'X' and 'Y' columns to numeric values
        self.stations['X'] = pd.to_numeric(self.stations['X'], errors='coerce')
        self.stations['Y'] = pd.to_numeric(self.stations['Y'], errors='coerce')

        return dict(zip(self.stations['ID'], zip(self.stations['X'], self.stations['Y'])))
