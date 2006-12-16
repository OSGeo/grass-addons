#ifndef RECORDH
#define RECORDH

typedef struct 
{
  unsigned long int occupied;
  float log_occupied;
  float size;
  float log_reciprocal_size;
  float d;
} tRecord;

#endif
