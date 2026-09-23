## DESCRIPTION

*m.prism.download* downloads data from [the PRISM Climate
Group](https://prism.oregonstate.edu/).

## NOTES

This module anonymously logs in to [their FTP
server](ftp://ftp.prism.oregonstate.edu/) ([HTTPS
server](https://ftp.prism.oregonstate.edu/) for easier browsing) and
download climate data for a specified time period.

## EXAMPLES

List supported datasets and exit:

```sh
# use indices or datasets, but indices can change between module versions
m.prism.download -d
```

Download daily precipitation from 2020-01-01 to today:

```sh
# find the dataset name
m.prism.download -d | grep "daily" # found daily/ppt

# just list URLs for now
m.prism.download dataset=daily/ppt start_date=2020-01-01 end_date=today -u sep=newline

# actually download files
m.prism.download dataset=daily/ppt start_date=2020-01-01 end_date=today

# do something with the downloaded files
for file in $(m.prism.download dataset=daily/ppt start_date=2020-01-01 end_date=today -f sep=newline); do
    echo $file
    unzip $file
    # more tasks...
done
```

## SEE ALSO

*[m.cdo.download](m.cdo.download.md),
[m.tnm.download](m.tnm.download.md)*

## AUTHOR

[Huidae Cho](mailto:grass4u@gmail-com), New Mexico State University
