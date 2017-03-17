import argparse
# import seaborn as sns
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np

class Report:
    def __init__(self, outputf, mdfilename):
        self.outputf = outputf
        # Open output file
        self.mdfile = open(mdfilename, 'w+')
        self.print_line('# ADE2016 Dataset analysis (automatic) report')

    def print_line(self, text):
        self.mdfile.write(text+'\n\n')


    def print_figure(self, fig, name, description):
        # For paper
        fig.savefig('%s/%s.pdf' % (self.outputf, name), bbox_inches='tight')

        self.print_line('#### Figure: %s \n\n' % description)
        # For MD Report
        fig.savefig('%s/%s.png' % (self.outputf, name), bbox_inches='tight')
        self.print_line('![%s](./%s.png)\n\n' %(description, name))
        return


def TimeBetweenPackets(df, report):
    report.print_line('## Time between packets of the same type')
    #%% Aggregate delta times for days and sensor types
    df = df[(df['delta'] > 1) & ((df['type']=='sensortag') | (df['type'] == 'estimote-nearable'))]

    gdf = df.groupby(['day', 'type'])['delta'].apply(sorted)
    fig = plt.figure()
    legends = []
    colors=plt.cm.viridis(np.linspace(0,1,4))
    message = ''
    ic = 0
    for i in gdf.index:
        legends.append(i)
        data = sorted(gdf[i])
        p = 1. * np.arange(len(data)) / (len(data) - 1)
        plt.plot(data, p, color=colors[ic])
        ic += 1
        message += '**%s**:\n\n* 100%% %.2f\n* 90%% %.2f\n* 75%% %.2f\n* 50%% %.2f\n* 25%% %.2f\n\n' % (i, np.percentile(data, 100), np.percentile(data, 90), np.percentile(data, 75), np.percentile(data, 50), np.percentile(data, 25))

    # Anotation
    plt.plot((1.25,1.25),(0,1), 'k--')
    plt.plot((2.5,2.5),(0,1), 'k--')
    plt.plot((1.25,1.25),(0,1), '--', color='grey')
    plt.plot((2.5,2.5),(0,1), '--', color='grey')
    plt.xlim(0,60)
    plt.annotate('1.25 seconds', xy=(1.25, 0.2), xytext=(6, 0.2),arrowprops=dict(arrowstyle="->"), color='grey')
    plt.annotate('2.5 seconds', xy=(2.5, 0.4), xytext=(6,0.4),arrowprops=dict(arrowstyle="->"), color='grey')
    plt.ylabel('CDF')
    plt.xlabel('Seconds between packets')
    plt.legend(legends)
    report.print_figure(fig, 'tbp_cdf', 'CDF of the time between consecutive packets received from the same sensor filtering deltas < 1s')
    report.print_line('### Stats (delta < 1s)')
    report.print_line(message)

