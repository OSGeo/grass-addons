### {{ gettext('Record Metadata') }}

|                             |                      |
| --------------------------- | -------------------- |
| {{ gettext('Identifier') }} | {{ obj.identifier }} |

{{ gettext('Title') }}

{{ obj.identification.title }}

{{ gettext('Abstract') }}

{{ obj.identification.abstract }}

{% for co in obj.identification.contact -%}

{{ gettext('Responsible party:') }}

{{ gettext(' -organisation') }}

{{ co.organization }}

{{ gettext(' -email') }}

{{ co.email }}

{{ gettext(' -role') }}

{{ co.role }}

{% endfor -%}

{{ gettext('Language') }}

{{ obj.languagecode }}

{% for rc in obj.identification.uselimitation -%}

{{ gettext('Use limitation') }}

{{ rc }}

{% endfor -%}

{% for oc in obj.identification.otherconstraints -%}

{{ gettext('Other constraint') }}

{{ oc }}

{% endfor -%}

{% for ac in obj.identification.accessconstraints -%}

{{ gettext('Access constraints') }}

{{ ac }}

{% endfor -%}

{{ gettext('Bounding Box') }}

{{ \[obj.identification.extent.boundingBox.minx,
obj.identification.extent.boundingBox.miny,
obj.identification.extent.boundingBox.maxx,
obj.identification.extent.boundingBox.maxy\]|join(',') }}

#### Links

- [{{ cod if cod not in \[None, 'None', ''\] else gettext('Access
    Link') }}](%7B%7B-cod-%7D%7D)
