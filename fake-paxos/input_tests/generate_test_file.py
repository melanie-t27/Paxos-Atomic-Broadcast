import random
import argparse

def generate_integers_to_file(file_name: str, num_integers: int, lower_bound: int, upper_bound: int) -> None:
    # Generates a file with random integers within a specified range, ensuring no duplicates.
    # Use a set to store unique integers
    unique_integers: set[int] = set()

    # Keep generating integers until we have enough unique ones
    while len(unique_integers) < num_integers:
        random_integer = random.randint(lower_bound, upper_bound)
        unique_integers.add(random_integer)  # Add to set (duplicates are ignored automatically)

    # Convert the set to a list and shuffle it for random order
    shuffled_integers = list(unique_integers)
    random.shuffle(shuffled_integers)

    # Write the unique integers to the file
    with open(file_name, 'w') as file:
        for integer in shuffled_integers:
            file.write(f"{integer}\n")
    
    print(f"{len(unique_integers)} unique integers have been written to {file_name}.")

def main():
    # Set up the argument parser
    parser = argparse.ArgumentParser(description="Generate a file with random integers.")
    parser.add_argument("file_name", type=str, help="Name of the output file.")
    parser.add_argument("num_integers", type=int, help="Number of integers to generate.")
    parser.add_argument("lower_bound", type=int, help="Lower bound for the integers.")
    parser.add_argument("upper_bound", type=int, help="Upper bound for the integers.")
    
    # Parse the arguments
    args = parser.parse_args()

    # Call the function with arguments
    generate_integers_to_file(args.file_name, args.num_integers, args.lower_bound, args.upper_bound)

if __name__ == "__main__":
    main()