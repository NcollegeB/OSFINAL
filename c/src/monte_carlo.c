#include <inttypes.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "common.h"

typedef struct
{
    long iterations;
    uint64_t seed;
    long hits;
} worker_args_t;

static uint64_t next_u64(uint64_t *state)
{
    uint64_t x = *state;

    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    *state = x;

    return x * UINT64_C(2685821657736338717);
}

static double next_unit_double(uint64_t *state)
{
    return (double)(next_u64(state) >> 11) * (1.0 / 9007199254740992.0);
}

static void *worker(void *arg)
{
    worker_args_t *args = (worker_args_t *)arg;
    uint64_t state = args->seed;
    long hits = 0;

    for (long i = 0; i < args->iterations; i++)
    {
        double x = next_unit_double(&state);
        double y = next_unit_double(&state);

        if ((x * x) + (y * y) <= 1.0)
        {
            hits++;
        }
    }

    args->hits = hits;
    return NULL;
}

int main(int argc, char **argv)
{
    long threads;
    long points;
    pthread_t *thread_ids;
    worker_args_t *args;
    long base_iterations;
    long remainder;
    long total_hits = 0;
    double start;
    double elapsed;
    double pi;
    char extra[64];

    if (argc != 3)
    {
        fprintf(stderr, "Usage: %s <threads> <points>\n", argv[0]);
        return EXIT_FAILURE;
    }

    threads = parse_positive_long(argv[1], "threads");
    points = parse_positive_long(argv[2], "points");

    thread_ids = calloc((size_t)threads, sizeof(*thread_ids));
    args = calloc((size_t)threads, sizeof(*args));
    if (thread_ids == NULL || args == NULL)
    {
        perror("calloc");
        free(thread_ids);
        free(args);
        return EXIT_FAILURE;
    }

    base_iterations = points / threads;
    remainder = points % threads;

    start = monotonic_seconds();

    for (long i = 0; i < threads; i++)
    {
        int error_number;

        args[i].iterations = base_iterations + (i < remainder ? 1 : 0);
        args[i].seed = UINT64_C(0x9e3779b97f4a7c15) ^ (uint64_t)(i + 1);
        args[i].hits = 0;

        error_number = pthread_create(&thread_ids[i], NULL, worker, &args[i]);
        if (error_number != 0)
        {
            fprintf(stderr, "pthread_create: %s\n", strerror(error_number));
            free(thread_ids);
            free(args);
            return EXIT_FAILURE;
        }
    }

    for (long i = 0; i < threads; i++)
    {
        int error_number = pthread_join(thread_ids[i], NULL);
        if (error_number != 0)
        {
            fprintf(stderr, "pthread_join: %s\n", strerror(error_number));
            free(thread_ids);
            free(args);
            return EXIT_FAILURE;
        }
        total_hits += args[i].hits;
    }

    elapsed = monotonic_seconds() - start;
    pi = 4.0 * ((double)total_hits / (double)points);
    snprintf(extra, sizeof(extra), "pi=%.8f", pi);
    print_csv_result("c", "monte_carlo", threads, points, elapsed, extra);

    free(thread_ids);
    free(args);
    return EXIT_SUCCESS;
}

