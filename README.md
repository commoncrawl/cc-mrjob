![Common Crawl Logo](https://commoncrawl.org/wp-content/uploads/2016/12/logocommoncrawl.png)

# mrjob starter kit

This project demonstrates using Python to process the Common Crawl dataset with the mrjob framework.
There are three tasks to run using the three different data formats:

+ Counting HTML tags using Common Crawl's raw response data (WARC files)
+ Analysis of web servers using Common Crawl's metadata (WAT files)
+ Word count using Common Crawl's extract text (WET files)

In addition, there is a more complex version of the server analysis tool that will only count unique domains.
This provides a good example of a more complex MapReduce job that involves an additional reduce step.

## Setup

To develop locally, you will need to install the `mrjob` Hadoop streaming framework, the `boto` library for AWS, the `warc` library for accessing the web data, and `gzipstream` to allow Python stream decompress gzip files.

This can all be done using `pip`:

    pip install -r requirements.txt

If you would like to create a virtual environment to protect local dependencies:

    virtualenv env/
    source env/bin/activate
    pip install -r requirements.txt

To develop locally, you'll need at least three data files -- one for each format the crawl uses.
These can either be downloaded by running the `get-data.sh` command line program or manually by grabbing the [WARC](https://data.commoncrawl.org/crawl-data/CC-MAIN-2014-35/segments/1408500800168.29/warc/CC-MAIN-20140820021320-00000-ip-10-180-136-8.ec2.internal.warc.gz), [WAT](https://data.commoncrawl.org/crawl-data/CC-MAIN-2014-35/segments/1408500800168.29/wat/CC-MAIN-20140820021320-00000-ip-10-180-136-8.ec2.internal.warc.wat.gz), and [WET](https://data.commoncrawl.org/crawl-data/CC-MAIN-2014-35/segments/1408500800168.29/wet/CC-MAIN-20140820021320-00000-ip-10-180-136-8.ec2.internal.warc.wet.gz) files.

## Running the code

The example code includes three tasks, the first of which runs a HTML tag counter over the raw web data.
One could use it to see how well HTML5 is being adopted or to see how strangely people use heading tags.

    "h1" 520487
    "h2" 1444041
    "h3" 1958891
    "h4" 1149127
    "h5" 368755
    "h6" 245941
    "h7" 1043
    "h8" 29
    "h10" 3
    "h11" 5
    "h12" 3
    "h13" 4
    "h14" 19
    "h15" 5
    "h21" 1

We'll be using `tag_counter.py` as our primary task, which runs over WARC files.
To run the other examples, `server_analysis.py` (WAT) or `word_count.py` (WET), simply run that Python script whilst using the relevant input format.

### Running locally

Running the code locally is made incredibly simple thanks to mrjob.
Developing and testing your code doesn't actually need a Hadoop installation.

First, you'll need to get the relevant demo data locally, which can be done by running:

    ./get-data.sh
    
If you're on Windows, you just need to download the files listed and place them in the appropriate folders, so that the input files (`input/test-1.{robots,warc,wat,wet}`) in the examples below contain the correct relative path to the local copies.

To run the jobs locally, you can simply run:

    python server_analysis.py --conf-path mrjob.conf --no-output --output-dir output/ input/test-1.wat
    python server_count_warc.py --conf-path mrjob.conf --no-output --output-dir output/ input/test-1.warc
    python sitemaps_from_robotstxt.py --conf-path mrjob.conf --no-output --output-dir output/ input/test-1.robots
    python tag_counter.py --conf-path mrjob.conf --no-output --output-dir output/ input/test-1.warc
    python unique_server_analysis.py --conf-path mrjob.conf --no-output --output-dir output/ input/test-1.wat
    python word_count.py --conf-path mrjob.conf --no-output --output-dir output/ input/test-1.wet

Using the 'local' runner simulates more features of Hadoop, such as counters:

    python tag_counter.py -r local --conf-path mrjob.conf --no-output --output-dir output/ input/test-1.warc

### Running via Elastic MapReduce

As the Common Crawl dataset lives in the [Amazon Web Services’ Open Data Sets Sponsorships](https://aws.amazon.com/opendata/) program, you can [access it for free](https://commoncrawl.org/access-the-data/).
The only cost that you incur is the cost of the machines and Elastic MapReduce itself.

By default, EMR machines run with Python 2.6.
The configuration file automatically installs Python 2.7 on your cluster for you.
The steps to do this are documented in `mrjob.conf`.

The three job examples in this repository (`tag_counter.py`, `server_analysis.py`, `word_count.py`) rely on a common module - `mrcc.py`.
By default, this module will not be present when you run the examples on Elastic MapReduce, so you have to include it explicitly.
You have two options:

1. [Deploy your source tree as a tar ball](https://mrjob.readthedocs.io/en/latest/guides/setup-cookbook.html#uploading-your-source-tree)
2. Copy-paste the code from mrcc.py into the job example that you are trying to run:

        cat mrcc.py tag_counter.py | sed "s/from mrcc import CCJob//" > tag_counter_emr.py

To run the job on Amazon Elastic MapReduce (their automated Hadoop cluster offering), you need to add your AWS access key ID and AWS access key to `mrjob.conf`.
By default, the configuration file only launches two machines, both using spot instances to be cost effective. If you are running this for a full fledged job, you will likely want to make the master server a normal instance, as spot instances can disappear at any time.

Using option two as shown above, you can then run the script on EMR by running:

    python tag_counter_emr.py -r emr --conf-path mrjob.conf --no-output --output-dir s3://my-output-bucket/path/ input/test-100.warc

this time reading 100 WARC files from Common Crawl's Public Data Set bucket `s3://commoncrawl/`. The output is written to S3 - do not forget to point the output (`s3://my-output-bucket/path/` is just a dummy) to a S3 bucket and path you have write permissions. The output directory must not exist!

### Running via Hadoop

To launch the job on a Hadoop cluster of AWS EC2 instances (e.g., CDH), see the script `run_ccmrjob_hadoop.sh`.

## Running it over all of Common Crawl

To run your mrjob task over the entirety of the Common Crawl dataset, you can use the WARC, WAT, or WET file listings found at `CC-MAIN-YYYY-WW/[warc|wat|wet].paths.gz`.

As an example, the [August 2014 crawl](https://commoncrawl.org/august-2014-crawl-data-available/) has 52,849 WARC files listed by [warc.paths.gz](https://data.commoncrawl.org/crawl-data/CC-MAIN-2014-35/warc.paths.gz). You'll find pointers to listings for all crawls including the most recent ones on the [commoncrawl Public Data Set bucket](https://data.commoncrawl.org/crawl-data/index.html) and the [get-started page](https://commoncrawl.org/the-data/get-started/).

It is highly recommended to run over batches of files at a time and then perform a secondary reduce over those results.
Running a single job over the entirety of the dataset complicates the situation substantially.
We also recommend having [N map jobs for the N files](https://groups.google.com/forum/#!topic/mrjob/o9t5FrgkMCs) you'll be attempting such that if there is a transient error, the minimal amount of work will be lost.

You'll also want to place your results in an S3 bucket instead of having them streamed back to your local machine.
For full details on this, refer to the mrjob documentation.

Note about locally buffering WARC/WAT/WET files: The default temp folder (set via hadoop.tmp.dir, default /tmp/) must be large enough to buffer content from S3 for all task running on a machine. You might point it explicitly to a directory on a volume large enough by passing `--s3_local_temp_dir=/path/to/tmp`.

## Running with PyPy

If you're interested in using PyPy for a speed boost, you can look at the [source code](https://github.com/mcroydon/social-graph-analysis) from **Social Graph Analysis using Elastic MapReduce and PyPy**.

## License

MIT License, as per `LICENSE`
