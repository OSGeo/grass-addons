#include "houghtransform.h"

/* helpers */

struct SortByX {
    bool operator()(const HoughTransform::Coordinates &c1,
                    const HoughTransform::Coordinates &c2) const
    {

        return c1.first < c2.first;
    }
};

struct SortByY {
    bool operator()(const HoughTransform::Coordinates &c1,
                    const HoughTransform::Coordinates &c2) const
    {

        return c1.second < c2.second;
    }
};

/* ctors */

HoughTransform::HoughTransform(const Matrix &matrix,
                               const HoughParametres &parametrs)
    : mOriginalMatrix(matrix), mParams(parametrs)
{
    mNumR = mOriginalMatrix.rows();
    mNumC = mOriginalMatrix.columns();

    mThetas = ColumnVector(
        Range(-M_PI / 2.0, M_PI / 2.0, M_PI / 180.0).matrix_value());

    const float diag_length = std::sqrt(mNumR * mNumR + mNumC * mNumC);
    mNumBins = ceil(diag_length) - 1;

    mHoughMatrix = Matrix(mNumBins, mThetas.length(), 0.0);

    c_2 = ceil(mNumC / 2.);
    r_2 = ceil(mNumR / 2.);

    first_bins = 1 - ceil(mNumBins / 2.0);
}

/* functions */

void HoughTransform::compute()
{
    for (int x = 0; x < mNumR; x++) {
        for (int y = 0; y < mNumC; y++) {
            if (mOriginalMatrix(x, y) == 1) {
                computeHoughForXY(x, y, 0, mThetas.length());
            }
        }
    }
}

void HoughTransform::computeHoughForXY(int x, int y, size_t minIndex,
                                       size_t maxIndex)
{
    for (size_t i = minIndex; i < maxIndex; i++) {
        const double theta = mThetas(i);
        const double rho_d =
            std::cos(theta) * (x - c_2) + std::sin(theta) * (y - r_2);
        const int rho = floor(rho_d + 0.5);
        const int bin = rho - first_bins;

        if ((bin > 0) && (bin < mNumBins)) {
            mHoughMatrix(bin, i)++;
            mHoughMap[Coordinates(bin, i)].push_back(Coordinates(x, y));
            mOriginalMap[Coordinates(x, y)].push_back(Coordinates(bin, i));
        }
    }
}

/**
  Expecting angles to be in degrees in range [0,180).

  Size of agles matrix must be the same as size of input edge matrix.
  mNumR != angles.rows() && mNumC != angles.columns()
  */
void HoughTransform::compute(const Matrix &angles, double angleWith)
{
    for (int x = 0; x < mNumR; x++) {
        for (int y = 0; y < mNumC; y++) {
            if (mOriginalMatrix(x, y) == 1) {
                // gradient in mathematical axes
                double angle = angles(x, y);

                // unify gradients
                if (angle < 0)
                    angle += 180;

                // converting angle [0,180) to index
                // in internal table of angles
                // assuming that table size is 180
                // TODO: angleIndex = mThetas.length() * angle/180
                int angleIndex = angle;
                int angleShift = angleWith / 2 + 0.5;

                // FIXME: magic number
                int minIndex = angleIndex - angleShift;
                int maxIndex = angleIndex + angleShift;

                if (minIndex < 0) {
                    computeHoughForXY(x, y, 0, maxIndex);
                    minIndex = 180 + minIndex;
                    computeHoughForXY(x, y, minIndex, 180);
                }
                else if (maxIndex > 180) {
                    computeHoughForXY(x, y, minIndex, 180);
                    maxIndex = maxIndex - 180;
                    computeHoughForXY(x, y, 0, maxIndex);
                }
                else {
                    computeHoughForXY(x, y, minIndex, maxIndex);
                }
            }
        }
    }
}

void HoughTransform::findPeaks(int maxPeakNumber, int threshold,
                               int sizeOfNeighbourhood)
{
    int maxIt = mHoughMatrix.rows() * mHoughMatrix.columns();
    int peaksFound = 0;
    for (int i = 0; i < maxIt; i++) {
        Coordinates coordinates;
        int maxValue = findMax(mHoughMatrix, coordinates);

        if (maxValue < threshold || peaksFound == maxPeakNumber)
            break;

        CoordinatesList neighbours(
            neighbourhood(coordinates, sizeOfNeighbourhood));

        Coordinates beginLine, endLine;

        removePeakEffect(neighbours, beginLine, endLine);

        Peak peak(coordinates, maxValue, beginLine, endLine);
        mPeaks.push_back(peak);
        peaksFound++;
    }
}

HoughTransform::CoordinatesList
HoughTransform::neighbourhood(Coordinates &coordinates,
                              const int sizeOfNeighbourhood)
{
    CoordinatesList list;
    const int x = coordinates.first;
    const int y = coordinates.second;
    for (int i = -sizeOfNeighbourhood; i <= sizeOfNeighbourhood; i++) {
        for (int j = -sizeOfNeighbourhood; j <= sizeOfNeighbourhood; j++) {
            list.push_back(Coordinates(x + i, y + j));
        }
    }
    return list;
}

void HoughTransform::removePeakEffect(const CoordinatesList &neighbours,
                                      Coordinates &beginLine,
                                      Coordinates &endLine)
{
    CoordinatesList lineList;
    for (CoordinatesList::const_iterator it = neighbours.begin(),
                                         end = neighbours.end();
         it != end; ++it) {
        CoordinatesList &toRemove = mHoughMap[*it];

        for (CoordinatesList::const_iterator it1 = toRemove.begin(),
                                             end = toRemove.end();
             it1 != end; ++it1) {
            if (mOriginalMap.find(*it1) != mOriginalMap.end()) {
                CoordinatesList &toDecrease = mOriginalMap[*it1];

                for (CoordinatesList::const_iterator it2 = toDecrease.begin(),
                                                     end = toDecrease.end();
                     it2 != end; ++it2) {
                    mHoughMatrix(it2->first, it2->second)--;
                }
                mOriginalMap.erase(*it1);

                lineList.push_back(*it1);
            }
        }
    }
    int angle = neighbours.front().second;
    // what to do if find endpoints finds nothing reasonable?
    findEndPoints(lineList, beginLine, endLine, angle);
}

/** \param list[in, out] will be sorted by y cooridinate
  if angle is in range (45, 135] or by x otherwise
  */
bool HoughTransform::findEndPoints(CoordinatesList &list,
                                   Coordinates &beginLine, Coordinates &endLine,
                                   const value_type angle)
{
    if (angle > 45 && angle <= 135) {
        std::sort(list.begin(), list.end(), SortByY());
    }
    else {
        std::sort(list.begin(), list.end(), SortByX());
    }

    beginLine = list.front();
    endLine = list.back();

    return true;
}

int HoughTransform::findMax(const Matrix &matrix, Coordinates &coordinates)
{
    size_t rowIndex = 0;
    size_t colIndex;
    std::vector<size_t> colIndexes;

    std::vector<value_type> rowMax = matrix.row_max(colIndexes);

    int max = 0;
    for (size_t i = 0; i < rowMax.size(); i++) {
        int tmp = rowMax[i];
        if (tmp > max) {
            max = tmp;
            rowIndex = i;
        }
    }
    colIndex = colIndexes[rowIndex];

    coordinates.first = rowIndex;
    coordinates.second = colIndex;

    return max;
}
