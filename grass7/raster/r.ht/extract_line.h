#ifndef EXTRACT_LINE_H
#define EXTRACT_LINE_H

#include "matrix.h"

#include <vector>
#include <list>

typedef std::pair<int, int> Coordinates;
typedef std::pair< Coordinates, Coordinates > Segment;
typedef std::vector< Segment > SegmentList;
typedef std::list< std::pair<int, int> > LineCoordinates;

void extract(const matrix::Matrix& I, const float orient, int gapSize, int maxNumOfGaps, const int lineGap, const int lineLength, LineCoordinates lineCoordinates, SegmentList& segments);

#endif // EXTRACT_LINE_H
