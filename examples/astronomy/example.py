from astropy.io import fits
import os
import argparse
import glob

def compute_median(values):
    """Return the median of a list of numbers."""
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n % 2 == 1:
        return sorted_vals[n//2]
    else:
        return 0.5 * (sorted_vals[n//2 - 1] + sorted_vals[n//2])

def remove_cosmic_rays(image, window_size=5, mad_thresh=5.0):
    """
    Simple cosmic-ray removal:
    - For each pixel, compute the median of its local window.
    - Compute the Median Absolute Deviation (MAD) of that window.
    - If |pixel - median| > mad_thresh * MAD, replace it with the median.
    image: nested list of floats
    returns a new nested list (same dims) with cosmic rays clipped.
    """
    height = len(image)
    width = len(image[0])
    half = window_size // 2
    
    # helper to get window values around (i,j)
    def local_window(i, j):
        vals = []
        for yy in range(max(0, i-half), min(height, i+half+1)):
            for xx in range(max(0, j-half), min(width,  j+half+1)):
                vals.append(image[yy][xx])
        return vals
    
    # build output image
    cleaned = [row[:] for row in image]
    
    for i in range(height):
        for j in range(width):
            window_vals = local_window(i, j)
            med = compute_median(window_vals)
            # compute MAD
            deviations = [abs(v - med) for v in window_vals]
            mad = compute_median(deviations) or 1e-6
            if abs(image[i][j] - med) > mad_thresh * mad:
                cleaned[i][j] = med
    return cleaned

def process_fits_file(in_path, out_path='cleaned_output.fits'):
    """Process a single FITS file and save the cleaned output."""
    with fits.open(in_path) as hdul:
        header = hdul[0].header
        data = hdul[0].data.astype(float)
    
    # Convert numpy array to nested Python lists
    image_lists = data.tolist()
    
    # Run our pure-Python cosmic-ray removal
    cleaned_lists = remove_cosmic_rays(image_lists,
                                      window_size=5,
                                      mad_thresh=5.0)
    
    print(f"Proccessed {in_path}")
    

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Remove cosmic rays from FITS images')
    parser.add_argument('--test', action='store_true', help='Run on only one test file')
    args = parser.parse_args()
    
    # Identify input files
    data_dir = 'data'
    
    if args.test:
        # Use just the first FITS file for testing
        fits_files = glob.glob(os.path.join(data_dir, '*.fits'))
        if fits_files:
            test_file = fits_files[0]  # Take just the first file
            print(f"Test mode: Processing only {test_file}")
            process_fits_file(test_file, f"cleaned_{os.path.basename(test_file)}")
        else:
            print(f"No FITS files found in {data_dir}")
    else:
        # Process all FITS files
        fits_files = glob.glob(os.path.join(data_dir, '*.fits'))
        if fits_files:
            print(f"Processing all {len(fits_files)} FITS files in {data_dir}")
            for fits_file in fits_files:
                output_name = f"cleaned_{os.path.basename(fits_file)}"
                print(f"Processing {fits_file}...")
                process_fits_file(fits_file, output_name)
        else:
            print(f"No FITS files found in {data_dir}")

if __name__ == '__main__':
    main()

