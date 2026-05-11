use std::env;
use std::process;
use std::thread;
use std::time::Instant;

fn parse_positive(value: &str, name: &str) -> usize {
    match value.parse::<usize>() {
        Ok(parsed) if parsed > 0 => parsed,
        _ => {
            eprintln!("Invalid {name}: {value}");
            process::exit(1);
        }
    }
}

fn value_for(row: usize, col: usize) -> f64 {
    (((row + 1) * 31 + (col + 1) * 17) % 101) as f64 / 101.0
}

fn fill_matrices(n: usize) -> (Vec<f64>, Vec<f64>) {
    let mut a = vec![0.0; n * n];
    let mut b_transposed = vec![0.0; n * n];

    for row in 0..n {
        for col in 0..n {
            a[row * n + col] = value_for(row, col);
            b_transposed[col * n + row] = value_for(col, row);
        }
    }

    (a, b_transposed)
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {
        eprintln!("Usage: {} <threads> <matrix_size>", args[0]);
        process::exit(1);
    }

    let threads = parse_positive(&args[1], "threads");
    let n = parse_positive(&args[2], "matrix_size");
    let (a, b_transposed) = fill_matrices(n);
    let mut c = vec![0.0; n * n];
    let rows_per_thread = (n + threads - 1) / threads;

    let start = Instant::now();

    thread::scope(|scope| {
        for (chunk_id, c_chunk) in c.chunks_mut(rows_per_thread * n).enumerate() {
            let start_row = chunk_id * rows_per_thread;
            let a = &a;
            let b_transposed = &b_transposed;

            scope.spawn(move || {
                let rows_in_chunk = c_chunk.len() / n;

                for local_row in 0..rows_in_chunk {
                    let row = start_row + local_row;
                    let output_row = &mut c_chunk[local_row * n..(local_row + 1) * n];

                    for col in 0..n {
                        let a_row = &a[row * n..(row + 1) * n];
                        let b_col = &b_transposed[col * n..(col + 1) * n];
                        let mut sum = 0.0;

                        for k in 0..n {
                            sum += a_row[k] * b_col[k];
                        }

                        output_row[col] = sum;
                    }
                }
            });
        }
    });

    let elapsed_ms = start.elapsed().as_secs_f64() * 1000.0;
    let checksum: f64 = c.iter().sum();
    println!("rust,matrix_mul,{threads},{n},{elapsed_ms:.6},checksum={checksum:.6}");
}
