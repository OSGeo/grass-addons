-- This script will create the table managing all categories of a raster maps 
-- this table should be altered if additional category columns are needed
-- the specific column should be selected with a where statement, by default the column
-- named "label" should be used
CREATE TABLE TABLE_NAME (cat INTEGER PRIMARY KEY, -- the category number 
			 value NUMERIC, -- the numerical value of the raster map using this category
			 label VARCHAR(500) -- the label of the category
                        );

