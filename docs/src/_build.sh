#!/bin/sh

pids=""
outputs="git pdf_ epub_"
for output in $outputs ; do
    Rscript -e "bookdown::render_book('index.Rmd', 'bookdown::${output}book')" > /tmp/doc_log_$output 2>&1 &
    pids="$pids $!"
done

errors=""
for pid in $pids ; do
    wait $pid
    if [ $? -ne 0 ] ; then
        errors="$errors $pid"
    fi
done

if ! [ -z "$errors" ] ; then
    echo "\n\nlaunched processes:"
    echo "$outputs with pids $pids"
    echo "$errors failed\n\n"

    for output in $outputs ; do
        echo "output $output"
        tail /tmp/doc_log_$output
    done

    return 1
fi

echo "done"

rm -r ../libs/ ../0* || echo "nothing to remove"
rm -r _book/images
mv _book/* ../
rmdir _book
