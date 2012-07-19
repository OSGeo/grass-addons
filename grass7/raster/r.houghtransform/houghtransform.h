#ifndef HOUGHTRANSFORM_H
#define HOUGHTRANSFORM_H

#include "houghparameters.h"
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

    /* types */

    /** This is class to provide compatible syntax with \c std::list. */
    template <typename T>
    class Vector: public std::vector<T>
    {
    public:

        /**
          Maybe it would be better to replace by an overload of sort function for list.
          And use this function for list.
          */
        template <typename Comp>
        void sort(Comp comp)
        {
            std::sort(this->begin(), this->end(), comp);
        }
        /** only for convenience, with some compiler optimalisation overhead shouldn't be so high  */
        operator std::list<T>() const
        {
            std::list<T> tmp;
            tmp.insert(tmp.begin(), this->begin(), this->end());
            return tmp;
        }
    };

    typedef std::pair<int, int> Coordinates;
    typedef Vector<Coordinates> CoordinatesList;
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

    HoughTransform(const Matrix &matrix, const HoughParametres &parametrs);

    void compute();
    void compute(const Matrix& angles)
    {
        compute(angles, mParams.angleWidth);
    }
    void compute(const Matrix& angles, double angleWith);
    void findPeaks()
    {
        findPeaks(mParams.maxPeaksNum, mParams.threshold, mParams.sizeOfNeighbourhood);
    }
    void findPeaks(int maxPeakNumber, int threshold,
                   const int sizeOfNeighbourhood);

    /* getters */

    const Matrix & getHoughMatrix() const { return mHoughMatrix; }
    const Matrix & getOrigMatrix()  const { return mOriginalMatrix; }
    const Peaks & getPeaks() const { return mPeaks; }
    const TracebackMap & getHoughMap() const { return mHoughMap; }

private:

    /* functions */

    // some of these functions can be changed to non-member
    CoordinatesList neighbourhood(Coordinates &coordinates, const int sizeOfNeighbourhood);
    void removePeakEffect(const CoordinatesList &neighbours, Coordinates &beginLine, Coordinates &endLine);
    bool findEndPoints(CoordinatesList& list, Coordinates &beginLine, Coordinates &endLine, const int angle);
    int findMax(const Matrix& matrix, Coordinates &coordinates);
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

    HoughParametres mParams;
};


#endif // HOUGHTRANSFORM_H
