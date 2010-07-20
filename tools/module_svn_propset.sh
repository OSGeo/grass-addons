#!/bin/sh
############################################################################
#
# TOOL:         module_svn_propset.sh
# AUTHOR:       Hamish Bowman, Dunedin, New Zealand
# PURPOSE:      Looks at the files you pass it, tries to set svn props
#		automatically for the ones it knows
# COPYRIGHT:    (c) 2009 Hamish Bowman, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

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
   if [ `svn proplist "$1" | grep -c 'svn:keywords'` -eq 0 ] ; then
      svn propset svn:keywords "Author Date Id" "$1"
   fi
}


########


apply_html()
{
   set_keywords "$1"
   set_mime_type "$1" text/html
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


########


for FILE in $* ; do
  #echo "Processing <$FILE> ..."

  if [ ! -e "$FILE" ] ; then
     echo "ERROR: file not found <$FILE>"
     continue
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
    py)
	apply_python_script "$FILE"
	;;
    pl)
	apply_perl_script "$FILE"
	;;
    html)
	apply_html "$FILE"
	;;
    sh)
	apply_shell_script "$FILE"
	;;
    pdf)
	apply_pdf "$FILE"
	;;
    png | jpg | jpeg | gif | bmp | svg)
	if [ "$FILE_SUFFIX" = "jpg" ] ; then
	    FILE_SUFFIX="jpeg"
	elif [ "$FILE_SUFFIX" = "svg" ] ; then
	    FILE_SUFFIX='svg+xml'
	fi
	apply_image "$FILE" "$FILE_SUFFIX"
	;;
    txt)
	apply_text "$FILE"
	;;
    rst)
	apply_text "$FILE"
	;;
    *)
	if [ "$FILE" = "Makefile" ] ; then
	   apply_makefile "$FILE"
	elif [ `file "$FILE" | grep -c "shell script"` -eq 1 ] ; then
	   apply_shell_script "$FILE"
	else
	    echo "WARNING: unknown file type <$FILE>"
	fi
	;;
  esac
done
