try:
    from collections.abc import Mapping

except ImportError:
    from collections import Mapping

from collections import OrderedDict

from grass.pygrass.raster import RasterRow


class _LocIndexer(Mapping):
    """
    Access raster maps by using a label
    
    Represents a structure similar to a dict, but can return values using a
    list of keys (not just a single key)
    
    This class also forces the keys to always match the names of the physical
    GRASS raster objects. We don't allow arbitary names in the RasterStack to
    refer to physical GRASS raster objects because this would get messy

    Parameters
    ----------
    parent : pyspatialml.Raster
        Requires to parent Raster object in order to setattr when
        changes in the dict, reflecting changes in the RasterLayers occur.
    """

    def __init__(self, parent, *args, **kw):
        self.parent = parent
        self._dict = OrderedDict(*args, **kw)

    def __getitem__(self, keys):
        if isinstance(keys, str):
            selected = self._dict[keys]
        else:
            selected = [self._dict[i] for i in keys]
        return selected

    def __str__(self):
        return str(self._dict)

    def __setitem__(self, key, value):
        """Add a new key, value pair to the LocIndexer
        
        Checks to see if the key exists already, in which case it replaces
        oldkey with newkey, value, otherwise it just adds a new key, value 
        pair to the dict
        """
        
        # convert to lists
        if isinstance(key, str):            
            key = [key]
        
        if isinstance(value, RasterRow):
            value = [value]
            
        # some checks
        # check equal number of keys and values
        if len(key) != len(value):
            raise ValueError("Cannot set layers using a different number of keys and values")
        
        # check types
        for k, v in zip(key, value):
            if not isinstance(k, str):
                raise ValueError("Label for new layer in the RasterStack has to be a string")
            
            if not isinstance(v, RasterRow):
                raise ValueError("Setting a layer on something other than a RasterRow object is not allowed")
        
        # check for duplicated keys
        if len(key) != len(set(key)):
            raise ValueError("Duplicate keys have been provided")
        
        # update
        for k, v in zip(key, value):
            if k in self.keys():
                self.update(k, v)
            
            else:  
                self._dict[k] = v
                setattr(self.parent, k, v)
                self.parent.mtypes.update({k: v.mtype})

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)

    def pop(self, key):
        # pop key, value pair from LocIndexer
        popped = self._dict.pop(key)
        
        # drop mtype from parent RasterStack
        self.parent.mtypes.pop(key)
        
        # delete attribute name from parent RasterStack
        delattr(self.parent, key)
        
        return popped
    
    def update(self, key, value):
        """Update a key with a new value
        
        We rather than simply replacing the value of the dict, we want to keep
        the names in-sync with the original GRASS raster names, i.e we don't
        want arbirary names in the RasterStack to refer to the physical names
        of GRASS GIS rasters because this will end up being messy.
        
        Instead the update method updates the dict value and replaces its key
        with the name of the RasterRow object
        """
        oldkey = key
        
        # replace value of dict
        self._dict[oldkey] = value
        
        # rename old key preserving order
        newkey = value.name_mapset().replace(".", "_")
        self._dict = OrderedDict(
            (newkey if k == oldkey else k, v) for k, v in self._dict.items()
        )
        
        # update parent attributes
        delattr(self.parent, oldkey)
        setattr(self.parent, newkey, value)

        # update parents mtypes
        self.parent.mtypes.pop(oldkey)
        self.parent.mtypes.update({newkey: value.mtype})


class _ILocIndexer(object):
    """
    Access raster maps using integer-based indexing

    Parameters
    ----------
    parent : RasterStack
        Requires to parent RasterStack object in order to setattr when
        changes in the dict, reflecting changes in the layers occur.
    
    loc_indexer : _LocIndexer
        Wraps around the _LocIndexer class to index it using integer indexes.
    """

    def __init__(self, parent, loc_indexer):
        self.parent = parent
        self._index = loc_indexer

    def __setitem__(self, index, value):
        """
        Assign a grass.pygrass.raster.RasterRow object to the index using an
        integer label
        
        Parameters
        ----------
        index : int, or slice
            Index position(s) to assign the new RasterRow objects.
        
        value : grass.pygrass.raster.RasterRow, or list
            Values to assign to the index.
        """

        if isinstance(index, int):
            # get dict key based on the index position
            oldkey = list(self._index.keys())[index]
            
            # update replacing both key and value
            self._index.update(oldkey, value)
            

        if isinstance(index, slice):
            index = list(range(index.start, index.stop))

        if isinstance(index, (list, tuple)):
            for idx, val in zip(index, value):
                
                oldkey = list(self._index.keys())[idx]
                self._index.update(oldkey, val)
                
    def __getitem__(self, index):
        """
        Get a grass.pygrass.raster.RasterRow object using an integer label
        
        Parameters
        ----------
        index : int, or slice
            Index(es) of layers to retrieve.
        
        Returns
        -------
        value
        """

        if isinstance(index, int):
            key = list(self._index.keys())[index]
            selected = self._index[key]

        if isinstance(index, slice):
            start = index.start
            stop = index.stop

            if start is None:
                start = 0

            if stop is None:
                stop = self.parent.count

            index = list(range(start, stop))

        if isinstance(index, (list, tuple)):
            key = []
            for i in index:
                key.append(list(self._index.keys())[i])
            selected = [self._index[k] for k in key]

        return selected
