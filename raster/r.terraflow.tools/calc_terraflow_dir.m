% calc_terraflow_dir.m
%   extract dominant flow from r.terraflow direction map and convert to GRASS aspect map
%   by Hamish Bowman 18 April 2005
%
% GRASS aspect format is in degrees CCW from east.
%
% (c) 2005 The GRASS GIS Development Team
% This program is free software under the GNU General Public
%   License (>=v2). Read the file COPYING that comes with GRASS
%   for details.
%
% terraflow directions:
%   32 64 128
%   16 *   1
%   8  4   2
%
% USAGE:
%  !r.out.mat in=terraflow.dir out=tf.mat
%  load tf.mat
%  then run this script

if ( exist('map_data') ~= 1)
    disp('you have to import map from GRASS first. r.out.mat->load file.mat')
end

dim = size(map_data);
dom_map = zeros(dim);
asp_map = zeros(dim);

for i = 1:dim(1)
    for j = 1:dim(2)
        dom_map(i,j) = dominant_dir(map_data(i,j));
    end
end

%imagesc(dom_map), axis equal, axis tight, colorbar

oct_mtx = [0 1 2 4 8 16 32 64 128 -1];
asp_mtx = [0 360:-45:45 -1];

for i = 1:length(oct_mtx)
   asp_map(find(dom_map == oct_mtx(i))) = asp_mtx(i);
end

%clf
%imagesc(asp_map), axis equal, axis tight, colorbar

% save results
map_data = asp_map;
map_name = 'terraflow_aspect';
map_title= 'TerraFlow direction from GRASS aspect format from calc_terraflow_dir.m';
save terraflow_aspect.mat map_* -v4

if(0)
% GRASS commands to load back in
!r.in.mat in=terraflow_aspect.mat -v
!r.null map=terraflow_aspect setnull=0
!r.colors terraflow_aspect col=aspect
!d.rast.arrow terraflow_aspect
end

