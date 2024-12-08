import random
import argparse

def generate_integers_to_file(file_name: str, num_integers: int, lower_bound: int, upper_bound: int) -> None:
    # Generates a file with random integers within a specified range, ensuring no duplicates.
    # Ensure the range can accommodate the requested number of integers
    if upper_bound - lower_bound + 1 < num_integers:
        raise ValueError("Range is too small to generate the requested number of unique integers.")
    
    # Generate the full range, shuffle, and take the first `num_integers`
    all_integers = list(range(lower_bound, upper_bound + 1))
    random.shuffle(all_integers)
    selected_integers = all_integers[:num_integers]

    # Write the selected integers to the file
    with open(file_name, 'w') as file:
        for integer in selected_integers:
            file.write(f"{integer}\n")
    
    print(f"{num_integers} unique integers have been written to {file_name}.")


def generate_integers_to_file_with_duplicates(file_name: str, num_integers: int, lower_bound: int, upper_bound: int) -> None:
    if lower_bound > upper_bound:
        raise ValueError("Lower bound cannot be greater than upper bound.")
    
    # Generate `num_integers` random integers with potential duplicates
    random_integers = [random.randint(lower_bound, upper_bound) for _ in range(num_integers)]
    
    # Write the generated integers to the file
    with open(file_name, 'w') as file:
        for integer in random_integers:
            file.write(f"{integer}\n")
    
    print(f"{num_integers} integers (with possible duplicates) have been written to {file_name}.")


def main():
    # Set up the argument parser
    parser = argparse.ArgumentParser(description="Generate a file with random integers.")
    parser.add_argument("file_name", type=str, help="Name of the output file.")
    parser.add_argument("num_integers", type=int, help="Number of integers to generate.")
    parser.add_argument("--lower_bound", type=int, default=1, help="Lower bound for the integers.")
    parser.add_argument("--upper_bound", type=int, default=None, help="Upper bound for the integers.")
    parser.add_argument("--duplicate", type=bool, default=False, help="Upper bound for the integers.")

    # Parse the arguments
    args = parser.parse_args()

    # If upper_bound is not specified than set it to the exact number of integer
    if args.upper_bound == None:
        args.upper_bound = args.num_integers + args.lower_bound

    # Call the function with arguments
    if args.duplicate:
        generate_integers_to_file_with_duplicates(args.file_name, args.num_integers, args.lower_bound, args.upper_bound)
    else: 
        generate_integers_to_file(args.file_name, args.num_integers, args.lower_bound, args.upper_bound)

if __name__ == "__main__":
    main()