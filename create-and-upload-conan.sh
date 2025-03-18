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
DEBUG_MODE=false  # Debug mode flag

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
        --debug)
            DEBUG_MODE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --no-upload       Create packages only without uploading to remote"
            echo "  --profile=NAME    Specify build profile (default: default)"
            echo "  --debug           Enable debug mode with verbose output"
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
BLUE="\033[34m"
RESET="\033[0m"

# -- functions --

# Logging
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")

    # Цветовая схема для разных уровней логирования
    local color=""
    case $level in
        "INFO")
            color=$GREEN
            ;;
        "ERROR")
            color=$RED
            ;;
        "WARNING")
            color=$YELLOW
            ;;
        "DEBUG")
            color=$BLUE
            # В обычном режиме не выводим отладочные сообщения
            if [ "$DEBUG_MODE" != "true" ]; then
                echo -e "[$timestamp] [$level] $message" >> "$LOG_FILE"
                return
            fi
            ;;
    esac

    echo -e "[$timestamp] ${color}[$level]${RESET} $message" | tee -a "$LOG_FILE"
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

    # Debug: Показать профили Conan
    if [ "$DEBUG_MODE" = "true" ]; then
        log "DEBUG" "Available Conan profiles:"
        conan profile list
        log "DEBUG" "Content of $BUILD_PROFILE profile:"
        conan profile show $BUILD_PROFILE 2>/dev/null || log "DEBUG" "Profile $BUILD_PROFILE not found"
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

