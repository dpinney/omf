DIR=`dirname "$0"`
export GLPATH=$DIR
export PATH=$PATH:$DIR
"${DIR}/gridlabd" "$@"