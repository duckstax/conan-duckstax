#!/bin/bash

# -- variables --
CONAN_REMOTE="duckstax"
RESULT_FILE="result.txt"
TMP_FILE="tmp.txt"
REQ_SEQ_FILE="req-seq.txt"
UPLOADED_PACKAGES="uploaded_packages.txt"
ERROR_FILE="error.txt"
LOG_FILE="conan_operation.log"
USER="duckstax"
CHANNEL="stable"
UPLOAD_PACKAGES=true  # By default, packages are uploaded
BUILD_PROFILE="default"  # Default build profile

# Command line arguments processing
for arg in "$@"; do
    case $arg in
        --no-upload)
            UPLOAD_PACKAGES=false
            shift
            ;;
        --profile=*)
            BUILD_PROFILE="${arg#*=}"
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --no-upload       Create packages only without uploading to remote"
            echo "  --profile=NAME    Specify build profile (default: default)"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            # Unknown parameter
            ;;
    esac
done

# -- colors --
GREEN="\033[32m"
RED="\033[31m"
YELLOW="\033[33m"
RESET="\033[0m"

# -- functions --

# Logging
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")

    echo -e "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Check if Conan is installed
check_conan() {
    if ! command -v conan &> /dev/null; then
        log "ERROR" "Conan is not installed. Please install Conan before running this script."
        exit 1
    fi

    # Check Conan version (should be v1.x)
    local version=$(conan --version | grep -oP '(?<=Conan version )[0-9]+\.[0-9]+\.[0-9]+')
    local major_version=$(echo $version | cut -d. -f1)

    if [[ "$major_version" != "1" ]]; then
        log "WARNING" "Detected Conan version $version. This script is intended for Conan v1.x"
        read -p "Continue execution? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log "INFO" "Using Conan version $version"
    fi
}

# Check remote repository
check_remote() {
    log "INFO" "Checking remote repository $CONAN_REMOTE"

    if ! conan remote list | grep -q "$CONAN_REMOTE"; then
        log "ERROR" "Remote repository $CONAN_REMOTE not found"
        read -p "Would you like to add this repository? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            read -p "Enter URL for repository $CONAN_REMOTE: " repo_url
            conan remote add "$CONAN_REMOTE" "$repo_url"
            if [ $? -ne 0 ]; then
                log "ERROR" "Failed to add repository"
                exit 1
            fi
            log "INFO" "Repository $CONAN_REMOTE successfully added"
        else
            exit 1
        fi
    fi
}

# Clean up temporary files
cleanup() {
    log "INFO" "Cleaning up temporary files"
    rm -f "$TMP_FILE" "$UPLOADED_PACKAGES" 2>/dev/null
}

# Prepare result file with packages that need to be uploaded
prepare_result_file() {
    log "INFO" "Preparing list of packages to process"

    # Check if req-seq.txt file exists
    if [ ! -f "$REQ_SEQ_FILE" ]; then
        log "ERROR" "File $REQ_SEQ_FILE not found"
        exit 1
    fi

    # Get list of already uploaded packages from remote repository
    if ! conan search -r="$CONAN_REMOTE" "*" > "$TMP_FILE" 2>/dev/null; then
        log "ERROR" "Failed to get package list from remote repository"
        exit 1
    fi

    # Remove header line
    sed -i '1d' "$TMP_FILE"

    # Extract package names
    touch "$UPLOADED_PACKAGES"
    while IFS= read -r str; do
        if grep -q "/" <<< "$str"; then
            echo "$str" >> "$UPLOADED_PACKAGES"
        fi
    done < "$TMP_FILE"

    # Compare and create list of packages for upload
    if [ -s "$UPLOADED_PACKAGES" ]; then
        grep -F -x -v -f "$UPLOADED_PACKAGES" "$REQ_SEQ_FILE" > "$RESULT_FILE"
    else
        cp "$REQ_SEQ_FILE" "$RESULT_FILE"
    fi

    # Remove empty lines
    sed -i '/^$/d' "$RESULT_FILE"

    # Count packages to process
    local count=$(wc -l < "$RESULT_FILE")
    log "INFO" "Found $count packages to process"
}

