#include "linesegmentsextractor.h"

#include "matrix.h"

#include <stdio.h>

#include <cmath>
#include <vector>
#include <list>

using namespace matrix;

struct Point {
    int x;
    int y;
};

/* non-member functions */

double segmentLenght(const Segment &segment)
{
    double x = segment.first.first - segment.second.first;
    double y = segment.first.second - segment.second.second;
    return std::sqrt(x * x + y * y);
}

bool checkBounds(int y, int x, int cols, int rows)
{
    if (y < 0 || y >= cols || x < 0 || x >= rows)
        return false;
    return true;
}

template <typename Matrix>
bool isData(const Matrix &I, const std::vector<int> &y,
            const std::vector<int> &x, const int cols, const int rows)
{
    for (size_t k = 0; k < y.size(); k++) {
        if (checkBounds(y.at(k), x.at(k), cols, rows) && I(x.at(k), y.at(k))) {
            return true;
        }
    }
    return false;
}

void remove_points(LineCoordinates &lineCoordinates,
                   const std::vector<int> &indicesI,
                   const std::vector<int> &indicesJ)
{
    for (size_t i = 0; i < indicesI.size(); ++i) {
        std::pair<int, int> coords;
        coords.second = indicesI[i];
        coords.first = indicesJ[i];
        lineCoordinates.remove(coords);
    }
}

void find_indices(std::vector<int> &indicesI, std::vector<int> &indicesJ,
                  const int shift, const bool xflag, const int x, const int y,
                  const int line_width)
{
    if (xflag) {
        int tmp1, tmp2;
        indicesJ[0] = x;
        tmp1 = y >> shift;
        tmp2 = tmp1;
        indicesI[0] = tmp1;
        for (int l = 1; l < line_width; l += 2) {
            indicesJ[l] = x;
            indicesJ[l + 1] = x;
            indicesI[l] = --tmp1;
            indicesI[l + 1] = ++tmp2;
        }
    }
    else {
        int tmp1, tmp2;
        indicesI[0] = y;
        tmp1 = x >> shift;
        tmp2 = tmp1;
        indicesJ[0] = tmp1;
        for (int l = 1; l < line_width; l += 2) {
            indicesI[l] = y;
            indicesI[l + 1] = y;
            indicesJ[l] = --tmp1;
            indicesJ[l + 1] = ++tmp2;
        }
    }
}

bool segmentContainsPoint(const Segment &segment, const std::pair<int, int> &p,
                          bool xFlag, int tol)
{
    int min, max;
    if (xFlag) {
        min = segment.first.first;
        max = segment.second.first;
        if (segment.first.first > segment.second.first) {
            min = segment.second.first;
            max = segment.first.first;
        }

        if (p.first > min + tol && p.first <= max - tol)
            return true;
    }
    else {
        min = segment.first.second;
        max = segment.second.second;
        if (segment.first.second > segment.second.second) {
            min = segment.second.second;
            max = segment.first.second;
        }
        if (p.second > min + tol && p.second <= max - tol)
            return true;
    }
    return false;
}

/* member functions */

void LineSegmentsExtractor::extract(LineCoordinates lineCoordinates,
                                    const double orient, SegmentList &segments)
{
    const int rows = mImage.rows();
    const int cols = mImage.columns();

    float rho = 1.0;
    float irho = 1. / rho;

    bool xflag;

    std::vector<Point> line_end(2);
    SegmentList newSegments;

    // from the current point walk in each direction
    // along the found line and extract the line segment
    float a = -(float)(sin(orient) * irho); //-trigtab[theta_n*2+1];
    float b = (float)(cos(orient) * irho);  // trigtab[theta_n*2];

    int dx0, dy0;
    const int shift = 16;

    std::vector<int> indicesI(lineWidth);
    std::vector<int> indicesJ(lineWidth);

    int lineNum = 0;
    while (!lineCoordinates.empty()) {
        lineNum++;
        std::pair<int, int> startCoordinates = lineCoordinates.front();

        int x0 = startCoordinates.first;
        int y0 = startCoordinates.second;

        if (fabs(a) > fabs(b)) {
            xflag = 1;
            dx0 = a > 0 ? 1 : -1;
            dy0 = (int)(b * (1 << shift) / fabs(a) + 0.5);
            y0 = (y0 << shift) + (1 << (shift - 1));
        }
        else {
            xflag = 0;
            dy0 = b > 0 ? 1 : -1;
            dx0 = (int)(a * (1 << shift) / fabs(b) + 0.5);
            x0 = (x0 << shift) + (1 << (shift - 1));
        }

        int numOfGaps = 0;
        bool useLine = true;
        for (int k = 0; k < 2; k++) {
            int gap = 0, x = x0, y = y0, dx = dx0, dy = dy0;

            if (k > 0)
                dx = -dx, dy = -dy;

            // walk along the line using fixed-point arithmetics,
            // stop at the image border or in case of too big gap
            for (;; x += dx, y += dy) {
                find_indices(indicesI, indicesJ, shift, xflag, x, y, lineWidth);

                remove_points(lineCoordinates, indicesI, indicesJ);

                // for each non-zero point:
                //    update line end,
                //    clear the mask element
                //    reset the gap
                if (isData(mImage, indicesI, indicesJ, cols, rows)) {
                    if (gap > gapSize) {
                        numOfGaps++;
                        if (numOfGaps > maxNumOfGaps) {
                            useLine = false;
                            break;
                        }
                    }
                    gap = 0;
                    line_end[k].y = indicesI[0];
                    line_end[k].x = indicesJ[0];
                }
                else if (++gap > lineGap) {
                    break;
                }
            }
        }

        bool good_line = abs(line_end[1].x - line_end[0].x) >= lineLength ||
                         abs(line_end[1].y - line_end[0].y) >= lineLength;

        if (good_line && useLine) {
            Segment newSegment;
            newSegment.first.first = line_end[0].x;
            newSegment.first.second = line_end[0].y;
            newSegment.second.first = line_end[1].x;
            newSegment.second.second = line_end[1].y;
            int limit = 5;
            bool add = true;
            if (!newSegments.empty()) {
                add = false;
                const Segment lastSegment = newSegments.back();
                if (!segmentContainsPoint(lastSegment, newSegment.first, xflag,
                                          limit) &&
                    !segmentContainsPoint(lastSegment, newSegment.second, xflag,
                                          limit) &&
                    !segmentContainsPoint(newSegment, lastSegment.first, xflag,
                                          limit) &&
                    !segmentContainsPoint(newSegment, lastSegment.second, xflag,
                                          limit)) {
                    add = true;
                }

                if (add == false) {
                    if (segmentLenght(lastSegment) <
                        segmentLenght(newSegment)) {
                        newSegments.pop_back();
                        add = true;
                    }
                }
            }
            if (add) {
                newSegments.push_back(newSegment);
            }
        }
    }
    segments.insert(segments.end(), newSegments.begin(), newSegments.end());
}
