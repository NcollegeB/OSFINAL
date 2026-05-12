/*
 * DNS lookup benchmark using POSIX threads.
 * This file was generated with help from AI and reviewed by the author.
 */

#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 200809L
#endif

#include <netdb.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "common.h"

typedef struct
{
    long thread_id;
    long threads;
    long count;
    char **hostnames;
    long resolved;
} worker_args_t;

static void trim_line(char *line)
{
    size_t length = strlen(line);

    while (length > 0 && (line[length - 1] == '\n' || line[length - 1] == '\r'))
    {
        line[length - 1] = '\0';
        length--;
    }
}

static char **read_hostnames(const char *path, long *out_count)
{
    FILE *file = fopen(path, "r");
    char buffer[1024];
    long count = 0;
    long capacity = 64;
    char **hostnames;

    if (file == NULL)
    {
        perror(path);
        exit(EXIT_FAILURE);
    }

    hostnames = malloc((size_t)capacity * sizeof(*hostnames));
    if (hostnames == NULL)
    {
        perror("malloc");
        fclose(file);
        exit(EXIT_FAILURE);
    }

    while (fgets(buffer, sizeof(buffer), file) != NULL)
    {
        trim_line(buffer);
        if (buffer[0] == '\0')
        {
            continue;
        }

        /* Grow the hostname list as needed so input files can vary in size. */
        if (count == capacity)
        {
            char **grown;
            capacity *= 2;
            grown = realloc(hostnames, (size_t)capacity * sizeof(*hostnames));
            if (grown == NULL)
            {
                perror("realloc");
                fclose(file);
                for (long i = 0; i < count; i++)
                {
                    free(hostnames[i]);
                }
                free(hostnames);
                exit(EXIT_FAILURE);
            }
            hostnames = grown;
        }

        hostnames[count] = strdup(buffer);
        if (hostnames[count] == NULL)
        {
            perror("strdup");
            fclose(file);
            for (long i = 0; i < count; i++)
            {
                free(hostnames[i]);
            }
            free(hostnames);
            exit(EXIT_FAILURE);
        }
        count++;
    }

    fclose(file);
    *out_count = count;
    return hostnames;
}

static int resolve_hostname(const char *hostname)
{
    struct addrinfo hints;
    struct addrinfo *result = NULL;
    int status;

    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    /* getaddrinfo uses the system resolver, which is the behavior being timed. */
    status = getaddrinfo(hostname, NULL, &hints, &result);
    if (status == 0)
    {
        freeaddrinfo(result);
        return 1;
    }

    return 0;
}

static void *worker(void *arg)
{
    worker_args_t *args = (worker_args_t *)arg;
    long resolved = 0;

    for (long i = args->thread_id; i < args->count; i += args->threads)
    {
        resolved += resolve_hostname(args->hostnames[i]);
    }

    args->resolved = resolved;
    return NULL;
}

int main(int argc, char **argv)
{
    long threads;
    long count = 0;
    char **hostnames;
    pthread_t *thread_ids;
    worker_args_t *args;
    long resolved = 0;
    double start;
    double elapsed;
    char extra[64];

    if (argc != 3)
    {
        fprintf(stderr, "Usage: %s <threads> <hostname_file>\n", argv[0]);
        return EXIT_FAILURE;
    }

    threads = parse_positive_long(argv[1], "threads");
    hostnames = read_hostnames(argv[2], &count);
    if (count == 0)
    {
        fprintf(stderr, "No hostnames found in %s\n", argv[2]);
        free(hostnames);
        return EXIT_FAILURE;
    }

    thread_ids = calloc((size_t)threads, sizeof(*thread_ids));
    args = calloc((size_t)threads, sizeof(*args));
    if (thread_ids == NULL || args == NULL)
    {
        perror("calloc");
        free(thread_ids);
        free(args);
        for (long i = 0; i < count; i++)
        {
            free(hostnames[i]);
        }
        free(hostnames);
        return EXIT_FAILURE;
    }

    /* Timing includes threaded resolver calls and thread overhead. */
    start = monotonic_seconds();

    /* Thread IDs stride through the shared hostname list without mutation. */
    for (long i = 0; i < threads; i++)
    {
        int error_number;

        args[i].thread_id = i;
        args[i].threads = threads;
        args[i].count = count;
        args[i].hostnames = hostnames;
        args[i].resolved = 0;

        error_number = pthread_create(&thread_ids[i], NULL, worker, &args[i]);
        if (error_number != 0)
        {
            fprintf(stderr, "pthread_create: %s\n", strerror(error_number));
            for (long j = 0; j < count; j++)
            {
                free(hostnames[j]);
            }
            free(hostnames);
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
            for (long j = 0; j < count; j++)
            {
                free(hostnames[j]);
            }
            free(hostnames);
            free(thread_ids);
            free(args);
            return EXIT_FAILURE;
        }
        resolved += args[i].resolved;
    }

    elapsed = monotonic_seconds() - start;
    snprintf(extra, sizeof(extra), "resolved=%ld", resolved);
    print_csv_result("c", "dns_lookup", threads, count, elapsed, extra);

    /* Hostnames were duplicated while reading the file, so free each string. */
    for (long i = 0; i < count; i++)
    {
        free(hostnames[i]);
    }
    free(hostnames);
    free(thread_ids);
    free(args);
    return EXIT_SUCCESS;
}
