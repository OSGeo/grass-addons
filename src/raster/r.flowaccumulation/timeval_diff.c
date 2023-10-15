#include <stdlib.h>
#ifdef _MSC_VER
#include <winsock2.h>
#else
#include <sys/time.h>
#endif

/* https://www.linuxquestions.org/questions/programming-9/how-to-calculate-time-difference-in-milliseconds-in-c-c-711096/#post3475339
 */
long long timeval_diff(struct timeval *difference, struct timeval *end_time,
                       struct timeval *start_time)
{
    struct timeval temp_diff;

    if (difference == NULL)
        difference = &temp_diff;
    difference->tv_sec = end_time->tv_sec - start_time->tv_sec;
    difference->tv_usec = end_time->tv_usec - start_time->tv_usec;

    /* Using while instead of if below makes the code slightly more robust. */
    while (difference->tv_usec < 0) {
        difference->tv_usec += 1000000;
        difference->tv_sec -= 1;
    }
    return 1000000LL * difference->tv_sec + difference->tv_usec;
}
