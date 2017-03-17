
import pandas as pd
import argparse
from time import gmtime
import numpy as np

"""
        Helper Functions
"""
def pi2room(pi):
    rooms = {
            'pi01': 'Housewarming Bar',
            'pi02': 'Housewarming Bar',
            'pi03': 'VIP Bar',
            'pi04': 'BlackBox',
            'pi05': 'BlackBox',
            'pi06': 'BlackBox',
            'pi07': 'BlackBox',
            'pi08': 'Attrium',
            'pi09': 'Attrium',
            'pi10': 'Attrium',
            'pi11': 'Attrium',
            'pi12': 'Attrium',
            'pi13': 'Attrium',
            'pi14': 'Attrium',
            'pi15': 'Attrium',
            'pi16': 'Hall',
            'pi17': 'Dinner',
            'pi18': 'Dinner',
            'pi19': 'Dinner',
            'pi20': 'Dinner',
            'pi21': 'Dinner',
            'pi22': 'Reception',
            'pi23': 'Overdrive',
            'pi24': 'Overdrive',
            'Out': 'Out'

            }
    if pi in rooms:
        return rooms[pi]
    else:
        return None


def time2day(ts):
    return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][gmtime(ts).tm_wday]


def hourofday(ts):
    # in amsterdam time
    return int(gmtime(ts).tm_hour)+2

def calculate_deltas(timestampserie):
    ts = np.array(timestampserie)
    deltas = ts[1:] - ts[:-1]
    return np.concatenate(([np.nan], deltas))

# This function insert rows that set the position of a sensor 'Out' of the venue when TIMEOUT seconds passed
def insert_timeouts(df):
    TIMEOUT = 10*60
    def set_next(timestampserie):
        ts = np.array(timestampserie)
        deltas = ts[1:] - ts[:-1]
        return np.concatenate((deltas, [np.inf]))


    df.loc[:,'next'] = df.groupby('sensorid')['timestamp'].transform(set_next)
    df_tos = df[(df['next'] > TIMEOUT)]
    df_tos.loc[:,'timestamp'] += TIMEOUT
    df_tos.loc[:,'pi'] = 'Out'
    return df.append(df_tos, ignore_index=True)


"""
    Main function
"""
def main(inputf, outputf, start_hour, crowd=True, clustering=True, statistics=True, blemodel=True, timebetweenpackets=True):
    print 'Loading CSV'
    blepackets = pd.read_csv(inputf)
    print 'Pandas DF created'

    # Filter interesting hours of the event
    blepackets['timestamp'] = blepackets['timestamp'].astype(float)
    blepackets['hour'] = blepackets['timestamp'].apply(hourofday)
    blepackets = blepackets[blepackets['hour'] >= start_hour]
    print 'DF filtered'

    # Create extra columns with interesting values
    blepackets['minute'] = blepackets['timestamp'].apply(lambda x: int(round(x/60)))
    blepackets['day'] = blepackets['timestamp'].apply(time2day)
    blepackets['delta'] = blepackets.groupby(['sensorid'])['timestamp'].transform(calculate_deltas)
    blepackets['duplicate_type'] = blepackets['delta'].apply(lambda x: 0 if x > 0.1 else 1)
    print 'DF parsed'

    # Write data for BLE model section
    if blemodel:
        counter = blepackets.groupby(['pi','rssi']).count().rename(columns={'sensorid': 'count'})
        counter.loc[:,['count']].to_csv(outputf+'BLEModel.csv')
        print 'BLEModel data writtern'

    # Write data for statistics per minute
    if statistics:
        aggregations = {
            'bytes': 'sum',
            'uniq_packets': 'sum',
            'packets': 'count'
        }
        blepackets['uniq_packets'] = blepackets['duplicate_type'].apply(lambda x: 0 if x else 1)
        blepackets['packets'] = 1
        blepackets['bytes'] = blepackets['payload_length']
        blepackets.groupby(['day','minute', 'sensorid', 'type', 'pi']).agg(aggregations).reset_index().loc[:,['day', 'minute', 'sensorid', 'type', 'pi', 'packets','uniq_packets','bytes']].to_csv(outputf+'/StatisticsPerMinute.csv')
        print 'StatisticsPerMinute data written'


    # Filter noise and duplicates
    blepackets = blepackets[((blepackets['duplicate_type'] == 0) & ((blepackets['type'] == 'estimote-iBeacon') | (blepackets['type'] == 'estimote-nearable') | (blepackets['type'] == 'sensortag')))]
    if timebetweenpackets:
        blepackets.reset_index().loc[:,['day','type', 'sensorid', 'timestamp', 'delta']].to_csv(outputf+'/TimeBetweenPackets.csv')
        print 'TimeBetweenPackets data written'


    # Prepare some metrics for clustering and crowd movement outputs
    if crowd or clustering:
        blepackets = blepackets.loc[:, ['day', 'timestamp', 'type','sensorid', 'pi']]
        # Insert timeout records if we haven't seen somebody
        blepackets = insert_timeouts(blepackets).sort_values('timestamp')
        # Set room from PI
        blepackets['room'] = blepackets['pi'].apply(pi2room)

        # Write clustering output
        if clustering:
            blepackets[blepackets['type'] == 'sensortag'].reset_index().loc[:,['day','timestamp', 'sensorid', 'pi', 'room']].to_csv(outputf+'/FoRClustering.csv')
            print 'FoRClustering Data Written'

        # Write output for Crowd Movement
        if crowd:
            blepackets['guest_type'] = blepackets['type'].apply(lambda x: 'FoR' if x == 'sensortag' else 'VIP')
            blepackets.rename(columns={'timestamp': 'time'}).reset_index().loc[:,['day','time', 'guest_type', 'sensorid', 'room']].to_csv(outputf+'/CrowdMovement.csv')
            print 'CrowdMovement Data written'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Read ADE2016 dataset (CSV) and generate outputs (CSVs) for analysis: CSV with unique messages, CSV of packets per minute per sensor')
    parser.add_argument('-i', dest='inputf', help='Input file containing packet data from the ADE2016 dataset', required=True)
    parser.add_argument('-o', dest='outputf', help='Output folder to store new datasets', default='./')
    parser.add_argument('--start_hour', dest='start_hour', help='Starting hour for analysis in Amsterdam time (e.g. 16 is 16:00 or 4pm). Minimum value is 9', type=int, default=16)
    parser.add_argument('--no_crowd', dest='crowd', help='Skip Crowd Movement output', action='store_false')
    parser.add_argument('--no_clustering', dest='clustering', help='Skip FoR Clustering output', action='store_false')
    parser.add_argument('--no_statistics', dest='statistics', help='Skip Statistics per Minute', action='store_false')
    parser.add_argument('--no_blemodel', dest='blemodel', help='Skip BLE Model', action='store_false')
    parser.add_argument('--no_timebetweenpackets', dest='timebetweenpackets', help='Skip Time Between Packets', action='store_false')

    args = parser.parse_args()
    # args
    df = main(**vars(args))
