-- this table will list all raster maps 
-- every time a raster map was created an entry will be 
-- made setting the creation and modification time
CREATE TABLE TABLE_NAME (name VARCHAR(256) PRIMARY KEY,
                         ctime DATE, -- creation time
                         mtime DATE, -- modification time
                         vtime_start DATE, -- start valid time
                         vtime_end DATE, -- end valid time
			 vtime_duration DATE -- the duration time
                        );

