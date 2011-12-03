-- This script will create the table managing the metadata of one raster map
CREATE TABLE TABLE_NAME (name VARCHAR(256) PRIMARY KEY, -- the name of the raster map
                         projection TEXT , -- Projection information
                         datatype VARCHAR(30), -- the map data type
			 rows INTEGER, -- the number of rows
			 cols INTEGER, -- the number of columns
			 cell_num INTEGER, -- the number of cell
			 north NUMERIC(15,10), -- coordinates of the northern edge
			 south NUMERIC(15,10), -- coordinates of the southern edge
			 west NUMERIC(15,10), -- coordinates of the western edge
			 east NUMERIC(15,10), -- coordinates of the eastern edge
			 ns_res NUMERIC(15,10), -- resolution in north/south direction
			 ew_res NUMERIC(15,10), -- resolution in east/west direction
			 min NUMERIC(25,15), --the minimum value
			 max NUMERIC(25,15), --the maximum value
			 mtime DATE, -- the modification time of the current entry
			 creator VARCHAR(30), -- the login of the creator
                         data_source TEXT , -- the source of the raster map
                         comments TEXT , -- comments 
                         description TEXT , -- the raster map description
                         additional_data TEXT -- further metadata
                        );
-- this table is created once for all existing raster maps containing the actual metadata information
-- and this table is created each time a new raster map is created containing the history of metadata
-- for each update a new row of metadata will be added to create a history of metadata changes
-- the table name is a combination of the raster map name and the suffix metadata 
