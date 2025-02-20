### {{ gettext('Service Metadata') }}

#### {{ gettext('Service Identification') }}

|                                     |                                             |
| ----------------------------------- | ------------------------------------------- |
| {{ gettext('Title') }}              | {{ obj.identification.title }}              |
| {{ gettext('Abstract') }}           | {{ obj.identification.abstract }}           |
| {{ gettext('Keywords') }}           | {{ obj.identification.keywords|join(',') }} |
| {{ gettext('Type') }}               | {{ obj.identification.type }}               |
| {{ gettext('Version') }}            | {{ obj.identification.version }}            |
| {{ gettext('Fees') }}               | {{ obj.identification.fees }}               |
| {{ gettext('Access Constraints') }} | {{ obj.identification.accessconstraints }}  |

#### {{ gettext('Service URL') }}

[{{ obj.url}}](%7B%7B-obj.url-%7D%7D)

#### {{ gettext('Service Provider') }}

|                       |                                                              |
| --------------------- | ------------------------------------------------------------ |
| {{ gettext('Name') }} | {{ obj.provider.name }}                                      |
| {{ gettext('Site') }} | [{{ obj.provider.url }}](%7B%7B-obj.provider.url-%7D%7D) |

#### {{ gettext('Service Contact') }}

<table>
<colgroup>
<col style="width: 50%" />
<col style="width: 50%" />
</colgroup>
<tbody>
<tr class="odd">
<td>{{ gettext('Name') }}</td>
<td>{{ obj.provider.contact.name }}</td>
</tr>
<tr class="even">
<td>{{ gettext('Position') }}</td>
<td>{{ obj.provider.contact.position}}</td>
</tr>
<tr class="odd">
<td>{{ gettext('Role') }}</td>
<td>{{ obj.provider.contact.role }}</td>
</tr>
<tr class="even">
<td>{{ gettext('Address') }}</td>
<td>{{ obj.provider.contact.address }}<br />
{{ obj.provider.contact.city }}, {{ obj.provider.contact.region }}<br />
{{ obj.provider.contact.postcode }}<br />
{{ obj.provider.contact.country }}</td>
</tr>
<tr class="odd">
<td>{{ gettext('Email') }}</td>
<td><a href="mailto:%7B%7B-obj.provider.contact.email--%7D%7D">{{ obj.provider.contact.email }}</a></td>
</tr>
<tr class="even">
<td>{{ gettext('Phone') }}</td>
<td>{{ obj.provider.contact.phone }}</td>
</tr>
<tr class="odd">
<td>{{ gettext('Fax') }}</td>
<td>{{ obj.provider.contact.fax }}</td>
</tr>
<tr class="even">
<td>{{ gettext('Url') }}</td>
<td><a href="%7B%7B-obj.provider.contact.url-%7D%7D">{{ obj.provider.contact.url }}</a></td>
</tr>
<tr class="odd">
<td>{{ gettext('Hours of Service') }}</td>
<td>{{ obj.provider.contact.hours }}</td>
</tr>
<tr class="even">
<td>{{ gettext('Contact Instructions') }}</td>
<td>{{ obj.provider.contact.instructions }}</td>
</tr>
</tbody>
</table>