def StatisticsPerMinute(df, report):
    report.print_line('## Dataset description (after 16:00)')

    df['traffic'] = df.apply(lambda x: 'system' if x['type'] in ['sensortag', 'estimote-nearable', 'estimote-iBeacon'] else 'noise', axis=1)
    df['system_type'] = df['type'].apply(lambda x: 'estimote' if x.startswith('estimote') else x)
    df['duplication_ratio'] =  df['packets'] / df['uniq_packets']
    df['rel_time'] = df['minute'] - min(df['minute'])
    df.loc[(df['day']=='Friday', 'rel_time')] = df.loc[(df['day']=='Friday', 'rel_time')] - min(df.loc[(df['day']=='Friday', 'rel_time')])

    # Stats
    report.print_line('### Stats')
    report.print_line('**Total number of packets+copies/packets**')
    report.print_line('* Thursday: %s/%s' % (df[(df['day'] == 'Thursday')]['packets'].sum(), df[(df['day'] == 'Thursday')]['uniq_packets'].sum()))
    report.print_line('* Friday: %s/%s' % (df[(df['day'] == 'Friday')]['packets'].sum(), df[(df['day'] == 'Friday')]['uniq_packets'].sum()))

    report.print_line('**Packets/copies received per Pi**')
    for pi in sorted(df['pi'].unique()):
        report.print_line('* %s: %s/%s' % (pi, df[(df['pi'] == pi)]['uniq_packets'].sum(), df[(df['pi'] == pi)]['packets'].sum()))

    report.print_line('**Packets/copies received per Pi (Estimotes and Sensortags only)**')
    for pi in sorted(df['pi'].unique()):
        report.print_line('* %s: %s/%s' % (pi, df[(df['pi'] == pi) & (df['traffic'] == 'system')]['uniq_packets'].sum(), df[(df['pi'] == pi) & (df['traffic'] == 'system')]['packets'].sum()))


    report.print_line('**Packets/copies received per type**')
    for t in sorted(df['type'].unique()):
        report.print_line('* %s: %s/%s' % (t, df[(df['type'] == t)]['uniq_packets'].sum(), df[(df['type'] == t)]['packets'].sum()))

    report.print_line('**System/Noise packets**')
    report.print_line('* Thursday: %s/%s' % (df[(df['day'] == 'Thursday') &  (df['traffic']=='system')]['uniq_packets'].sum(), df[(df['day'] == 'Thursday') & (df['traffic']=='noise')]['uniq_packets'].sum()))
    report.print_line('* Friday: %s/%s' % (df[(df['day'] == 'Friday') &  (df['traffic']=='system')]['uniq_packets'].sum(), df[(df['day'] == 'Friday') &  (df['traffic']=='noise')]['uniq_packets'].sum()))

    report.print_line('**Sensortag/Estimote packets**')
    report.print_line('* Thursday: %s/%s' % (df[(df['day'] == 'Thursday') &  (df['system_type']=='sensortag')]['uniq_packets'].sum(), df[(df['day'] == 'Thursday') & (df['system_type']=='estimote')]['uniq_packets'].sum()))
    report.print_line('* Friday: %s/%s' % (df[(df['day'] == 'Friday') &  (df['system_type']=='sensortag')]['uniq_packets'].sum(), df[(df['day'] == 'Friday') &  (df['system_type']=='estimote')]['uniq_packets'].sum()))

    report.print_line('**Mean/Max packets per minute**')
    report.print_line('* Thursday: %.2f/%.2f' % (df[(df['day'] == 'Thursday')].groupby('rel_time')['uniq_packets'].apply(np.sum).mean(), df[(df['day'] == 'Thursday')].groupby('rel_time')['uniq_packets'].apply(np.sum).max()) )
    report.print_line('* Friday: %.2f/%.2f' % (df[(df['day'] == 'Friday')].groupby('rel_time')['uniq_packets'].apply(np.sum).mean(), df[(df['day'] == 'Friday')].groupby('rel_time')['uniq_packets'].apply(np.sum).max()))

    report.print_line('**Mean/Max sensors per minute**')
    report.print_line('* Thursday: %.2f/%.2f' % (df[(df['day'] == 'Thursday') & (df['traffic'] == 'system')].groupby('rel_time')['sensorid'].unique().apply(len).mean(), df[(df['day'] == 'Thursday') & (df['traffic'] == 'system')].groupby('rel_time')['sensorid'].unique().apply(len).max()))
    report.print_line('* Friday: %.2f/%.2f' %  (df[(df['day'] == 'Friday') & (df['traffic'] == 'system')].groupby('rel_time')['sensorid'].unique().apply(len).mean(), df[(df['day'] == 'Friday') & (df['traffic'] == 'system')].groupby('rel_time')['sensorid'].unique().apply(len).max()))

    # Plot styles

    labels = ('16:00', '18:00', '20:00', '22:00', '00:00')
    # linestyles = ['-', '--', '-.', ':']
    # colors=[(0, 70.0/255, 0), (60.0/255, 179.0/255, 113.0/255), (0,0,70.0/255),(70.0/255, 130.0/255, 180.0/255)]
    colors=plt.cm.viridis(np.linspace(0,1,4))
    # Plot messages vs time: unique - duplicates
    dataplot = df.loc[:, ['uniq_packets', 'packets', 'rel_time', 'day']].groupby(['rel_time', 'day']).aggregate(np.sum).unstack()

    pl = dataplot.plot(color=colors)
    pl.set_xticks(range(0,len(dataplot.index),len(dataplot.index)/(len(labels)-1)))
    pl.set_xticklabels(labels)
    pl.set_xlabel('Time')
    pl.set_ylabel('Packets & Packet Copies per minute')
    # pl.legend(['Friday, packets', 'Friday, packets + copies', 'Thursday, packets ', 'Thursday, packets + copies'])
    report.print_figure(pl.get_figure(), 'packets_records_perminute', 'Packets vs. packets + copies')


    # Plot system vs. noise
    dataplot = df.groupby(['rel_time', 'day', 'traffic'])['packets'].aggregate(np.sum).unstack().unstack()

    pl = dataplot.plot(color=colors)

    pl.set_xticks(range(0,len(dataplot.index),len(dataplot.index)/(len(labels)-1)))
    pl.set_xticklabels(labels)
    pl.set_xlabel('Time')
    pl.set_ylabel('Packets per minute')
    # pl.legend(['Friday, noise', 'Friday, system', 'Thursday, system', 'Thursday, system'])
    report.print_figure(pl.get_figure(), 'system_noise_perminute', 'System (Estimote & Sensortag) packets vs. Noise packets')

    # Plot bytes of system vs. noise
    dataplot = df.groupby(['rel_time', 'day', 'traffic'])['bytes'].aggregate(lambda x: np.sum(x)/(1024)).unstack().unstack()

    pl = dataplot.plot(color=colors)

    pl.set_xticks(range(0,len(dataplot.index),len(dataplot.index)/(len(labels)-1)))
    pl.set_xticklabels(labels)
    pl.set_xlabel('Time')
    pl.set_ylabel('KB per minute')
    # pl.legend(['Friday, noise', 'Friday, system', 'Thursday, noise', 'Thursday, system'])
    report.print_figure(pl.get_figure(), 'system_noise_bytes_perminute', 'System (Estimote & Sensortag) bytes vs. Noise bytes')

    # Plot estimote vs. sensortag
    dataplot = df[(df['traffic'] == 'system')].groupby(['rel_time', 'day', 'system_type'])['uniq_packets'].aggregate(np.sum).unstack().unstack()

    pl = dataplot.plot(color=colors)

    pl.set_xticks(range(0,len(dataplot.index),len(dataplot.index)/(len(labels)-1)))
    pl.set_xticklabels(labels)
    pl.set_xlabel('Time')
    pl.set_ylabel('Packets per minute')
    # pl.legend(['Friday, estimote', 'Friday, sensortag', 'Thursday, estimote', 'Thursday, sensortag'])
    report.print_figure(pl.get_figure(), 'estimote_sensortag_perminute', 'Estimote packets vs. Sensortag packets')

    #%% Plot sensor seen every minute vs time
    dataplot = df[(df['traffic'] == 'system')].groupby(['rel_time', 'system_type',  'day'])['sensorid'].unique().apply(len).unstack().unstack()

    pl = dataplot.plot(color=colors)

    pl.set_xticks(range(0,len(dataplot.index),len(dataplot.index)/(len(labels)-1)))
    pl.set_xticklabels(labels)
    pl.set_xlabel('Time')
    pl.set_ylabel('Sensors per minute')
    # pl.legend(['Friday, estimote', 'Friday, sensortag', 'Thursday, estimote', 'Thursday, sensortag'])
    report.print_figure(pl.get_figure(), 'estimote_sensortag_sensorcount_perminute', 'Estimote vs. Sensortag sensors seen per minute')

    #%% Plot sensor seen every minute vs time in the Overdrive room
    dataplot = df[(df['traffic'] == 'system') & (df['pi']=='pi23')].groupby(['rel_time', 'system_type',  'day'])['sensorid'].unique().apply(len).unstack().unstack()

    pl = dataplot.plot(color=colors)

    pl.set_xticks(range(0,len(dataplot.index),len(dataplot.index)/(len(labels)-1)))
    pl.set_xticklabels(labels)
    pl.set_xlabel('Time')
    pl.set_ylabel('Sensors per minute in the Overdrive room')
    # pl.legend(['Friday, estimote', 'Thursday, estimote', 'Friday, sensortag', 'Thursday, sensortag'])
    report.print_figure(pl.get_figure(), 'overdrive_estimote_sensortag_sensorcount_perminute', 'Estimote vs. Sensortag sensors seen per minute in the Overdrive room')

    #%% Represents packets per pi
    dataplot = df.loc[:, ['pi', 'uniq_packets',  'packets']].groupby(['pi']).aggregate(np.sum)
    dataplot['packets'] = dataplot['packets'] - dataplot['uniq_packets']
    pl = dataplot.sort_values('uniq_packets').plot(kind='bar', stacked=True, colormap='Blues_r')
    pl.set_xlabel('Pi receiver')
    pl.set_ylabel('Packets')
    pl.legend(['Packets', 'Packet copies'])
    report.print_figure(pl.get_figure(), 'records_packets_perpi', 'Packets received per PI, including copies')
    #%% Represents packets per pi (system only)
    dataplot = df.loc[(df['traffic'] == 'system'), ['pi', 'uniq_packets',  'packets']].groupby(['pi']).aggregate(np.sum)
    dataplot['packets'] = dataplot['packets'] - dataplot['uniq_packets']
    pl = dataplot.sort_values('uniq_packets').plot(kind='bar', stacked=True, colormap='Blues_r')
    pl.set_xlabel('Pi receiver')
    pl.set_ylabel('Estimote and Sensortag Packets')
    pl.legend(['Packets', 'Packet copies'])
    report.print_figure(pl.get_figure(), 'records_packets_systemonly_perpi', 'Estimote and Sensortag packets received per PI, including copies')

    #%% Represents packets per type
    dataplot = df.loc[:, ['type', 'uniq_packets',  'packets']].groupby(['type']).aggregate(np.sum)
    dataplot['packets'] = dataplot['packets'] - dataplot['uniq_packets']
    pl = dataplot.sort_values('uniq_packets').plot(kind='bar', stacked=True, colormap='Greens_r')
    pl.set_yscale('log')
    pl.set_xlabel('Packet type')
    pl.set_ylabel('Packets')
    pl.legend(['Packets', 'Packet copies'])
    report.print_figure(pl.get_figure(), 'records_packets_pertype', 'Packets received per type, including copies')


