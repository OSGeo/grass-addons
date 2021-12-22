#!/bin/sh
############################################################################
#
# TOOL:         module_svn_propset.sh
# AUTHOR:       Hamish Bowman, Dunedin, New Zealand
# PURPOSE:      Looks at the files you pass it, tries to set svn props
#		automatically for the ones it knows
# COPYRIGHT:    (c) 2009-2013 Hamish Bowman, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
# For a list of valid mime types see /etc/mime.types
#

if [ $# -lt 1 ] ; then
    echo "USAGE:  module_svn_propset.sh file1 [file2 file3 *.html]"
    echo
    exit 1
fi

if [ ! -x "`which svn`" ] ; then
    echo "ERROR: Subversion not found, install it first" 1>&2
    exit 1
fi

########

# will only set if previously empty
set_native_eol()
{
   if [ `svn proplist "$1" | grep -c 'svn:eol-style'` -eq 0 ] ; then
      svn propset svn:eol-style "native" "$1"

   fi
}

set_msdos_eol()
{
   if [ "`svn propget svn:eol-style "$1"`" = "native" ] ; then
      svn propdel svn:eol-style "$1"
   fi
   if [ `svn proplist "$1" | grep -c 'svn:eol-style'` -eq 0 ] ; then
      svn propset svn:eol-style "CRLF" "$1"
   fi
}

set_mime_type()
{
   # remove generic default for images
   if [ `echo "$2" | cut -f1 -d/` = "image" ] ; then
      if [ "`svn propget svn:mime-type "$1"`" = "application/octet-stream" ] ; then
         svn propdel svn:mime-type "$1"
      fi
   fi

   if [ `svn proplist "$1" | grep -c 'svn:mime-type'` -eq 0 ] ; then
      svn propset svn:mime-type "$2" "$1"
   fi
}

# will only set if previously empty
set_exe()
{
   if [ `svn proplist "$1" | grep -c 'svn:executable'` -eq 0 ] ; then
      svn propset svn:executable "ON" "$1"
   fi
}

# will only unset if previously set
unset_exe()
{
   if [ `svn proplist "$1" | grep -c 'svn:executable'` -eq 1 ] ; then
      svn propdel svn:executable "$1"
   fi
}

# will only set if previously empty
set_keywords()
{
   # check if set at all
   if [ `svn proplist "$1" | grep -c 'svn:keywords'` -eq 0 ] ; then
      svn propset svn:keywords "Author Date Id" "$1"
   fi
   # check if any keyword is missing
   for keyword in Author Date Id ; do
      if [ `svn proplist -v "$1" | grep -c "$keyword"` -eq 0 ] ; then
         svn propset svn:keywords "Author Date Id" "$1"
      fi
   done
}


########
#usually these are not stored in Svn, but fyi:
# diff | patch ) svn propset svn:mime-type text/x-diff filenname

apply_html()
{
   set_keywords "$1"
   set_mime_type "$1" text/html
   set_native_eol "$1"
   unset_exe "$1"
}

apply_xml()
{
   # While given as "application" in /etc/mime.types, "text" is desired
   #  here due to the way SVN uses the mime type. See RFC 3023 and
   #   http://www.imc.org/ietf-xml-mime/mail-archive/msg00496.html
   #  Unfortunately SVN treats "application" as "binary" and then refuses
   #  to do text diffs. (same problem with PostScript)
   set_mime_type "$1" text/xml
   set_native_eol "$1"
   unset_exe "$1"
}

apply_text()
{
   set_keywords "$1"
   set_mime_type "$1" text/plain
   set_native_eol "$1"
   unset_exe "$1"
}

apply_makefile()
{
   set_mime_type "$1" text/x-makefile
   set_native_eol "$1"
   unset_exe "$1"
}

apply_shell_script()
{
   set_mime_type "$1" text/x-sh
   set_native_eol "$1"
   set_exe "$1"
}

apply_python_script()
{
   set_mime_type "$1" text/x-python
   set_native_eol "$1"
   #? set_exe "$1"
}

apply_perl_script()
{
   set_mime_type "$1" text/x-perl
   set_native_eol "$1"
   #? set_exe "$1"
}

apply_bat_script()
{
   # CHECKME: setting as an app/ might stop trac from trying diffs & previews
   set_mime_type "$1" "text/x-bat"
   set_msdos_eol "$1"
   unset_exe "$1"
}

apply_C_code()
{
   set_mime_type "$1" text/x-csrc
   set_native_eol "$1"
   unset_exe "$1"
}

apply_C_header()
{
   set_mime_type "$1" text/x-chdr
   set_native_eol "$1"
   unset_exe "$1"
}

apply_Cpp_code()
{
   set_mime_type "$1" "text/x-c++src"
   set_native_eol "$1"
   unset_exe "$1"
}

apply_Fortran_code()
{
   set_mime_type "$1" text/x-fortran
   set_native_eol "$1"
   unset_exe "$1"
}

apply_image()
{
   set_mime_type "$1" "image/$2"
   unset_exe "$1"
}

apply_pdf()
{
   set_mime_type "$1" "application/pdf"
   unset_exe "$1"
}

apply_po()
{
   set_keywords "$1"
   set_mime_type "$1" text/x-po
   set_native_eol "$1"
   unset_exe "$1"
}

apply_OBJ_code()
{
   svn propset svn:ignore "OBJ.*
*.tmp.html" .
}

apply_Sql_code()
{
   set_mime_type "$1" text/x-sql
   set_native_eol "$1"
   unset_exe "$1"
}

apply_svg()
{
   set_mime_type "$1" "image/svg+xml"
   set_native_eol "$1"
   unset_exe "$1"
}

########


for FILE in $* ; do
  #echo "Processing <$FILE> ..."

  if [ ! -e "$FILE" ] ; then
     echo "ERROR: file not found <$FILE>"
     continue
  fi

  if test -d "$FILE" ; then
     DIRPREF=`echo "$FILE" | cut -d'.' -f1`
     if [ "$DIRPREF" = "OBJ" ] ; then
	apply_OBJ_code "$FILE"
     fi
  fi

  FILE_SUFFIX=`echo "$FILE" | sed -e 's/^.*\.//'`
  case "$FILE_SUFFIX" in
    c)
	apply_C_code "$FILE"
	;;
    h)
	apply_C_header "$FILE"
	;;
    cc | cpp)
	apply_Cpp_code "$FILE"
	;;
    f | for | f77 | f90)
	apply_Fortran_code "$FILE"
	;;
    py)
	apply_python_script "$FILE"
	;;
    pl)
	apply_perl_script "$FILE"
	;;
    bat)
	apply_bat_script "$FILE"
	;;
    sh)
	apply_shell_script "$FILE"
	;;
    html)
	apply_html "$FILE"
	;;
    xml)
	apply_xml "$FILE"
	;;
    gxm)
	apply_xml "$FILE"
	;;
    pdf | PDF)
	apply_pdf "$FILE"
	;;
    png | jpg | jpeg | gif | bmp | xpm | xcf | ico)
	if [ "$FILE_SUFFIX" = "jpg" ] ; then
	    FILE_SUFFIX="jpeg"
	elif [ "$FILE_SUFFIX" = "svg" ] ; then
	    FILE_SUFFIX='svg+xml'
	elif [ "$FILE_SUFFIX" = "xpm" ] ; then
	    FILE_SUFFIX='x-xpixmap'
	elif [ "$FILE_SUFFIX" = "ico" ] ; then
	    FILE_SUFFIX='x-icon'
	fi
	apply_image "$FILE" "$FILE_SUFFIX"
	;;
    txt | ascii | dox | md)
	apply_text "$FILE"
	;;
    po)
        apply_po "$FILE"
        ;;
    rst)
	apply_text "$FILE"
	;;
    sql)
	apply_Sql_code "$FILE"
	;;
    svg)
	apply_svg "$FILE"
	;;
    *)
	if [ "`basename $FILE`" = "Makefile" ] ; then
	   apply_makefile "$FILE"
	elif [ "`basename $FILE`" = "README" ] || [ "`basename $FILE`" = "TODO" ] ; then
	   apply_text "$FILE"
	elif [ `file "$FILE" | grep -c "shell script\|sh script"` -eq 1 ] ; then
	   apply_shell_script "$FILE"
	else
	    if test ! -d "$FILE" ; then
		echo "WARNING: unknown file type <$FILE>"
	    fi
	fi
	;;
  esac
done
