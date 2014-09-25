#!/bin/bash

if [ -z $1 ]; then
    echo 'a version argument is required.'
    exit 1
fi

full=$1
major=$(echo $1 | awk -F . {' print $1"."$2 '})
uname=$(uname)

if [ "$uname" == "Darwin" ]; then
    find ./ -iname "setup.py" -exec sed -i '' "s/version='.*'/version='${full}'/g" {} \;
    find ./ -iname "setup.py" -exec sed -i '' "s/\"iustools.core==.*\",/\"iustools.core==${full}\",/g" {} \;
elif [ "$uname" == "Linux" ]; then
    find ./ -iname "setup.py" -exec sed -i "s/version='.*'/version='${full}'/g" {} \;
    find ./ -iname "setup.py" -exec sed -i "s/\"iustools.core==.*\",/\"iustools.core==${full}\",/g" {} \;
fi