# Create package
create_package() {
    local package="$1"

    if [ -z "$package" ]; then
        log "ERROR" "Empty package name passed"
        return 1
    fi

    local package_name=${package%/*}
    local package_version=${package#*/}
    local package_ref="${package}@${USER}/${CHANNEL}"

    log "INFO" "Creating package $package_ref with build profile $BUILD_PROFILE"

    # Check if recipe directory exists
    if [ ! -d "recipes/$package_name" ]; then
        log "ERROR" "Directory recipes/$package_name not found"
        return 1
    fi

    # Create package with specified build profile
    if conan create "recipes/$package_name"/*/ "$package_ref" --build missing -pr:b=$BUILD_PROFILE; then
        log "SUCCESS" "Package $package_ref successfully created"
        return 0
    else
        log "ERROR" "Failed to create package $package_ref"
        return 1
    fi
}

# Upload package
upload_package() {
    local package="$1"

    if [ -z "$package" ]; then
        log "ERROR" "Empty package name passed"
        return 1
    fi

    local package_ref="${package}@${USER}/${CHANNEL}"

    log "INFO" "Uploading package $package_ref to repository $CONAN_REMOTE"

    # Upload package
    if conan upload "$package_ref" -r "$CONAN_REMOTE" --all --confirm; then
        log "SUCCESS" "Package $package_ref successfully uploaded"
        return 0
    else
        log "ERROR" "Failed to upload package $package_ref"
        return 1
    fi
}

# Check results
check_results() {
    local error_count=0
    local success_count=0
    local total_count=$(wc -l < "$RESULT_FILE")

    echo
    log "INFO" "Checking operation results"

    if $UPLOAD_PACKAGES; then
        # Check uploaded packages
        for package in $(cat "$RESULT_FILE"); do
            local package_ref="${package}@${USER}/${CHANNEL}"
            if conan search -r="$CONAN_REMOTE" "$package_ref" &>/dev/null; then
                ((success_count++))
            else
                ((error_count++))
                echo -e "${RED}Error: $package_ref not found in repository${RESET}"
            fi
        done
    else
        # Check only locally created packages
        for package in $(cat "$RESULT_FILE"); do
            local package_ref="${package}@${USER}/${CHANNEL}"
            if conan search "$package_ref" &>/dev/null; then
                ((success_count++))
            else
                ((error_count++))
                echo -e "${RED}Error: $package_ref not found locally${RESET}"
            fi
        done
    fi

    # Output summary
    echo
    echo -e "${GREEN}Operation summary:${RESET}"
    echo -e "Total packages: $total_count"
    echo -e "Successfully processed: $success_count"
    if [ $error_count -gt 0 ]; then
        echo -e "${RED}Errors: $error_count${RESET}"
        echo "recipes_create_result=err" > .create_result_tmp
    else
        echo -e "${GREEN}Errors: $error_count${RESET}"
        echo "recipes_create_result=success" > .create_result_tmp
    fi

    log "INFO" "Operations completed. Success: $success_count, Errors: $error_count"
}

# Main script function
main() {
    echo -e "${GREEN}=== Conan Package Creation and Upload ===${RESET}"
    echo "Execution started: $(date)" > "$LOG_FILE"
    echo -e "${YELLOW}Using build profile: $BUILD_PROFILE${RESET}"

    # Environment checks
    check_conan
    check_remote

    # Prepare package list
    prepare_result_file

    # Check if there are packages to process
    if [ ! -s "$RESULT_FILE" ]; then
        echo -e "${GREEN}-> No packages to upload, all required packages are already uploaded.${RESET}"
        echo "recipes_create_result=ntu" > .create_result_tmp
        cleanup
        exit 0
    fi

    # Output list of packages to process
    echo -e "${GREEN}Packages for creation and upload:${RESET}"
    cat "$RESULT_FILE"
    echo -e "${GREEN}------------------------------------------${RESET}"

    # Create and upload packages
    local failed_packages=""

    for package in $(cat "$RESULT_FILE"); do
        echo -e "${YELLOW}Processing package: $package${RESET}"

        if create_package "$package"; then
            if $UPLOAD_PACKAGES; then
                if upload_package "$package"; then
                    echo -e "${GREEN}Package $package successfully created and uploaded${RESET}"
                    echo
                else
                    failed_packages="$failed_packages\n$package (upload error)"
                fi
            else
                echo -e "${GREEN}Package $package successfully created (upload disabled)${RESET}"
                echo
            fi
        else
            failed_packages="$failed_packages\n$package (creation error)"
        fi
    done

    # Check results
    check_results

    # Output information about failed packages
    if [ ! -z "$failed_packages" ]; then
        echo -e "${RED}List of packages with errors:${RESET}"
        echo -e "$failed_packages" | sed '/^$/d'
    fi

    # Cleanup
    cleanup

    echo -e "${GREEN}Script completed. Details in file: $LOG_FILE${RESET}"
}

# Run main function
main "$@"
