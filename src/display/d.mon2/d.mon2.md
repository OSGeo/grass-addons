## DESCRIPTION

This is just a little experiment to see if we can make the ximgview,
wximgview, and wxpyimgview programs a bit simpler to start up.

Add this to your `~/.grass.bashrc` file:

```sh
  if [ `echo "$GRASS_VERSION" | cut -f1 -d.` -eq 7 ] ; then
     alias d.mon='eval `d.mon.py -b`'
  fi
```

By default the temporary file will be stored in $MAPSET/.tmp/ and
cleared at the end of the session. You can put it somewhere else with
the **tempfile** option. For example, when working remotely with PuTTY
(ssh without tunnelled X) + Apache:

```sh
   alias d.mon='eval `d.mon.py -b handler=none tempfile=/var/www/grassmap.png`'
```

then just hit reload in your web browser whenever a refresh is needed.

## AUTHOR

Hamish Bowman  
Dunedin, New Zealand
