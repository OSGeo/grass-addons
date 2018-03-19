#!/usr/bin/env python3

import fileinput

def contribs_to_git(contribs_file, authors_file):
    extra = True if 'extra' in contribs_file else False
    contribs_data = {}
    with open(contribs_file) as fd:
        for line in fd.readlines()[1:]:
            if not extra:
                cvs_id,name,email,country,osgeo_id,rfc2_agreed = line.split(',')
            else:
                name,email,country,rfc2_agreed = line.split(',')
            email = '@'.join(email.split(' ', -1))
            names = list(map(lambda x: x.lower(), name.split(' ')))
            if not extra:
                names.append(osgeo_id)
                names.append(cvs_id)
            for uid in names:
                if uid != '-':
                    contribs_data[uid] = '{uid} = {name} {email}'.format(uid=uid, name=name, email=email)

    with fileinput.FileInput(authors_file, inplace=True) as fd:
        for line in fd:
            author, rest = map(lambda x: x.strip(), line.split(' ', 1))
            if author in contribs_data:
                print(contribs_data[author])
            else:
                print(line, end='')

### MAIN ###
for cfile in ('contributors.csv', 'contributors_extra.csv'):
    contribs_to_git(cfile, 'authors.txt')
