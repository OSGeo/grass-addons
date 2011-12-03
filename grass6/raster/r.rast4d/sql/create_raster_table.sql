-- This script will create the table managing all raster maps of grass
-- inclusively categories, color tables, metadata and links to temporal data types
CREATE TABLE TABLE_NAME (name VARCHAR(256) PRIMARY KEY,
                         base_map VARCHAR(256) , -- the map of which this map is based on
                         reference_table VARCHAR(300), -- the table containing all raster map names which are using this map as base map
			 color TEXT, -- the color information is stored as TEXT
                         group_table VARCHAR(300), -- the table containing all group names in which this raster map is registered
                         temporal_table VARCHAR(300), -- the table containing all temporal raster map names 
			 			      -- in which this raster map is registered
                         metadata_table VARCHAR(300), -- the table containing the metadata history list (one row for each update)
                         category_table VARCHAR(300), -- the category table
                         category_num INTEGER -- number of categories
                        );
-- the names of the data tables are a combination of 
-- the raster map name, which must be unique and the 
-- table eg.: 
-- if map name is slope the data tables will have the following names:
--	raster_reference_table_slope
--	raster_group_table_slope
--	raster_metadata_table_slope
-- 	raster_temporal_table_slope
--	raster_category_table_slope
