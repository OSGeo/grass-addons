#ifndef LILESEGMENTSEXTRACTOR_H
#define LILESEGMENTSEXTRACTOR_H

#include "houghparameters.h"
#include "matrix.h"

#include <vector>
#include <list>

typedef std::pair<int, int> Coordinates;
typedef std::pair<Coordinates, Coordinates> Segment;
typedef std::vector<Segment> SegmentList;
typedef std::list<std::pair<int, int>> LineCoordinates;

class LineSegmentsExtractor {
public:
    typedef double value_type;
    typedef matrix::Matrix<value_type> Matrix;

    /**
      \param image should exist during existence of LineSegmentsExtractor
      \param lineCoordinates will be copied to internal variable
      */
    LineSegmentsExtractor(const Matrix &image,
                          const ExtractParametres &parametres)
        : mImage(image), gapSize(parametres.gapSize),
          maxNumOfGaps(parametres.maxNumOfGaps), lineGap(parametres.maxGap),
          lineLength(parametres.lineLength), lineWidth(parametres.lineWidth)
    {
    }

    /**
      \param lineCoordinates list of lines
      \param orient orientation of lines
      \param[out] segments extracted segments will be added to this list
      */
    void extract(LineCoordinates lineCoordinates, const double orient,
                 SegmentList &segments);

private:
    const Matrix &mImage;
    int gapSize;
    int maxNumOfGaps;
    int lineGap;
    int lineLength;
    int lineWidth;
};

#endif // LILESEGMENTSEXTRACTOR_H
