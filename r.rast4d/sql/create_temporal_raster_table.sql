-- This script will create the table managing all temporal raster datatypes of grass
-- inclusively metadata 
 
CREATE TABLE TABLE_NAME (name VARCHAR(256) PRIMARY KEY, -- name of the temporal raster table
                         raster_map_table VARCHAR(300), -- the table containing the list of all registered raster maps
                         metadata_table VARCHAR(300) -- the table containing the metadata list (one row for each update)
			);
-- the names of the data tables are a combination of 
-- the raster map name, which must be unique and the 
-- table eg.: 
-- if map name is slope the data tables will have the following names:
--	temporal_metadata_table_slope
