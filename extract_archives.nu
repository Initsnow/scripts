#!/usr/bin/env nu

# extract_archives.nu
# This script traverses a directory for compressed files, extracts them using 7zip
# to a folder named after the file (without extension), and deletes the original
# archive if extraction was successful.

def main [
    dir?: string = "."  # Default to current directory if not specified
] {
    # Get all compressed files in the directory
    let compressed_files = (
        ls $dir 
        | where type == file 
        | where name =~ '\.(zip|rar|7z|tar|gz|bz2|xz)$'
        | get name
    )
    
    if ($compressed_files | is-empty) {
        print "No compressed files found in directory: ($dir)"
        return
    }
    
    print $"Found ($compressed_files | length) compressed files to extract"
    
    # Process each compressed file
    for file in $compressed_files {
        let full_path = (if $dir == "." { $file } else { $"($dir)/($file)" })
        let file_name = ($file | path basename)
        let file_stem = ($file | path parse | get stem)
        let extract_dir = (if $dir == "." { $file_stem } else { $"($dir)/($file_stem)" })
        
        print $"Processing: ($file_name)"
        
        # Create extraction directory if it doesn't exist
        if not ($extract_dir | path exists) {
            mkdir $extract_dir
        }
        
        # Try to extract the file
        print $"Extracting to: ($extract_dir)"
        let result = run-external "7z" "x" $full_path $"-o($extract_dir)" | complete
        if $result.exit_code == 0 {
            print $"✓ Successfully extracted ($file_name)"
            
            # Delete the original file
            rm $full_path
            print $"✓ Deleted original archive: ($file_name)"
        } else {
            print $"✗ Failed to extract ($file_name)"
            print $"Error: ($result.stderr)"
        }
        
        print "----------------------------------------"
    }
    
    print "Extraction process completed!"
}

