use std::env;
use std::fs;
use std::net::ToSocketAddrs;
use std::process;
use std::sync::Arc;
use std::thread;
use std::time::Instant;

fn parse_positive(value: &str, name: &str) -> usize
{
    match value.parse::<usize>()
    {
        Ok(parsed) if parsed > 0 => parsed,
        _ =>
        {
            eprintln!("Invalid {name}: {value}");
            process::exit(1);
        }
    }
}

fn read_hostnames(path: &str) -> Vec<String>
{
    let contents = fs::read_to_string(path).unwrap_or_else(|error|
    {
        eprintln!("{path}: {error}");
        process::exit(1);
    });

    contents
        .lines()
        .map(str::trim)
        .filter(|line| !line.is_empty())
        .map(str::to_owned)
        .collect()
}

fn resolves(hostname: &str) -> bool
{
    (hostname, 0)
        .to_socket_addrs()
        .map(|mut addresses| addresses.next().is_some())
        .unwrap_or(false)
}

fn main()
{
    let args: Vec<String> = env::args().collect();
    if args.len() != 3
    {
        eprintln!("Usage: {} <threads> <hostname_file>", args[0]);
        process::exit(1);
    }

    let threads = parse_positive(&args[1], "threads");
    let hostnames = read_hostnames(&args[2]);
    if hostnames.is_empty()
    {
        eprintln!("No hostnames found in {}", args[2]);
        process::exit(1);
    }

    let count = hostnames.len();
    let hostnames = Arc::new(hostnames);
    let start = Instant::now();
    let mut handles = Vec::with_capacity(threads);

    for thread_id in 0..threads
    {
        let hostnames = Arc::clone(&hostnames);
        handles.push(thread::spawn(move ||
        {
            let mut resolved = 0_usize;
            let mut i = thread_id;

            while i < hostnames.len()
            {
                if resolves(&hostnames[i])
                {
                    resolved += 1;
                }
                i += threads;
            }

            resolved
        }));
    }

    let resolved: usize = handles
        .into_iter()
        .map(|handle| handle.join().expect("worker thread panicked"))
        .sum();

    let elapsed_ms = start.elapsed().as_secs_f64() * 1000.0;
    println!("rust,dns_lookup,{threads},{count},{elapsed_ms:.6},resolved={resolved}");
}
