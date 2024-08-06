# DDoSia ChatGPT 4o analysis

## Providing context

*What is the DDoSia project ?*

*Use the file name to determine the date. File name have the following format YYYY-MM-DD_HH-MM-SS_DDoSia-target-list.csv where YYYY-MM-DD is the date and HH-MM-SS is the time. The files in the zip file represents configurations of the DDoSia project.*

*The targets are identified via the host field in each file.*

## Questions & Answers

### General

*What is the first date and timestamp of the configuration files*

January 21, 2024, at 06:05:04

*What is the last date and timestamp ?*

August 6, 2024, at 07:15:03

### Analysis per day

*Provide a table of number of files per day*

[Number of files per day](data/Number_of_Files_Per_Day.csv)

*Plot the number of files per day*

![Plot of the number of files per day](data/files_per_day.png)

*Show average files per day*

Approximately 4.57 files per day

*Show the busiest day*

The busiest day for the DDoSia project configurations was May 27, 2024, with 17 files.

*Identify the least busy day*

February 9, 2024, with just 1 file.

### Analysis per week

*What is the number of files per week number ?*

[Number of files per week number](data/Number_of_Files_Per_Week.csv)

*Plot number of files per week*

![Plot of the number of files per week](data/files_per_week.png)

*Show average files per week*

Approximately 28.17 files per week

*Show the busiest week*

Week number 22 of 2024, with 60 files.

*Identify the least busy week*

Week number 3 of 2024, with 3 files

*Analyse the number of files between open business days and week-ends per weeks*

[Number of files between open business days and week-ends](data/Number_of_Files_by_Week_and_Type_of_Day.csv)

### Analysis per month

*What is the number of files per month ?*

[Number of files per month](data/Number_of_Files_Per_Month.csv)

*Plot number of files per month*

![Plot of the number of files per month](data/files_per_month.png)

### Analysis of non activities

*On the overall period what are the dates and week day name without files*

- Saturday, February 24, 2024
- Sunday, February 25, 2024
- Tuesday, February 27, 2024
- Wednesday, February 28, 2024
- Thursday, February 29, 2024
- Friday, March 1, 2024
- Saturday, March 2, 2024
- Sunday, March 3, 2024
- Sunday, March 24, 2024
- Friday, April 12, 2024
- Saturday, May 11, 2024
- Sunday, May 12, 2024
- Tuesday, July 2, 2024
- Sunday, July 7, 2024

*Are any of these days particular dates in Russia, like public holidays or major events*

None of the dates listed are major public holidays in Russia. Some are adjacent to significant holidays such as Defender of the Fatherland Day and Victory Day, but they are not public holidays themselves.

### Analysis on Saturday's and Sunday's

*On the overall period what are the Saturday's and Sunday's with files. Display a list of with the dates, week day name and number of files*

[List of Saterday's and Sunday's with files](data/Saturdays_and_Sundays_With_Files_and_Counts.csv)

### Analysis of target ccTLD's

*What are the top 20 ccTLD targets as uniq hosts*

The top 20 ccTLD targets as hosts are:

- ua: 23,706 occurrences
- md: 18,771 occurrences
- com: 18,546 occurrences
- es: 16,834 occurrences
- it: 11,240 occurrences
- pl: 10,803 occurrences
- fi: 9,951 occurrences
- de: 9,113 occurrences
- ro: 8,854 occurrences
- cz: 8,190 occurrences
- se: 4,721 occurrences
- fr: 4,421 occurrences
- lt: 3,848 occurrences
- nl: 3,289 occurrences
- lu: 3,084 occurrences
- jp: 3,050 occurrences
- si: 2,991 occurrences
- gr: 2,868 occurrences
- il: 2,806 occurrences
- org: 2,709 occurrences

*What are the top 20 ccTLD targets as uniq hosts*

The top 20 ccTLD targets as unique hosts are:

