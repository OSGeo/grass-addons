#!/bin/bash

for file in *.met
do
	./l7inread $file
	chmod +x temp.txt
	cat temp.txt
	echo "Start GRASS Processing"
	./temp.txt
	echo "Done"
done