# Check for toolchain files in conan build directories
check_toolchain_files() {
    local package_name=$1
    local package_version=$2
    local stage=$3  # "before" or "after"

    log "DEBUG" "Checking for toolchain files $stage build for $package_name/$package_version"

    # Возможные пути к директории сборки
    local build_dirs=(
        "$HOME/.conan/data/$package_name/$package_version/$USER/$CHANNEL/build"
        "/github/home/.conan/data/$package_name/$package_version/$USER/$CHANNEL/build"
        ".conan/data/$package_name/$package_version/$USER/$CHANNEL/build"
    )

    for dir in "${build_dirs[@]}"; do
        if [ -d "$dir" ]; then
            log "DEBUG" "Found build directory: $dir"

            # Найти все папки с билдами
            find "$dir" -type d | while read -r build_dir; do
                # Проверить toolchain файлы
                local toolchain_files=$(find "$build_dir" -name "conan_toolchain.cmake" 2>/dev/null)
                if [ -n "$toolchain_files" ]; then
                    echo "$toolchain_files" | while read -r toolchain; do
                        log "DEBUG" "Found toolchain file: $toolchain"

                        # Проверить содержимое toolchain файла
                        log "DEBUG" "Toolchain file content (first 15 lines):"
                        head -n 15 "$toolchain" | while read -r line; do
                            log "DEBUG" "  $line"
                        done

                        log "DEBUG" "Checking critical settings in toolchain:"
                        grep -i "CMAKE_CXX_COMPILER" "$toolchain" | log "DEBUG"
                        grep -i "CMAKE_C_COMPILER" "$toolchain" | log "DEBUG"
                        grep -i "CMAKE_BUILD_TYPE" "$toolchain" | log "DEBUG"
                    done
                else
                    log "DEBUG" "No toolchain files found in $build_dir"
                fi

                # Проверить CMake логи
                local cmake_error_log=$(find "$build_dir" -name "CMakeError.log" 2>/dev/null | head -n 1)
                if [ -n "$cmake_error_log" ]; then
                    log "DEBUG" "Found CMake error log: $cmake_error_log"
                    log "DEBUG" "CMake error log content (last 30 lines):"
                    tail -n 30 "$cmake_error_log" | while read -r line; do
                        log "DEBUG" "  $line"
                    done
                fi
            done
        fi
    done
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
        echo "FAILURE REASON: Recipe directory not found for $package_name" >> .build_failures
        return 1
    fi

    # Проверка toolchain файлов до сборки
    if [ "$DEBUG_MODE" = "true" ]; then
        check_toolchain_files "$package_name" "$package_version" "before"
    fi

    # Сохраняем stdout и stderr в отдельные файлы для этого пакета
    local log_dir="build_logs"
    mkdir -p "$log_dir"
    local stdout_log="$log_dir/${package_name}_${package_version}_stdout.log"
    local stderr_log="$log_dir/${package_name}_${package_version}_stderr.log"

    # Запускаем сборку с сохранением логов
    local env_vars=""
    if [ "$DEBUG_MODE" = "true" ]; then
        env_vars="CONAN_LOGGING_LEVEL=debug CONAN_CMAKE_VERBOSE_MAKEFILE=1"
    fi

    # Четкий статус ошибки и подробные логи
    if eval $env_vars conan create "recipes/$package_name"/*/ "$package_ref" --build missing -pr:b=$BUILD_PROFILE > "$stdout_log" 2> "$stderr_log"; then
        log "SUCCESS" "Package $package_ref successfully created"
        echo "$package: SUCCESS" >> .build_results
        return 0
    else
        local exit_code=$?
        log "ERROR" "Failed to create package $package_ref (exit code: $exit_code)"
        log "ERROR" "See logs in $stdout_log and $stderr_log"

        # Сохраняем причину ошибки для отчетности
        echo "$package: FAILED (exit code: $exit_code)" >> .build_results

        # Если это otterbrix, сохраняем детальный лог ошибки
        if [[ "$package_name" == "otterbrix" ]]; then
            cat "$stderr_log" > "otterbrix_failure.log"
            echo "FAILURE REASON: See otterbrix_failure.log for details" >> .build_failures
        else
            echo "FAILURE REASON: Build failure with exit code $exit_code" >> .build_failures
        fi

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

    # Output summary с четким статусом
    echo
    echo -e "${GREEN}Operation summary:${RESET}"
    echo -e "Total packages: $total_count"
    echo -e "Successfully processed: $success_count"
    echo -e "Failed packages: $error_count"

    # Сохраняем четкий статус в файл вместо закодированных значений
    if [ $error_count -gt 0 ]; then
        echo -e "${RED}BUILD STATUS: FAILURE${RESET}"
        echo "BUILD STATUS: FAILURE" > .build_status
        return 1
    else
        echo -e "${GREEN}BUILD STATUS: SUCCESS${RESET}"
        echo "BUILD STATUS: SUCCESS" > .build_status
        return 0
    fi
}

# Main script function
main() {
    echo -e "${GREEN}=== Conan Package Creation and Upload ===${RESET}"
    echo "Execution started: $(date)" > "$LOG_FILE"
    echo -e "${YELLOW}Using build profile: $BUILD_PROFILE${RESET}"

    if [ "$DEBUG_MODE" = "true" ]; then
        echo -e "${BLUE}Debug mode enabled - verbose output will be shown${RESET}"
    fi

    # Environment checks
    check_conan
    check_remote

    # Prepare package list
    prepare_result_file

    # Check if there are packages to process
    if [ ! -s "$RESULT_FILE" ]; then
        echo -e "${GREEN}No packages to build - all packages are already built.${RESET}"
        echo "BUILD STATUS: NO_PACKAGES_NEEDED" > .build_status
        cleanup
        exit 0
    fi

    # Output list of packages to process
    echo -e "${GREEN}Packages for creation and upload:${RESET}"
    cat "$RESULT_FILE"
    echo -e "${GREEN}------------------------------------------${RESET}"

    # Create and upload packages
    local failed_packages=()

    for package in $(cat "$RESULT_FILE"); do
        echo -e "${YELLOW}Processing package: $package${RESET}"

        if create_package "$package"; then
            if $UPLOAD_PACKAGES; then
                if upload_package "$package"; then
                    echo -e "${GREEN}Package $package successfully created and uploaded${RESET}"
                    echo
                else
                    failed_packages+=("$package (upload error)")
                fi
            else
                echo -e "${GREEN}Package $package successfully created (upload disabled)${RESET}"
                echo
            fi
        else
            failed_packages+=("$package (creation error)")
        fi
    done

    # Check results
    check_results
    local result_code=$?

    # Output information about failed packages
    if [ ${#failed_packages[@]} -gt 0 ]; then
        echo -e "${RED}List of packages with errors:${RESET}"
        for pkg in "${failed_packages[@]}"; do
            echo -e "  - $pkg"
        done
    fi

    # Cleanup
    cleanup

    echo -e "${GREEN}Script completed. Details in file: $LOG_FILE${RESET}"

    # Возвращаем четкий статус
    exit $result_code
}

# Run main function
main "$@"
