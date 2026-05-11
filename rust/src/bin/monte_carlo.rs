use std::env;
use std::process;
use std::thread;
use std::time::Instant;

fn parse_positive(value: &str, name: &str) -> u64 {
    match value.parse::<u64>() {
        Ok(parsed) if parsed > 0 => parsed,
        _ => {
            eprintln!("Invalid {name}: {value}");
            process::exit(1);
        }
    }
}

fn next_u64(state: &mut u64) -> u64 {
    let mut x = *state;
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    *state = x;
    x.wrapping_mul(2_685_821_657_736_338_717)
}

fn next_unit_double(state: &mut u64) -> f64 {
    ((next_u64(state) >> 11) as f64) * (1.0 / 9_007_199_254_740_992.0)
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {
        eprintln!("Usage: {} <threads> <points>", args[0]);
        process::exit(1);
    }

    let threads = parse_positive(&args[1], "threads") as usize;
    let points = parse_positive(&args[2], "points");
    let base_iterations = points / threads as u64;
    let remainder = points % threads as u64;

    let start = Instant::now();
    let mut handles = Vec::with_capacity(threads);

    for thread_id in 0..threads {
        let iterations = base_iterations + u64::from((thread_id as u64) < remainder);
        handles.push(thread::spawn(move || {
            let mut state = 0x9e37_79b9_7f4a_7c15_u64 ^ ((thread_id as u64) + 1);
            let mut hits = 0_u64;

            for _ in 0..iterations {
                let x = next_unit_double(&mut state);
                let y = next_unit_double(&mut state);
                if (x * x) + (y * y) <= 1.0 {
                    hits += 1;
                }
            }

            hits
        }));
    }

    let total_hits: u64 = handles
        .into_iter()
        .map(|handle| handle.join().expect("worker thread panicked"))
        .sum();

    let elapsed_ms = start.elapsed().as_secs_f64() * 1000.0;
    let pi = 4.0 * (total_hits as f64 / points as f64);
    println!("rust,monte_carlo,{threads},{points},{elapsed_ms:.6},pi={pi:.8}");
}
