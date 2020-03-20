try:
    from collections.abc import Mapping
except ImportError:
    from collections import Mapping

from collections import OrderedDict


class _LocIndexer(Mapping):
    """
    Access raster maps by using a label
    
    Represents a structure similar to a dict, but can return values using a
    list of keys (not just a single key)

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
        self._dict[key] = value
        setattr(self.parent, key, value)

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)

    def pop(self, key):
        pop = self._dict.pop(key)
        delattr(self.parent, key)
        return pop


class _ILocIndexer(object):
    """
    Access raster maps using integer-based indexing

    Parameters
    ----------
    parent : pyspatialml.Raster
        Requires to parent Raster object in order to setattr when
        changes in the dict, reflecting changes in the RasterLayers occur.
    
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
            key = list(self._index.keys())[index]
            self._index[key] = value
            setattr(self.parent, key, value)

        if isinstance(index, slice):
            index = list(range(index.start, index.stop))

        if isinstance(index, (list, tuple)):
            for i, idx in enumerate(index):
                key = list(self._index.keys())[idx]
                self._index[key] = value[i]
                setattr(self.parent, key, value[i])

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
