#!/bin/bash
mkdir ghtorrent
cd ghtorrent

#~100 GB in size
wget http://ghtorrent-downloads.ewi.tudelft.nl/mysql/mysql-2019-06-01.tar.gz
tar -zxvf mysql-2019-06-01.tar.gz projects.csv watchers.csv