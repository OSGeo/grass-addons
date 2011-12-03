function dominant_dir = dominant_dir(dir)
% dominant_dir.m
%   extract dominant flow from r.terraflow direction map.
%   by Hamish Bowman 18 April 2005
% based upon the rules in r.terraflow's findDominant() funtion in direction.cc
%
% directions:
%   32 64 128
%   16 *   1
%   8  4   2
%
% USAGE:  this scipt is a helper function for use by the
%         calc_terraflow_dir.m script

switch(dir)
  case {1,2,4,8,16,32,64,128}
    dominant_dir=dir;

  case {1+2, 128+1}
    dominant_dir=1;
  case {2+4, 4+8}
    dominant_dir=4;
  case {8+16, 16+32}
    dominant_dir=16;
  case {32+64, 64+128}
    dominant_dir=64;

  case {1+2+4}
    dominant_dir=2;
  case {2+4+8}
    dominant_dir=4;
  case {4+8+16}
    dominant_dir=8;
  case {8+16+32}
    dominant_dir=16;
  case {16+32+64}
    dominant_dir=32;
  case {32+64+128}
    dominant_dir=64;
  case {64+128+1}
    dominant_dir=128;
  case {128+1+2}
    dominant_dir=1;

  case {128+1+2+4, 64+128+1+2}
    dominant_dir=1;
  case {1+2+4+8, 2+4+8+16}
    dominant_dir=4;
  case {8+16+32+64, 4+8+16+32}
    dominant_dir=16;
  case {32+64+128+1, 16+32+64+128}
    dominant_dir=64;

  case {64+128+1+2+4}
    dominant_dir=1;
  case {128+1+2+4+8}
    dominant_dir=2;
  case {1+2+4+8+16}
    dominant_dir=4;
  case {2+4+8+16+32}
    dominant_dir=8;
  case {4+8+16+32+64}
    dominant_dir=16;
  case {8+16+32+64+128}
    dominant_dir=32;
  case {16+32+64+128+1}
    dominant_dir=64;
  case {32+64+128+1+2}
    dominant_dir=128;

  case 0
    dominant_dir=dir;

  otherwise
    disp(['Ambiguous direction: [' num2str(dir) ']'])
    dominant_dir=-1;
end
