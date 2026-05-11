#ifndef OSFINAL_COMMON_H
#define OSFINAL_COMMON_H

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static double monotonic_seconds(void)
{
    struct timespec ts;

    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0)
    {
        perror("clock_gettime");
        exit(EXIT_FAILURE);
    }

    return (double)ts.tv_sec + ((double)ts.tv_nsec / 1000000000.0);
}

static long parse_positive_long(const char *text, const char *name)
{
    char *end = NULL;
    long value;

    errno = 0;
    value = strtol(text, &end, 10);

    if (errno != 0 || end == text || *end != '\0' || value <= 0)
    {
        fprintf(stderr, "Invalid %s: %s\n", name, text);
        exit(EXIT_FAILURE);
    }

    return value;
}

static void print_csv_result(
    const char *language,
    const char *algorithm,
    long threads,
    long workload,
    double elapsed_seconds,
    const char *extra)
{
    printf("%s,%s,%ld,%ld,%.6f,%s\n",
           language,
           algorithm,
           threads,
           workload,
           elapsed_seconds * 1000.0,
           extra);
}

#endif
