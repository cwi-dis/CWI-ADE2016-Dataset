# CWI-ADE2016-Dataset Files
## Merging files
To be able to host these files in GitHub, we have splitted them in chunks. In case you are interested, the command used was: 

split -C 90m -d ade2016dataset-blepackets.csv ade2016dataset-blepackets.csv-part-

split -C 90m -d ade2016dataset-sensordata.csv ade2016dataset-sensordata.csv-part-

Thus, to use this dataset, you may want to merge the CSV files back. For that you can simply use a command like the following:

cat blepackets/* > ade2016dataset-blepackets.csv

cat sensordata/* > ade2016dataset-sensordata.csv
