cat << "EOF"
Made with love in India
EOF

# Default values
MODEL_ID=""
USERNAME=""
TOKEN=""
QUANTIZATION_METHODS="q4_k_m,q5_k_m" # Default to "q4_k_m,q5_k_m" if not provided

# Display help/usage information
usage() {
  echo "Usage: $0 -m MODEL_ID [-u USERNAME] [-t TOKEN] [-q QUANTIZATION_METHODS]"
  echo
  echo "Options:"
  echo "  -m MODEL_ID                   Required: Set the HF model ID"
  echo "  -u USERNAME                   Optional: Set the username"
  echo "  -t TOKEN                      Optional: Set the token"
  echo "  -q QUANTIZATION_METHODS       Optional: Set the quantization methods (default: q4_k_m,q5_k_m)"
  echo "  -h                            Display this help and exit"
  echo
}

# Parse command-line options
while getopts ":m:u:t:q:h" opt; do
  case ${opt} in
    m )
      MODEL_ID=$OPTARG
      ;;
    u )
      USERNAME=$OPTARG
      ;;
    t )
      TOKEN=$OPTARG
      ;;
    q )
      QUANTIZATION_METHODS=$OPTARG
      ;;
    h )
      usage
      exit 0
      ;;
    \? )
      echo "Invalid Option: -$OPTARG" 1>&2
      usage
      exit 1
      ;;
    : )
      echo "Invalid Option: -$OPTARG requires an argument" 1>&2
      usage
      exit 1
      ;;
  esac
done
shift $((OPTIND -1))

# Ensure MODEL_ID is provided
if [ -z "$MODEL_ID" ]; then
    echo "Error: MODEL_ID is required."
    usage
    exit 1
fi

# # Echoing the arguments for checking
# echo "MODEL_ID: $MODEL_ID"
# echo "USERNAME: ${USERNAME:-'Not provided'}"
# echo "TOKEN: ${TOKEN:-'Not provided'}"
# echo "QUANTIZATION_METHODS: $QUANTIZATION_METHODS"

# Splitting string into an array for quantization methods, if provided
IFS=',' read -r -a QUANTIZATION_METHOD_ARRAY <<< "$QUANTIZATION_METHODS"
echo "Quantization Methods: ${QUANTIZATION_METHOD_ARRAY[@]}"

MODEL_NAME=$(echo "$MODEL_ID" | awk -F'/' '{print $NF}')




# ----------- llama.cpp setup block-----------
# Check if llama.cpp is already installed and skip the build step if it is
if [ ! -d "llama.cpp" ]; then
    echo "llama.cpp not found. Cloning and setting up..."
    git clone https://github.com/ggerganov/llama.cpp
    cd llama.cpp && git pull
    # Install required packages
    pip3 install -r requirements.txt
    # Build llama.cpp as it's freshly cloned
    if ! command -v nvcc &> /dev/null
    then
        echo "nvcc could not be found, building llama without LLAMA_CUBLAS"
        make clean && make
    else
        make clean && LLAMA_CUBLAS=1 make
    fi
    cd ..
else
    echo "llama.cpp found. Assuming it's already built and up to date."
    # Optionally, still update dependencies
    # cd llama.cpp && pip3 install -r requirements.txt && cd ..
fi
# ----------- llama.cpp setup block-----------




# Download model 
#todo : shall we put condition to check if model has been already downloaded? similar to autogguf?
echo "Downloading the model..."
huggingface-cli download "$MODEL_ID" --local-dir "./${MODEL_NAME}" --local-dir-use-symlinks False --revision main


# Convert to fp16
FP16="${MODEL_NAME}/${MODEL_NAME,,}.fp16.bin"
echo "Converting the model to fp16..."
python3 llama.cpp/convert-hf-to-gguf.py "$MODEL_NAME" --outtype f16 --outfile "$FP16"

# Quantize the model
echo "Quantizing the model..."
for METHOD in "${QUANTIZATION_METHOD_ARRAY[@]}"; do
    QTYPE="${MODEL_NAME}/${MODEL_NAME,,}.${METHOD^^}.gguf"
    ./llama.cpp/llama-quantize "$FP16" "$QTYPE" "$METHOD"
done


# Check if USERNAME and TOKEN are provided
if [[ -n "$USERNAME" && -n "$TOKEN" ]]; then

    # Login to Hugging Face
    echo "Logging in to Hugging Face..."
    huggingface-cli login --token "$TOKEN"


    # Uploading .gguf, .md files, and config.json
    echo "Uploading .gguf, .md files, and config.json..."


    # Define a temporary directory
    TEMP_DIR="./temp_upload_dir"

    # Create the temporary directory
    mkdir -p "${TEMP_DIR}"

    # Copy the specific files to the temporary directory
    find "./${MODEL_NAME}" -type f \( -name "*.gguf" -o -name "*.md" -o -name "config.json" \) -exec cp {} "${TEMP_DIR}/" \;

    # Upload the temporary directory to Hugging Face
    huggingface-cli upload "${USERNAME}/${MODEL_NAME}-GGUF" "${TEMP_DIR}" --private

    # Remove the temporary directory after upload
    rm -rf "${TEMP_DIR}"
    echo "Upload completed."
else
    echo "USERNAME and TOKEN must be provided for upload."
fi

echo "Script completed."