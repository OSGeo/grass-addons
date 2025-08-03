#ifndef HOUGHPARAMETERS_H
#define HOUGHPARAMETERS_H

struct HoughParametres {
    double angleWidth;
    int maxPeaksNum;
    int threshold;
    int sizeOfNeighbourhood;
};

struct ExtractParametres {
    int gapSize;
    int maxNumOfGaps;
    int maxGap;
    int lineLength;
    int lineWidth;
};

#endif // HOUGHPARAMETERS_H
