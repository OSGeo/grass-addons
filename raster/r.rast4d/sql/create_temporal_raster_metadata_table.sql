-- This script will create the table managing the metadata of one temporal raster map
-- the temporal raster map region is used with all registered raster map, independently which kind of region
-- the registered raster maps have
CREATE TABLE TABLE_NAME (name VARCHAR(256) PRIMARY KEY, -- the name of the temporal raster map
                         projection CLOB , -- Projection information for this temporal data type
                         vtime_start DATE, -- start valid time
                         vtime_end DATE, -- end valid time
			 vtime_duration DATE, -- the duration time
			 time_step DATE, -- the time step
                         ctime DATE, -- creation time
                         mtime DATE, -- modification time
                         datatype VARCHAR(30), -- the temporal map data type
			 rows INTEGER, -- the number of rows of the temporal region
			 cols INTEGER, -- the number of columns  of the temporal region
			 raster_num INTEGER, -- the number of registered raster maps
			 cell_num INTEGER, -- the number of temporal cell (rows * cols * raster_num)
			 north NUMERIC(15,10), -- coordinates of the northern edge
			 south NUMERIC(15,10), -- coordinates of the southern edge
			 west NUMERIC(15,10), -- coordinates of the western edge
			 east NUMERIC(15,10), -- coordinates of the eastern edge
			 ns_res NUMERIC(15,10), -- resolution in north/south direction
			 ew_res NUMERIC(15,10), -- resolution in east/west direction
			 min NUMERIC(25,15), --the minimum value
			 max NUMERIC(25,15), --the maximum value
			 modification_time DATE, -- the modification time of the current temporal map 
			 creator VARCHAR(30), -- the login of the creator
                         data_source CLOB , -- the source of the temporal raster map
                         comments CLOB , -- comments 
                         description CLOB , -- the temporal raster map description
                         additonal_data CLOB -- further metadata
                        );
-- this table is created once for all existing raster maps containing the actual metadata information
-- and this table is created each time a new raster map is created containing the history of metadata
-- for each update a new row of metadata will be added to create a history of metadata changes
-- this table name is a combination of the temporal raster map name and the suffix temporal_metadata 
