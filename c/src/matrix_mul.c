#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "common.h"

typedef struct
{
    long start_row;
    long end_row;
    long n;
    const double *a;
    const double *b_transposed;
    double *c;
} worker_args_t;

static double value_for(long row, long col)
{
    return (double)(((row + 1) * 31 + (col + 1) * 17) % 101) / 101.0;
}

static void fill_matrices(double *a, double *b, double *b_transposed, long n)
{
    for (long row = 0; row < n; row++)
    {
        for (long col = 0; col < n; col++)
        {
            a[row * n + col] = value_for(row, col);
            b[row * n + col] = value_for(col, row);
            b_transposed[col * n + row] = b[row * n + col];
        }
    }
}

static void *worker(void *arg)
{
    worker_args_t *args = (worker_args_t *)arg;
    long n = args->n;

    for (long row = args->start_row; row < args->end_row; row++)
    {
        for (long col = 0; col < n; col++)
        {
            double sum = 0.0;
            const double *a_row = &args->a[row * n];
            const double *b_col = &args->b_transposed[col * n];

            for (long k = 0; k < n; k++)
            {
                sum += a_row[k] * b_col[k];
            }

            args->c[row * n + col] = sum;
        }
    }

    return NULL;
}

int main(int argc, char **argv)
{
    long threads;
    long n;
    size_t elements;
    double *a;
    double *b;
    double *b_transposed;
    double *c;
    pthread_t *thread_ids;
    worker_args_t *args;
    double start;
    double elapsed;
    double checksum = 0.0;
    char extra[80];
    long rows_per_thread;

    if (argc != 3)
    {
        fprintf(stderr, "Usage: %s <threads> <matrix_size>\n", argv[0]);
        return EXIT_FAILURE;
    }

    threads = parse_positive_long(argv[1], "threads");
    n = parse_positive_long(argv[2], "matrix_size");
    elements = (size_t)n * (size_t)n;

    a = malloc(elements * sizeof(*a));
    b = malloc(elements * sizeof(*b));
    b_transposed = malloc(elements * sizeof(*b_transposed));
    c = calloc(elements, sizeof(*c));
    thread_ids = calloc((size_t)threads, sizeof(*thread_ids));
    args = calloc((size_t)threads, sizeof(*args));

    if (a == NULL || b == NULL || b_transposed == NULL || c == NULL ||
        thread_ids == NULL || args == NULL)
    {
        perror("allocation");
        free(a);
        free(b);
        free(b_transposed);
        free(c);
        free(thread_ids);
        free(args);
        return EXIT_FAILURE;
    }

    fill_matrices(a, b, b_transposed, n);
    rows_per_thread = (n + threads - 1) / threads;

    start = monotonic_seconds();

    for (long i = 0; i < threads; i++)
    {
        int error_number;
        long start_row = i * rows_per_thread;
        long end_row = start_row + rows_per_thread;

        if (end_row > n)
        {
            end_row = n;
        }

        args[i].start_row = start_row;
        args[i].end_row = end_row;
        args[i].n = n;
        args[i].a = a;
        args[i].b_transposed = b_transposed;
        args[i].c = c;

        error_number = pthread_create(&thread_ids[i], NULL, worker, &args[i]);
        if (error_number != 0)
        {
            fprintf(stderr, "pthread_create: %s\n", strerror(error_number));
            free(a);
            free(b);
            free(b_transposed);
            free(c);
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
            free(a);
            free(b);
            free(b_transposed);
            free(c);
            free(thread_ids);
            free(args);
            return EXIT_FAILURE;
        }
    }

    elapsed = monotonic_seconds() - start;

    for (size_t i = 0; i < elements; i++)
    {
        checksum += c[i];
    }

    snprintf(extra, sizeof(extra), "checksum=%.6f", checksum);
    print_csv_result("c", "matrix_mul", threads, n, elapsed, extra);

    free(a);
    free(b);
    free(b_transposed);
    free(c);
    free(thread_ids);
    free(args);
    return EXIT_SUCCESS;
}
