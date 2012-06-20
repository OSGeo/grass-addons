#ifndef HOUGHTRANSFORM_H
#define HOUGHTRANSFORM_H

#include "matrix.h"

#include <cmath>
#include <vector>
#include <list>
#include <set>
#include <map>
#include <limits>
#include <algorithm>

#include <stdio.h>

using namespace matrix;

class HoughTransform
{
public:

    /* typedefs */

    template <typename T>
    class MyVector: public std::vector<T>
    {
    public:
        template <typename Comp>
        void sort(Comp comp)
        {
            std::sort(this->begin(), this->end(), comp);
        }
        operator std::list<T>() const
        {
            std::list<T> tmp;
            tmp.insert(tmp.begin(), this->begin(), this->end());
            return tmp;
        }
    };

    typedef std::pair<int, int> Coordinates;
    typedef MyVector<Coordinates> CoordinatesList;
    typedef std::map<Coordinates, CoordinatesList> TracebackMap;

    struct Peak
    {
        Peak(Coordinates coordinates, int value, Coordinates begin, Coordinates end)
            : coordinates(coordinates), value(value), beginLine(begin), endLine(end)
        {}
        Coordinates coordinates;
        int value;
        Coordinates beginLine;
        Coordinates endLine;
    };

    typedef std::vector<Peak> Peaks;

    /* functions */

    HoughTransform(const Matrix &matrix);

    void compute();
    void compute(const Matrix& angles, double angleWith);
    void findPeaks(int maxPeakNumber, int threshold,
                   const int sizeOfNeighbourhood);

    /* getters */

    const Matrix & getHoughMatrix() { return mHoughMatrix; }
    const Matrix & getOrigMatrix() { return mOriginalMatrix; }
    const Peaks & getPeaks() const { return mPeaks; }
    const TracebackMap & getHoughMap() { return mHoughMap; }

private:

    /* functions */

    CoordinatesList neighbourhood(Coordinates &coordinates, const int sizeOfNeighbourhood);
    void removePeakEffect(const CoordinatesList &neighbours, Coordinates &beginLine, Coordinates &endLine);
    bool findEndPoints(CoordinatesList list, Coordinates &beginLine, Coordinates &endLine, const int angle );
    int findMax(const Matrix& matrix, Coordinates &coordinates);
    void addToMaps(const std::vector<std::pair<Coordinates, Coordinates> > &pairs);
    void computeHoughForXY(int x, int y, size_t minIndex, size_t maxIndex);

    /* data members */

    const Matrix& mOriginalMatrix;
    Matrix mHoughMatrix;
    TracebackMap mOriginalMap;
    TracebackMap mHoughMap;
    Peaks mPeaks;

    int mNumR;
    int mNumC;
    ColumnVector mThetas;
    int mNumBins;
    int c2;
    int r2;
    int bins0;
};


#endif // HOUGHTRANSFORM_H
