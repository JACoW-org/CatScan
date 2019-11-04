#!/bin/sh

echo BOOT container started

counter=1
while true; do
    echo BOOT Trying to upgrade DB...
    flask db upgrade
    if [ "$?" = "0" ]; then
        echo BOOT DB upgrade DONE
        break
    elif [ "$counter" -gt 5 ]; then
        echo "BOOT Counter: $counter times reached; Exiting loop!"
        break
    fi
    echo "BOOT Upgrade command attempt #$counter failed, retrying in 10 secs..."
    sleep 10
    counter=$((counter+1))
done

# ExecStart=/usr/local/bin/pipenv run gunicorn -w 3 --pid /run/gunicorn/pid --timeout 180 wsgi:app -b 0.0.0.0:8080
exec gunicorn --bind=0.0.0.0:5000 wsgi:app