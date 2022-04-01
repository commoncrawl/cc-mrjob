#!/usr/bin/env bash

ccfiles=(
  'crawl-data/CC-MAIN-2014-35/segments/1408500800168.29/warc/CC-MAIN-20140820021320-00000-ip-10-180-136-8.ec2.internal.warc.gz'
  'crawl-data/CC-MAIN-2014-35/segments/1408500800168.29/wat/CC-MAIN-20140820021320-00000-ip-10-180-136-8.ec2.internal.warc.wat.gz'
  'crawl-data/CC-MAIN-2014-35/segments/1408500800168.29/wet/CC-MAIN-20140820021320-00000-ip-10-180-136-8.ec2.internal.warc.wet.gz'
  'crawl-data/CC-MAIN-2017-30/segments/1500549423183.57/robotstxt/CC-MAIN-20170720121902-20170720141902-00000.warc.gz'
);

for ccfile in ${ccfiles[@]}; do
  mkdir -p `dirname $ccfile`
  echo "Downloading `basename $ccfile` ..."
  echo "---"
  wget --no-clobber https://commoncrawl.s3.amazonaws.com/$ccfile -O $ccfile
done
