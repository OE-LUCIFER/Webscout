import subprocess
import argparse

def autollama(model_path, gguf_file):
    # Initialize command list
    command = ["bash", "./webscout/Extra/autollama.sh", "-m", model_path, "-g", gguf_file]

    # Execute the command
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Print the output and error in real-time
    for line in process.stdout:
        print(line, end='')

    for line in process.stderr:
        print(line, end='')

    process.wait()

def main():
    parser = argparse.ArgumentParser(description='Run autollama.sh to manage models with Ollama')
    parser.add_argument('-m', '--model_path', required=True, help='Set the path to the model')
    parser.add_argument('-g', '--gguf_file', required=True, help='Set the GGUF file name')
    args = parser.parse_args()

    try:
        autollama(args.model_path, args.gguf_file)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
