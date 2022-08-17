#!/bin/sh

JOB="$1"
INPUT="$2"
OUTPUT="$3"

if [ -z "$JOB" ] || [ -z "$INPUT" ] || [ -z "$OUTPUT" ]; then
    echo "Usage: $0 <job> <input> <outputdir>"
    echo "  Run a CommonCrawl mrjob on Hadoop"
    echo
    echo "Arguments:"
    echo "  <job>     CCJob implementation"
    echo "  <input>   input path"
    echo "  <output>  output path (must not exist)"
    echo
    echo "Example:"
    echo "  $0 word_count hdfs://.../wet.paths  hdfs:///.../output/"
    echo
    echo "Note: don't forget to adapt the number of maps/reduces and the memory requirements"
    exit 1
fi

# strip .py from job name
JOB=${JOB%.py}

# wrap Python files for deployment, cf. below option --setup,
# see for details
# http://pythonhosted.org/mrjob/guides/setup-cookbook.html#putting-your-source-tree-in-pythonpath
tar cvfz ${JOB}_ccmr.tar.gz *.py

# number of maps resp. reduces 
NUM_MAPS=250
NUM_REDUCES=10

if [ -n "$S3_LOCAL_TEMP_DIR" ]; then
	S3_LOCAL_TEMP_DIR="--s3_local_temp_dir=$S3_LOCAL_TEMP_DIR"
else
	S3_LOCAL_TEMP_DIR=""
fi

if [ -n "$S3_BUCKET" ]; then
	S3_BUCKET="--bucket=$S3_BUCKET"
else
	S3_BUCKET=""
fi

python3 $JOB.py \
       -r hadoop \
       --jobconf "mapreduce.map.memory.mb=1200" \
       --jobconf "mapreduce.map.java.opts=-Xmx1024m" \
       --jobconf "mapreduce.reduce.memory.mb=1200" \
       --jobconf "mapreduce.reduce.java.opts=-Xmx1024m" \
       --jobconf "mapreduce.output.fileoutputformat.compress=true" \
       --jobconf "mapreduce.output.fileoutputformat.compress.codec=org.apache.hadoop.io.compress.BZip2Codec" \
       --jobconf "mapreduce.job.reduces=$NUM_REDUCES" \
       --jobconf "mapreduce.job.maps=$NUM_MAPS" \
       --setup 'export PYTHONPATH=$PYTHONPATH:'${JOB}'_ccmr.tar.gz#/' \
       --no-output \
       --cleanup NONE \
       $S3_LOCAL_TEMP_DIR \
       $S3_BUCKET \
       --output-dir "$OUTPUT" \
       "$INPUT"