- com: 261 unique hosts
- es: 169 unique hosts
- ua: 147 unique hosts
- it: 115 unique hosts
- cz: 110 unique hosts
- pl: 93 unique hosts
- de: 88 unique hosts
- fi: 87 unique hosts
- fr: 70 unique hosts
- dk: 64 unique hosts
- be: 61 unique hosts
- se: 58 unique hosts
- il: 55 unique hosts
- ro: 54 unique hosts
- nl: 51 unique hosts
- si: 50 unique hosts
- lu: 49 unique hosts
- ch: 47 unique hosts
- jp: 46 unique hosts
- gr: 43 unique hosts

*Visualize the distribution of ccTLD targets.*

![Plot of the number of files per month](data/TOP20-ccTLDs.png)

*For the overall period, plot the top 10 uniq number of ccTLD targets per weeks. The targets are identified via the host field in each file. Add the ccTLD name in the plot as legend. Each ccTLD should have a uniq distinguishable color*

![Plot the top 10 uniq number of ccTLD targets per weeks](data/Plot_top10_ccTLD_per_week.png)

*Which ccTLD had the most fluctuation*

The ccTLD that experienced the most fluctuation is .ua, with a standard deviation of approximately 115.73.

*Are they any patterns of the targeted top 20 ccTLDs overtime*

**Observations:**
- Fluctuations: Certain ccTLDs show significant fluctuations in targeting activity.
- Spikes: There are visible spikes in activity for some ccTLDs, indicating periods of increased targeting.
- Trends: Some ccTLDs exhibit consistent levels of activity, while others have more erratic patterns.

#### Fluctuations

The ccTLDs with the most fluctuations, based on the standard deviation of the number of unique hosts per week, are:

- ua: 115.73
- es: 100.32
- it: 98.46
- md: 87.52
- pl: 73.39
- ro: 67.24
- de: 63.76
- com: 61.79
- fi: 59.44
- se: 50.90

![Top 10 ccTLDs with the most fluctuations](data/TOP10_ccTLDs_fluctuations.png)

*What are the ccTLDs exhibiting consistent levels of activity*

The ccTLDs exhibiting the most consistent levels of activity, based on the lowest standard deviations, are:

- org: 11.08
- nl: 22.20
- fr: 26.53
- lu: 32.82
- gr: 33.75
- jp: 34.61
- si: 35.59
- lt: 38.40
- cz: 42.49
- il: 45.83

These ccTLDs have shown relatively stable activity levels over the weeks.

*What are the most consistent ccTLD targets?*

The most consistent ccTLD targets, based on the coefficient of variation (CV), are:

- com: 1.10
- org: 1.38
- ua: 1.77
- cz: 1.97
- md: 2.07
- fr: 2.09
- es: 2.22
- fi: 2.33
- nl: 2.47
- de: 2.83

### Analysis of targeted hosts

*What is the top 20 uniq targeted hosts*

The top 20 unique targeted hosts are:

- servicii.gov.md: 2,512 occurrences
- mai.gov.md: 2,080 occurrences
- presedinte.md: 1,971 occurrences
- mfa.gov.md: 1,820 occurrences
- stisc.gov.md: 1,710 occurrences
- www.tram.cat: 1,666 occurrences
- moldova.md: 1,539 occurrences
- gov.md: 1,471 occurrences
- www.legis.md: 1,445 occurrences
- mpass.gov.md: 1,277 occurrences
- mded.gov.md: 918 occurrences
- www.caf.net: 752 occurrences
- multimedia.parlament.md: 739 occurrences
- a1.com.pl: 690 occurrences
- credit-agricole.ua: 653 occurrences
- metro.kyiv.ua: 621 occurrences
- anasf.it: 621 occurrences
- www.autostrada-a2.pl: 608 occurrences
- autostrady.mpay.pl: 594 occurrences
- www.radioroks.ua: 559 occurrences

## Used protocols

*What are the used protocols on the overall period for all targets ? The protocols are identified by the "type" field in the csv files*

Here are the used protocols on the overall period for all targets, based on the "type" field in the CSV files:

- tcp: 842 occurrences
- http: 839 occurrences
- nginx_loris: 839 occurrences
- http2: 810 occurrences
- udp: 349 occurrences
- http3: 313 occurrences