def BLEModel(df, report):
    # Title
    report.print_line('## BLE Model statistics')

    # Common styles and labels for these plots

    # Distribution for all pi
    dataplot = df.groupby('rssi').sum()
    ax = dataplot.plot(colormap=plt.cm.viridis)
    ax.set_ylabel('Packets received')
    ax.set_xlim(-120,10)
    ax.set_xlabel('RSSI [dB]')
    ax.legend('')

    report.print_figure(ax.get_figure(), 'rssi_packets', 'Distribution of packets received vs. their RSSI')

    # Normalize per pi
    df['count'] = df.groupby('pi')['count'].transform(lambda x: x/max(x))

    ax = df.pivot_table(index='rssi', columns='pi', values='count').plot(colormap=plt.cm.viridis)
    ax.set_ylabel('Ratio of packets received')
    ax.set_xlim(-120,10)
    ax.set_xlabel('RSSI [dB]')
    report.print_figure(ax.get_figure(), 'rssi_packets_perpi', 'Distribution of packets received per pi vs. their RSSI')

    # Stats
    report.print_line('### Stats')
    report.print_line('RSSI value with more packets received: %s' % dataplot[dataplot['count'] == max(dataplot['count'])].index)

def Clustering(df, report):
    report.print_line('## FoR clustering')
    import seaborn as sns
    sns.set_style('whitegrid')
    sns.set_context('paper')
    for metric in ['pi', 'room']:
        for day in ['Friday', 'Thursday']:
            paths = df[(df['day']==day)].pivot_table(index='timestamp', values=metric, columns='sensorid', aggfunc=lambda x: x.any()).ffill()

            cols = paths.columns
            cluster_matrix = np.matrix([[0.0] * len(cols)] * len(cols))
            rowslen = paths.shape[0]
            for i in range(0,len(cols)):
                c1 = paths.columns[i]
                cluster_matrix[i,i] = 1.0

                for j in range(i+1, len(cols)):
                    c2 = paths.columns[j]
                    counts = (paths[c1] == paths[c2]).value_counts()
                    if True in counts:
                        cluster_matrix[i,j] = float(counts[True])/rowslen
                        cluster_matrix[j,i] = float(counts[True])/rowslen

            sns.set_context('paper', font_scale=0.8)
            plt.figure()
            pl = sns.clustermap(cluster_matrix)
            report.print_figure(pl, 'FoRPathSimilarityClustering_by%s_%s' % (metric, day), 'Clustering of FoR paths by %s on %s' % (metric, day))
            labels = [i if i%5==0 else '' for i in range(0,61)]
            sns.set_context('paper', font_scale=1)
            plt.figure()
            pl = sns.heatmap(cluster_matrix, xticklabels=labels, yticklabels=labels)
            report.print_figure(pl.get_figure(), 'FoRPathSimilarity_by%s_%s' % (metric, day), 'Heatmap of FoR paths by %s on %s' % (metric, day))


