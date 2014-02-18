#!/bin/sh
FILE='.git/hooks/pre-commit'

echo '#!/bin/sh' > $FILE
echo 'cd src/' >> $FILE
echo 'sudo py.test' >> $FILE
echo 'exit $?' >> $FILE

chmod 750 $FILE
