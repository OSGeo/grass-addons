<!DOCTYPE html>
<html lang="{{ language }}">
<head>
    <meta charset="utf-8"/>
    <title>{{ gettext('Record Metadata') }}</title>
    <style type="text/css">
        body, h3 {
            background-color: #ffffff;
            font-family: arial, verdana, sans-serif;
            text-align: left;
            float: left;
        }

        header {
            display: inline-block;
        }
    </style>
</head>
<body>
<header>
    <h3>{{ gettext('Record Metadata') }}</h3>
</header>
<section id="record-metadata">
     <table>
         <tr>
            <td>{{ gettext('Identifier') }}</td>
            <td>{{ obj.identifier }}</td>
        </tr>
    </table>
    <table>
        <tr>
            <td>{{ gettext('Title') }}</td>
            <td>{{ obj.identification.title }}</td>
        </tr>
        <tr>
            <td>{{ gettext('Abstract') }}</td>
            <td>{{ obj.identification.abstract }}</td>
        </tr>
        <tr>
        {% for co in obj.identification.contact -%}
            <tr>
                <td>{{ gettext('Responsible party:') }}</td>
                <tr><td>{{ gettext(' -organisation') }}</td><td>{{ co.organization }}</td></tr>
                <tr><td>{{ gettext(' -email') }}</td><td>{{ co.email }}</td></tr>
                <tr><td>{{ gettext(' -role') }}</td><td>{{ co.role }}</td></tr>
            </tr>
        {% endfor -%}
        </tr>
        <tr>
            <td>{{ gettext('Language') }}</td>
            <td>{{ obj.languagecode }}</td>
        </tr>
        <tr>
            {% for rc in obj.identification.uselimitation -%}
                <td>{{ gettext('Use limitation') }}</td>
                <td> {{ rc }}</td>
            {% endfor -%}
        </tr>
        <tr>
            {% for oc in obj.identification.otherconstraints -%}
                <td>{{ gettext('Other constraint') }}</td>
                <td>{{ oc }}</td>
            {% endfor -%}
        </tr>
        <tr>
            {% for ac in obj.identification.accessconstraints -%}
                <td>{{ gettext('Access constraints') }}</td>
                <td> {{ ac }}</td>
            {% endfor -%}
        </tr>
        <tr>
            <td>{{ gettext('Bounding Box') }}</td>
            <td>{{ [obj.identification.extent.boundingBox.minx, obj.identification.extent.boundingBox.miny, obj.identification.extent.boundingBox.maxx, obj.identification.extent.boundingBox.maxy]|join(',') }}</td>
        </tr>
    </table>
</section>
<section id="links">
    <h4>Links</h4>
    <ul>
        {% for (cod,code) in zip(obj.identification.uricode,obj.identification.uricodespace) %}

        <li><a href="{{ cod }}">{{ cod if cod not in [None, 'None', ''] else
            gettext('Access Link') }}</a></li>
        {% endfor %}
    </ul>
</section>
</body>
</html>
