#!/bin/bash

# (c) 2010 by Anton Korenyushkin

if [[ $# < 4 ]]; then
    echo Usage: $0 user path from to
    exit 1
fi

user=$1
base=$2
from=$3
to=$4

for i in `seq $from $to`; do
    echo $i
    dir=$base/$i
    mkdir $dir
    chown $user:$i $dir
    chmod g+s $dir
    mkdir $dir/tablespace $dir/apps $dir/libs $dir/grantors
    chown postgres $dir/tablespace
    echo -n {} > $dir/config
    ssh-keygen -q -N '' -C '' -f $dir/rsa
    echo -e '#!/bin/bash\nexec /usr/bin/ssh -i "${0%/*}/rsa" "$@"' > $dir/ssh
    chown $user $dir/apps $dir/libs $dir/grantors $dir/config $dir/rsa $dir/rsa.pub $dir/ssh
    chmod u+x $dir/ssh
done
