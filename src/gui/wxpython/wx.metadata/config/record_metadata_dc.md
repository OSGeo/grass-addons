### {{ gettext('Record Metadata') }} ([{{ gettext('View XML') }}](%7B%7B-obj.xml_url-%7D%7D))

|                             |                      |
| --------------------------- | -------------------- |
| {{ gettext('Identifier') }} | {{ obj.identifier }} |

|                               |                                                                                |
| ----------------------------- | ------------------------------------------------------------------------------ |
| {{ gettext('Title') }}        | {{ obj.title }}                                                                |
| {{ gettext('Abstract') }}     | {{ obj.abstract }}                                                             |
| {{ gettext('Subjects') }}     | {{ obj.subjects|join(',') }}                                                   |
| {{ gettext('Creator') }}      | {{ obj.creator }}                                                              |
| {{ gettext('Contributor') }}  | {{ obj.contributor}}                                                           |
| {{ gettext('Publisher') }}    | {{ obj.publisher}}                                                             |
| {{ gettext('Modified') }}     | {{ obj.modified }}                                                             |
| {{ gettext('Language') }}     | {{ obj.language }}                                                             |
| {{ gettext('Format') }}       | {{ obj.format }}                                                               |
| {{ gettext('Rights') }}       | {{ obj.rights|join(',') }}                                                     |
| {{ gettext('Bounding Box') }} | {{ \[obj.bbox.minx, obj.bbox.miny, obj.bbox.maxx, obj.bbox.maxy\]|join(',') }} |

#### Links

  - [{{ link\['scheme'\] if link\['scheme'\] not in \[None, 'None', ''\]
    else gettext('Access Link') }}](%7B%7B-link%5B'url'%5D-%7D%7D)
  - [{{ link\['protocol'\] if link\['protocol'\] not in \[None, 'None',
    ''\] else gettext('Access Link')
    }}](%7B%7B-link%5B'url'%5D-%7D%7D)