def main(inputf='./', outputf='./', statistics=True, blemodel=True, clustering=True, timebetweenpackets=True, figuresonly=False):
    if not statistics and not blemodel and not clustering and not timebetweenpackets:
        return

    # Initialize report object
    if figuresonly:
        report = Report(outputf, '/dev/null')
    else:
        report = Report(outputf, '%s/DatasetStatistics.md' % outputf)

    plt.style.use('seaborn-paper')
    # Insert stats from original dataset, precomputed to avoid loading it
    report.print_line('## Dataset stats')
    report.print_line('- Estimotes/Sensortags Thursday: 811/60')
    report.print_line('- Estimotes/Sensortags Friday: 556/61')
    report.print_line('- Estimotes/Sensortags: 812/109')


    report.print_line('- Packets/Copies (> 100ms criteria) Thursday: 6896252/14720392')
    report.print_line('- Packets/Copies (> 100ms criteria) Friday: 7758473/10965277')
    report.print_line('- Packets/Copies (> 1s criteria) Thursday: 2483302/19133342')
    report.print_line('- Packets/Copies (> 1s criteria) Friday: 3002246/15721504')



    # # Statistics per minute
    if statistics:
        # open df
        stat_df = pd.read_csv(inputf+'/StatisticsPerMinute.csv.gz')
        StatisticsPerMinute(stat_df, report)
    
    # BLEModel report section
    if  blemodel:
        ble_df = pd.read_csv(inputf+'/BLEModel.csv.gz')
        BLEModel(ble_df, report)

    # Time Between Packets analysis
    if timebetweenpackets:
        tbp_df = pd.read_csv(inputf+'/TimeBetweenPackets.csv.gz')
        TimeBetweenPackets(tbp_df, report)
    #Clustering of FoR
    if clustering:
        clustering_df = pd.read_csv(inputf+'/FoRClustering.csv.gz')
        Clustering(clustering_df, report)


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', dest='inputf', help='Input folder for CSV files.', required=True)
    parser.add_argument('-o', dest='outputf', help='Output folder to leave results', required=True)
    parser.add_argument('--no_clustering', dest='clustering', help='Skip FoR Clustering', action='store_false')
    parser.add_argument('--no_statistics', dest='statistics', help='Skip Statistics per Minute', action='store_false')
    parser.add_argument('--no_blemodel', dest='blemodel', help='Skip BLE Model', action='store_false')
    parser.add_argument('--no_timebetweenpackets', dest='timebetweenpackets', help='Skip Time Between Packets', action='store_false')
    parser.add_argument('--figures_only', dest='figuresonly', help='Just plot figures, do not modify text report', action='store_true')

    args = parser.parse_args()
    main(**vars(args))
